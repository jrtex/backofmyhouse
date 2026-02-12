import pytest
from datetime import datetime
from uuid import uuid4

from sqlalchemy.orm import Session

from app.models.recipe import Recipe, RecipeComplexity
from app.models.category import Category
from app.models.tag import Tag
from app.models.user import User, UserRole
from app.schemas.backup_schemas import (
    BackupExport,
    BackupMetadata,
    BackupRecipe,
    BackupIngredient,
    BackupInstruction,
    ConflictStrategy,
)
from app.services.backup_service import BackupService
from app.services.auth import AuthService


def create_user(db: Session, username: str = "testuser") -> User:
    user = User(
        id=uuid4(),
        username=username,
        email=f"{username}@example.com",
        hashed_password=AuthService.hash_password("password123"),
        role=UserRole.standard,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def create_category(db: Session, name: str = "Test Category") -> Category:
    category = Category(name=name, description="Test description")
    db.add(category)
    db.commit()
    db.refresh(category)
    return category


def create_tag(db: Session, name: str = "test-tag") -> Tag:
    tag = Tag(name=name)
    db.add(tag)
    db.commit()
    db.refresh(tag)
    return tag


def create_recipe(db: Session, user: User, **kwargs) -> Recipe:
    defaults = {
        "title": "Test Recipe",
        "description": "Test description",
        "ingredients": [{"name": "Salt", "quantity": "1", "unit": "tsp", "notes": None}],
        "instructions": [{"step_number": 1, "text": "Mix well"}],
        "prep_time_minutes": 10,
        "cook_time_minutes": 20,
        "servings": 4,
        "user_id": user.id,
    }
    defaults.update(kwargs)
    recipe = Recipe(**defaults)
    db.add(recipe)
    db.commit()
    db.refresh(recipe)
    return recipe


def create_backup_recipe(
    title: str = "Imported Recipe",
    category_name: str = None,
    tag_names: list = None,
) -> BackupRecipe:
    return BackupRecipe(
        title=title,
        description="Imported description",
        ingredients=[BackupIngredient(name="Flour", quantity="2", unit="cups")],
        instructions=[BackupInstruction(step_number=1, text="Mix ingredients")],
        prep_time_minutes=15,
        cook_time_minutes=30,
        servings=6,
        notes="Some notes",
        complexity="medium",
        special_equipment=["Mixer"],
        source_author="Test Chef",
        source_url="https://example.com/recipe",
        category_name=category_name,
        tag_names=tag_names or [],
        original_author="original_user",
        created_at=datetime.utcnow(),
    )


class TestExportRecipes:
    def test_export_creates_valid_structure(self, db: Session):
        """Export creates valid BackupExport structure."""
        user = create_user(db)
        create_recipe(db, user, title="Recipe 1")
        create_recipe(db, user, title="Recipe 2")

        result = BackupService.export_all_recipes(db)

        assert isinstance(result, BackupExport)
        assert result.metadata.format_version == "1.0"
        assert result.metadata.recipe_count == 2
        assert len(result.recipes) == 2

    def test_export_includes_all_recipe_fields(self, db: Session):
        """Export includes all recipe fields."""
        user = create_user(db)
        category = create_category(db, "Desserts")
        tag = create_tag(db, "sweet")
        recipe = create_recipe(
            db,
            user,
            title="Full Recipe",
            category_id=category.id,
            complexity=RecipeComplexity.hard,
            special_equipment=["Stand mixer"],
            source_author="Famous Chef",
            source_url="https://example.com",
        )
        recipe.tags.append(tag)
        db.commit()

        result = BackupService.export_all_recipes(db)

        assert len(result.recipes) == 1
        exported = result.recipes[0]
        assert exported.title == "Full Recipe"
        assert exported.category_name == "Desserts"
        assert exported.complexity == "hard"
        assert exported.special_equipment == ["Stand mixer"]
        assert exported.source_author == "Famous Chef"
        assert exported.tag_names == ["sweet"]
        assert exported.original_author == user.username

    def test_export_empty_database(self, db: Session):
        """Export with no recipes returns empty list."""
        result = BackupService.export_all_recipes(db)

        assert result.metadata.recipe_count == 0
        assert result.recipes == []


class TestImportRecipesSkipStrategy:
    def test_skip_strategy_skips_duplicates(self, db: Session):
        """Skip strategy skips recipes with existing titles."""
        user = create_user(db)
        create_recipe(db, user, title="Existing Recipe")

        backup = BackupExport(
            metadata=BackupMetadata(exported_at=datetime.utcnow(), recipe_count=1),
            recipes=[create_backup_recipe(title="Existing Recipe")],
        )

        result = BackupService.import_recipes(
            db, backup, user.id, ConflictStrategy.skip
        )

        assert result.skipped == 1
        assert result.created == 0
        assert db.query(Recipe).count() == 1

    def test_skip_strategy_creates_new(self, db: Session):
        """Skip strategy creates recipes that don't exist."""
        user = create_user(db)

        backup = BackupExport(
            metadata=BackupMetadata(exported_at=datetime.utcnow(), recipe_count=1),
            recipes=[create_backup_recipe(title="New Recipe")],
        )

        result = BackupService.import_recipes(
            db, backup, user.id, ConflictStrategy.skip
        )

        assert result.created == 1
        assert result.skipped == 0
        assert db.query(Recipe).filter(Recipe.title == "New Recipe").first() is not None


class TestImportRecipesReplaceStrategy:
    def test_replace_strategy_updates_existing(self, db: Session):
        """Replace strategy updates existing recipes."""
        user = create_user(db)
        existing = create_recipe(db, user, title="Recipe", description="Old")

        backup = BackupExport(
            metadata=BackupMetadata(exported_at=datetime.utcnow(), recipe_count=1),
            recipes=[create_backup_recipe(title="Recipe")],
        )

        result = BackupService.import_recipes(
            db, backup, user.id, ConflictStrategy.replace
        )

        assert result.replaced == 1
        assert result.created == 0
        db.refresh(existing)
        assert existing.description == "Imported description"


class TestImportRecipesRenameStrategy:
    def test_rename_strategy_generates_unique_title(self, db: Session):
        """Rename strategy creates with numbered suffix."""
        user = create_user(db)
        create_recipe(db, user, title="Recipe")

        backup = BackupExport(
            metadata=BackupMetadata(exported_at=datetime.utcnow(), recipe_count=1),
            recipes=[create_backup_recipe(title="Recipe")],
        )

        result = BackupService.import_recipes(
            db, backup, user.id, ConflictStrategy.rename
        )

        assert result.created == 1
        assert db.query(Recipe).filter(Recipe.title == "Recipe (2)").first() is not None

    def test_rename_strategy_increments_number(self, db: Session):
        """Rename strategy increments number if (2) exists."""
        user = create_user(db)
        create_recipe(db, user, title="Recipe")
        create_recipe(db, user, title="Recipe (2)")

        backup = BackupExport(
            metadata=BackupMetadata(exported_at=datetime.utcnow(), recipe_count=1),
            recipes=[create_backup_recipe(title="Recipe")],
        )

        result = BackupService.import_recipes(
            db, backup, user.id, ConflictStrategy.rename
        )

        assert result.created == 1
        assert db.query(Recipe).filter(Recipe.title == "Recipe (3)").first() is not None


class TestCategoryTagAutoCreation:
    def test_creates_category_if_not_exists(self, db: Session):
        """Creates new category if it doesn't exist."""
        user = create_user(db)

        backup = BackupExport(
            metadata=BackupMetadata(exported_at=datetime.utcnow(), recipe_count=1),
            recipes=[create_backup_recipe(title="New", category_name="New Category")],
        )

        result = BackupService.import_recipes(
            db, backup, user.id, ConflictStrategy.skip
        )

        assert result.categories_created == 1
        assert db.query(Category).filter(Category.name == "New Category").first() is not None

    def test_uses_existing_category(self, db: Session):
        """Uses existing category if it exists."""
        user = create_user(db)
        create_category(db, "Existing Category")

        backup = BackupExport(
            metadata=BackupMetadata(exported_at=datetime.utcnow(), recipe_count=1),
            recipes=[create_backup_recipe(title="New", category_name="Existing Category")],
        )

        result = BackupService.import_recipes(
            db, backup, user.id, ConflictStrategy.skip
        )

        assert result.categories_created == 0
        recipe = db.query(Recipe).filter(Recipe.title == "New").first()
        assert recipe.category.name == "Existing Category"

    def test_creates_tags_if_not_exists(self, db: Session):
        """Creates new tags if they don't exist."""
        user = create_user(db)

        backup = BackupExport(
            metadata=BackupMetadata(exported_at=datetime.utcnow(), recipe_count=1),
            recipes=[create_backup_recipe(title="New", tag_names=["new-tag", "another-tag"])],
        )

        result = BackupService.import_recipes(
            db, backup, user.id, ConflictStrategy.skip
        )

        assert result.tags_created == 2
        recipe = db.query(Recipe).filter(Recipe.title == "New").first()
        assert len(recipe.tags) == 2

    def test_uses_existing_tags(self, db: Session):
        """Uses existing tags if they exist."""
        user = create_user(db)
        create_tag(db, "existing-tag")

        backup = BackupExport(
            metadata=BackupMetadata(exported_at=datetime.utcnow(), recipe_count=1),
            recipes=[create_backup_recipe(title="New", tag_names=["existing-tag", "new-tag"])],
        )

        result = BackupService.import_recipes(
            db, backup, user.id, ConflictStrategy.skip
        )

        assert result.tags_created == 1
        recipe = db.query(Recipe).filter(Recipe.title == "New").first()
        assert len(recipe.tags) == 2


class TestErrorHandling:
    def test_invalid_complexity_records_error(self, db: Session):
        """Invalid data records error without stopping import."""
        user = create_user(db)

        bad_recipe = BackupRecipe(
            title="Bad Recipe",
            description=None,
            ingredients=[],
            instructions=[],
            prep_time_minutes=None,
            cook_time_minutes=None,
            servings=None,
            notes=None,
            complexity="invalid_complexity",
            special_equipment=None,
            source_author=None,
            source_url=None,
            category_name=None,
            tag_names=[],
            original_author="test",
            created_at=datetime.utcnow(),
        )

        backup = BackupExport(
            metadata=BackupMetadata(exported_at=datetime.utcnow(), recipe_count=1),
            recipes=[bad_recipe],
        )

        result = BackupService.import_recipes(
            db, backup, user.id, ConflictStrategy.skip
        )

        assert result.errors == 1
        assert len(result.error_details) == 1
        assert result.error_details[0]["title"] == "Bad Recipe"
