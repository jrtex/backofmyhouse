from datetime import datetime
from typing import List
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.recipe import Recipe
from app.models.category import Category
from app.models.tag import Tag
from app.schemas.backup_schemas import (
    BackupExport,
    BackupMetadata,
    BackupRecipe,
    BackupIngredient,
    BackupInstruction,
    ConflictStrategy,
    ImportResult,
)


class BackupService:
    @staticmethod
    def export_all_recipes(db: Session) -> BackupExport:
        """Export all recipes with relationships to BackupExport format."""
        recipes = db.query(Recipe).all()

        backup_recipes = []
        for recipe in recipes:
            backup_recipe = BackupRecipe(
                title=recipe.title,
                description=recipe.description,
                ingredients=[
                    BackupIngredient(**ing) for ing in recipe.ingredients
                ],
                instructions=[
                    BackupInstruction(**inst) for inst in recipe.instructions
                ],
                prep_time_minutes=recipe.prep_time_minutes,
                cook_time_minutes=recipe.cook_time_minutes,
                servings=recipe.servings,
                notes=recipe.notes,
                complexity=recipe.complexity.value if recipe.complexity else None,
                special_equipment=recipe.special_equipment,
                source_author=recipe.source_author,
                source_url=recipe.source_url,
                category_name=recipe.category.name if recipe.category else None,
                tag_names=[tag.name for tag in recipe.tags],
                original_author=recipe.user.username,
                created_at=recipe.created_at,
            )
            backup_recipes.append(backup_recipe)

        metadata = BackupMetadata(
            exported_at=datetime.utcnow(),
            recipe_count=len(backup_recipes),
        )

        return BackupExport(metadata=metadata, recipes=backup_recipes)

    @staticmethod
    def import_recipes(
        db: Session,
        backup_data: BackupExport,
        importing_user_id: UUID,
        conflict_strategy: ConflictStrategy,
    ) -> ImportResult:
        """Import recipes from backup with conflict resolution."""
        result = ImportResult(
            total_in_file=len(backup_data.recipes),
            created=0,
            skipped=0,
            replaced=0,
            errors=0,
            categories_created=0,
            tags_created=0,
            error_details=[],
        )

        for backup_recipe in backup_data.recipes:
            try:
                existing = (
                    db.query(Recipe)
                    .filter(Recipe.title == backup_recipe.title)
                    .first()
                )

                if existing:
                    if conflict_strategy == ConflictStrategy.skip:
                        result.skipped += 1
                        continue
                    elif conflict_strategy == ConflictStrategy.replace:
                        BackupService._update_recipe_from_backup(
                            db, existing, backup_recipe, importing_user_id, result
                        )
                        result.replaced += 1
                        continue
                    elif conflict_strategy == ConflictStrategy.rename:
                        new_title = BackupService._generate_unique_title(
                            db, backup_recipe.title
                        )
                        backup_recipe_copy = backup_recipe.model_copy()
                        backup_recipe_copy.title = new_title
                        BackupService._create_recipe_from_backup(
                            db, backup_recipe_copy, importing_user_id, result
                        )
                        result.created += 1
                        continue

                BackupService._create_recipe_from_backup(
                    db, backup_recipe, importing_user_id, result
                )
                result.created += 1

            except Exception as e:
                result.errors += 1
                result.error_details.append({
                    "title": backup_recipe.title,
                    "error": str(e),
                })

        db.commit()
        return result

    @staticmethod
    def _create_recipe_from_backup(
        db: Session,
        backup_recipe: BackupRecipe,
        user_id: UUID,
        result: ImportResult,
    ) -> Recipe:
        """Create a new recipe from backup data."""
        category_id = None
        if backup_recipe.category_name:
            category_id, created = BackupService._get_or_create_category(
                db, backup_recipe.category_name
            )
            if created:
                result.categories_created += 1

        tag_ids, tags_created = BackupService._get_or_create_tags(
            db, backup_recipe.tag_names
        )
        result.tags_created += tags_created

        from app.models.recipe import RecipeComplexity

        complexity = None
        if backup_recipe.complexity:
            complexity = RecipeComplexity(backup_recipe.complexity)

        recipe = Recipe(
            title=backup_recipe.title,
            description=backup_recipe.description,
            ingredients=[ing.model_dump() for ing in backup_recipe.ingredients],
            instructions=[inst.model_dump() for inst in backup_recipe.instructions],
            prep_time_minutes=backup_recipe.prep_time_minutes,
            cook_time_minutes=backup_recipe.cook_time_minutes,
            servings=backup_recipe.servings,
            notes=backup_recipe.notes,
            complexity=complexity,
            special_equipment=backup_recipe.special_equipment,
            source_author=backup_recipe.source_author,
            source_url=backup_recipe.source_url,
            category_id=category_id,
            user_id=user_id,
        )
        db.add(recipe)
        db.flush()

        if tag_ids:
            tags = db.query(Tag).filter(Tag.id.in_(tag_ids)).all()
            recipe.tags = tags

        return recipe

    @staticmethod
    def _update_recipe_from_backup(
        db: Session,
        recipe: Recipe,
        backup_recipe: BackupRecipe,
        user_id: UUID,
        result: ImportResult,
    ) -> None:
        """Update an existing recipe with backup data."""
        category_id = None
        if backup_recipe.category_name:
            category_id, created = BackupService._get_or_create_category(
                db, backup_recipe.category_name
            )
            if created:
                result.categories_created += 1

        tag_ids, tags_created = BackupService._get_or_create_tags(
            db, backup_recipe.tag_names
        )
        result.tags_created += tags_created

        from app.models.recipe import RecipeComplexity

        complexity = None
        if backup_recipe.complexity:
            complexity = RecipeComplexity(backup_recipe.complexity)

        recipe.description = backup_recipe.description
        recipe.ingredients = [ing.model_dump() for ing in backup_recipe.ingredients]
        recipe.instructions = [inst.model_dump() for inst in backup_recipe.instructions]
        recipe.prep_time_minutes = backup_recipe.prep_time_minutes
        recipe.cook_time_minutes = backup_recipe.cook_time_minutes
        recipe.servings = backup_recipe.servings
        recipe.notes = backup_recipe.notes
        recipe.complexity = complexity
        recipe.special_equipment = backup_recipe.special_equipment
        recipe.source_author = backup_recipe.source_author
        recipe.source_url = backup_recipe.source_url
        recipe.category_id = category_id
        recipe.user_id = user_id

        if tag_ids:
            tags = db.query(Tag).filter(Tag.id.in_(tag_ids)).all()
            recipe.tags = tags
        else:
            recipe.tags = []

        db.flush()

    @staticmethod
    def _get_or_create_category(db: Session, name: str) -> tuple[UUID, bool]:
        """Find existing category or create new one. Returns (id, was_created)."""
        category = db.query(Category).filter(Category.name == name).first()
        if category:
            return category.id, False

        category = Category(name=name)
        db.add(category)
        db.flush()
        return category.id, True

    @staticmethod
    def _get_or_create_tags(db: Session, names: List[str]) -> tuple[List[UUID], int]:
        """Find existing tags or create new ones. Returns (ids, count_created)."""
        if not names:
            return [], 0

        tag_ids = []
        created_count = 0

        for name in names:
            tag = db.query(Tag).filter(Tag.name == name).first()
            if tag:
                tag_ids.append(tag.id)
            else:
                tag = Tag(name=name)
                db.add(tag)
                db.flush()
                tag_ids.append(tag.id)
                created_count += 1

        return tag_ids, created_count

    @staticmethod
    def _generate_unique_title(db: Session, base_title: str) -> str:
        """Generate 'Title (2)', 'Title (3)' etc. for rename strategy."""
        counter = 2
        while True:
            new_title = f"{base_title} ({counter})"
            existing = (
                db.query(Recipe)
                .filter(Recipe.title == new_title)
                .first()
            )
            if not existing:
                return new_title
            counter += 1
