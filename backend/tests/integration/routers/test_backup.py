import io
import json
import pytest
from datetime import datetime
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.recipe import Recipe, RecipeComplexity
from app.models.category import Category
from app.models.tag import Tag
from app.models.user import User
from tests.conftest import create_test_user


def create_recipe(db: Session, user: User, **kwargs) -> Recipe:
    """Helper to create a recipe in the database."""
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


def create_category(db: Session, name: str = "Test Category") -> Category:
    """Helper to create a category."""
    category = Category(name=name, description="Test description")
    db.add(category)
    db.commit()
    db.refresh(category)
    return category


def create_tag(db: Session, name: str = "test-tag") -> Tag:
    """Helper to create a tag."""
    tag = Tag(name=name)
    db.add(tag)
    db.commit()
    db.refresh(tag)
    return tag


def create_valid_backup_json(recipes: list = None) -> dict:
    """Create a valid backup JSON structure."""
    if recipes is None:
        recipes = [
            {
                "title": "Imported Recipe",
                "description": "Imported description",
                "ingredients": [{"name": "Flour", "quantity": "2", "unit": "cups", "notes": None}],
                "instructions": [{"step_number": 1, "text": "Mix ingredients"}],
                "prep_time_minutes": 15,
                "cook_time_minutes": 30,
                "servings": 6,
                "notes": "Some notes",
                "complexity": "medium",
                "special_equipment": ["Mixer"],
                "source_author": "Test Chef",
                "source_url": "https://example.com/recipe",
                "category_name": None,
                "tag_names": [],
                "original_author": "original_user",
                "created_at": datetime.utcnow().isoformat(),
            }
        ]
    return {
        "metadata": {
            "format_version": "1.0",
            "exported_at": datetime.utcnow().isoformat(),
            "recipe_count": len(recipes),
        },
        "recipes": recipes,
    }


class TestExportEndpoint:
    def test_export_returns_json_file(
        self, client: TestClient, admin_auth_headers: dict, db: Session, admin_user: User
    ):
        """Export returns valid JSON file."""
        create_recipe(db, admin_user, title="Test Recipe")

        response = client.get("/api/backup/export", headers=admin_auth_headers)

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"
        assert "attachment" in response.headers["content-disposition"]
        assert "recipes-backup-" in response.headers["content-disposition"]

        data = response.json()
        assert "metadata" in data
        assert "recipes" in data
        assert data["metadata"]["recipe_count"] == 1

    def test_export_requires_admin(self, client: TestClient, auth_headers: dict):
        """Export requires admin access."""
        response = client.get("/api/backup/export", headers=auth_headers)
        assert response.status_code == 403

    def test_export_requires_auth(self, client: TestClient):
        """Export requires authentication."""
        response = client.get("/api/backup/export")
        assert response.status_code == 401

    def test_export_includes_all_recipe_data(
        self, client: TestClient, admin_auth_headers: dict, db: Session, admin_user: User
    ):
        """Export includes complete recipe data."""
        category = create_category(db, "Desserts")
        tag = create_tag(db, "sweet")
        recipe = create_recipe(
            db,
            admin_user,
            title="Full Recipe",
            category_id=category.id,
            complexity=RecipeComplexity.medium,
            special_equipment=["Stand mixer"],
            source_author="Famous Chef",
            source_url="https://example.com/recipe",
        )
        recipe.tags.append(tag)
        db.commit()

        response = client.get("/api/backup/export", headers=admin_auth_headers)
        data = response.json()

        exported = data["recipes"][0]
        assert exported["title"] == "Full Recipe"
        assert exported["category_name"] == "Desserts"
        assert exported["tag_names"] == ["sweet"]
        assert exported["complexity"] == "medium"
        assert exported["special_equipment"] == ["Stand mixer"]


class TestImportEndpoint:
    def test_import_with_valid_file(
        self, client: TestClient, admin_auth_headers: dict, db: Session
    ):
        """Import with valid file succeeds."""
        backup_data = create_valid_backup_json()
        file_content = json.dumps(backup_data).encode()

        response = client.post(
            "/api/backup/import",
            files={"file": ("backup.json", io.BytesIO(file_content), "application/json")},
            headers=admin_auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total_in_file"] == 1
        assert data["created"] == 1
        assert data["errors"] == 0

    def test_import_requires_admin(self, client: TestClient, auth_headers: dict):
        """Import requires admin access."""
        backup_data = create_valid_backup_json()
        file_content = json.dumps(backup_data).encode()

        response = client.post(
            "/api/backup/import",
            files={"file": ("backup.json", io.BytesIO(file_content), "application/json")},
            headers=auth_headers,
        )

        assert response.status_code == 403

    def test_import_requires_auth(self, client: TestClient):
        """Import requires authentication."""
        backup_data = create_valid_backup_json()
        file_content = json.dumps(backup_data).encode()

        response = client.post(
            "/api/backup/import",
            files={"file": ("backup.json", io.BytesIO(file_content), "application/json")},
        )

        assert response.status_code == 401

    def test_import_invalid_json_returns_422(
        self, client: TestClient, admin_auth_headers: dict
    ):
        """Import with invalid JSON returns 422."""
        response = client.post(
            "/api/backup/import",
            files={"file": ("backup.json", io.BytesIO(b"not json"), "application/json")},
            headers=admin_auth_headers,
        )

        assert response.status_code == 422
        assert "Invalid JSON" in response.json()["detail"]

    def test_import_invalid_format_returns_422(
        self, client: TestClient, admin_auth_headers: dict
    ):
        """Import with wrong structure returns 422."""
        invalid_data = {"wrong": "structure"}
        file_content = json.dumps(invalid_data).encode()

        response = client.post(
            "/api/backup/import",
            files={"file": ("backup.json", io.BytesIO(file_content), "application/json")},
            headers=admin_auth_headers,
        )

        assert response.status_code == 422
        assert "Invalid backup format" in response.json()["detail"]

    def test_import_non_json_file_returns_400(
        self, client: TestClient, admin_auth_headers: dict
    ):
        """Import with non-JSON file returns 400."""
        response = client.post(
            "/api/backup/import",
            files={"file": ("backup.txt", io.BytesIO(b"text content"), "text/plain")},
            headers=admin_auth_headers,
        )

        assert response.status_code == 400
        assert "JSON file" in response.json()["detail"]


class TestSelectiveExportEndpoint:
    def test_export_with_recipe_ids(
        self, client: TestClient, admin_auth_headers: dict, db: Session, admin_user: User
    ):
        """Export with specific recipe IDs returns only those recipes."""
        recipe1 = create_recipe(db, admin_user, title="Recipe 1")
        recipe2 = create_recipe(db, admin_user, title="Recipe 2")
        create_recipe(db, admin_user, title="Recipe 3")

        response = client.get(
            f"/api/backup/export?recipe_ids={recipe1.id}&recipe_ids={recipe2.id}",
            headers=admin_auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["metadata"]["recipe_count"] == 2
        titles = {r["title"] for r in data["recipes"]}
        assert titles == {"Recipe 1", "Recipe 2"}

    def test_export_without_recipe_ids_returns_all(
        self, client: TestClient, admin_auth_headers: dict, db: Session, admin_user: User
    ):
        """Export without recipe_ids param returns all recipes."""
        create_recipe(db, admin_user, title="Recipe 1")
        create_recipe(db, admin_user, title="Recipe 2")

        response = client.get("/api/backup/export", headers=admin_auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["metadata"]["recipe_count"] == 2


class TestSelectiveImportEndpoint:
    def test_import_with_selected_titles(
        self, client: TestClient, admin_auth_headers: dict, db: Session
    ):
        """Import with selected_titles imports only those recipes."""
        backup_data = create_valid_backup_json([
            {
                "title": "Recipe A",
                "description": None,
                "ingredients": [],
                "instructions": [],
                "prep_time_minutes": None,
                "cook_time_minutes": None,
                "servings": None,
                "notes": None,
                "complexity": None,
                "special_equipment": None,
                "source_author": None,
                "source_url": None,
                "category_name": None,
                "tag_names": [],
                "original_author": "test",
                "created_at": datetime.utcnow().isoformat(),
            },
            {
                "title": "Recipe B",
                "description": None,
                "ingredients": [],
                "instructions": [],
                "prep_time_minutes": None,
                "cook_time_minutes": None,
                "servings": None,
                "notes": None,
                "complexity": None,
                "special_equipment": None,
                "source_author": None,
                "source_url": None,
                "category_name": None,
                "tag_names": [],
                "original_author": "test",
                "created_at": datetime.utcnow().isoformat(),
            },
            {
                "title": "Recipe C",
                "description": None,
                "ingredients": [],
                "instructions": [],
                "prep_time_minutes": None,
                "cook_time_minutes": None,
                "servings": None,
                "notes": None,
                "complexity": None,
                "special_equipment": None,
                "source_author": None,
                "source_url": None,
                "category_name": None,
                "tag_names": [],
                "original_author": "test",
                "created_at": datetime.utcnow().isoformat(),
            },
        ])
        file_content = json.dumps(backup_data).encode()

        response = client.post(
            "/api/backup/import?selected_titles=Recipe%20A&selected_titles=Recipe%20C",
            files={"file": ("backup.json", io.BytesIO(file_content), "application/json")},
            headers=admin_auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total_in_file"] == 3
        assert data["total_selected"] == 2
        assert data["created"] == 2
        assert db.query(Recipe).filter(Recipe.title == "Recipe B").first() is None

    def test_import_without_selected_titles_imports_all(
        self, client: TestClient, admin_auth_headers: dict, db: Session
    ):
        """Import without selected_titles imports all recipes."""
        backup_data = create_valid_backup_json()
        file_content = json.dumps(backup_data).encode()

        response = client.post(
            "/api/backup/import",
            files={"file": ("backup.json", io.BytesIO(file_content), "application/json")},
            headers=admin_auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total_in_file"] == 1
        assert data["total_selected"] == 1
        assert data["created"] == 1


class TestConflictStrategiesEndToEnd:
    def test_skip_strategy(
        self, client: TestClient, admin_auth_headers: dict, db: Session, admin_user: User
    ):
        """Skip strategy works end-to-end."""
        create_recipe(db, admin_user, title="Existing Recipe")

        backup_data = create_valid_backup_json([
            {
                "title": "Existing Recipe",
                "description": "New description",
                "ingredients": [],
                "instructions": [],
                "prep_time_minutes": None,
                "cook_time_minutes": None,
                "servings": None,
                "notes": None,
                "complexity": None,
                "special_equipment": None,
                "source_author": None,
                "source_url": None,
                "category_name": None,
                "tag_names": [],
                "original_author": "test",
                "created_at": datetime.utcnow().isoformat(),
            }
        ])
        file_content = json.dumps(backup_data).encode()

        response = client.post(
            "/api/backup/import?conflict_strategy=skip",
            files={"file": ("backup.json", io.BytesIO(file_content), "application/json")},
            headers=admin_auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["skipped"] == 1
        assert data["created"] == 0

    def test_replace_strategy(
        self, client: TestClient, admin_auth_headers: dict, db: Session, admin_user: User
    ):
        """Replace strategy works end-to-end."""
        recipe = create_recipe(db, admin_user, title="Existing Recipe", description="Old")

        backup_data = create_valid_backup_json([
            {
                "title": "Existing Recipe",
                "description": "Updated description",
                "ingredients": [],
                "instructions": [],
                "prep_time_minutes": None,
                "cook_time_minutes": None,
                "servings": None,
                "notes": None,
                "complexity": None,
                "special_equipment": None,
                "source_author": None,
                "source_url": None,
                "category_name": None,
                "tag_names": [],
                "original_author": "test",
                "created_at": datetime.utcnow().isoformat(),
            }
        ])
        file_content = json.dumps(backup_data).encode()

        response = client.post(
            "/api/backup/import?conflict_strategy=replace",
            files={"file": ("backup.json", io.BytesIO(file_content), "application/json")},
            headers=admin_auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["replaced"] == 1

        db.refresh(recipe)
        assert recipe.description == "Updated description"

    def test_rename_strategy(
        self, client: TestClient, admin_auth_headers: dict, db: Session, admin_user: User
    ):
        """Rename strategy works end-to-end."""
        create_recipe(db, admin_user, title="Existing Recipe")

        backup_data = create_valid_backup_json([
            {
                "title": "Existing Recipe",
                "description": "New recipe",
                "ingredients": [],
                "instructions": [],
                "prep_time_minutes": None,
                "cook_time_minutes": None,
                "servings": None,
                "notes": None,
                "complexity": None,
                "special_equipment": None,
                "source_author": None,
                "source_url": None,
                "category_name": None,
                "tag_names": [],
                "original_author": "test",
                "created_at": datetime.utcnow().isoformat(),
            }
        ])
        file_content = json.dumps(backup_data).encode()

        response = client.post(
            "/api/backup/import?conflict_strategy=rename",
            files={"file": ("backup.json", io.BytesIO(file_content), "application/json")},
            headers=admin_auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["created"] == 1

        assert db.query(Recipe).filter(Recipe.title == "Existing Recipe (2)").first() is not None


class TestCategoryTagCreation:
    def test_import_creates_categories(
        self, client: TestClient, admin_auth_headers: dict, db: Session
    ):
        """Import creates new categories automatically."""
        backup_data = create_valid_backup_json([
            {
                "title": "Recipe",
                "description": None,
                "ingredients": [],
                "instructions": [],
                "prep_time_minutes": None,
                "cook_time_minutes": None,
                "servings": None,
                "notes": None,
                "complexity": None,
                "special_equipment": None,
                "source_author": None,
                "source_url": None,
                "category_name": "New Category",
                "tag_names": [],
                "original_author": "test",
                "created_at": datetime.utcnow().isoformat(),
            }
        ])
        file_content = json.dumps(backup_data).encode()

        response = client.post(
            "/api/backup/import",
            files={"file": ("backup.json", io.BytesIO(file_content), "application/json")},
            headers=admin_auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["categories_created"] == 1
        assert db.query(Category).filter(Category.name == "New Category").first() is not None

    def test_import_creates_tags(
        self, client: TestClient, admin_auth_headers: dict, db: Session
    ):
        """Import creates new tags automatically."""
        backup_data = create_valid_backup_json([
            {
                "title": "Recipe",
                "description": None,
                "ingredients": [],
                "instructions": [],
                "prep_time_minutes": None,
                "cook_time_minutes": None,
                "servings": None,
                "notes": None,
                "complexity": None,
                "special_equipment": None,
                "source_author": None,
                "source_url": None,
                "category_name": None,
                "tag_names": ["new-tag-1", "new-tag-2"],
                "original_author": "test",
                "created_at": datetime.utcnow().isoformat(),
            }
        ])
        file_content = json.dumps(backup_data).encode()

        response = client.post(
            "/api/backup/import",
            files={"file": ("backup.json", io.BytesIO(file_content), "application/json")},
            headers=admin_auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["tags_created"] == 2
