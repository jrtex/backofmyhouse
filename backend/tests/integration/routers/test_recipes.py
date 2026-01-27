import pytest
from uuid import uuid4
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.user import User, UserRole
from app.models.recipe import Recipe, RecipeComplexity
from app.models.category import Category
from app.models.tag import Tag
from tests.conftest import create_test_user


def create_recipe(db: Session, user: User, **kwargs) -> Recipe:
    """Helper to create a recipe in the database."""
    defaults = {
        "title": "Test Recipe",
        "description": "Test description",
        "ingredients": [{"name": "Salt", "quantity": "1", "unit": "tsp"}],
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


class TestListRecipes:
    def test_list_recipes_empty(self, client: TestClient, auth_headers: dict):
        """List recipes returns empty list when no recipes exist."""
        response = client.get("/api/recipes", headers=auth_headers)
        assert response.status_code == 200
        assert response.json() == []

    def test_list_recipes(
        self, client: TestClient, auth_headers: dict, db: Session, test_user: User
    ):
        """List recipes returns all recipes."""
        create_recipe(db, test_user, title="Recipe 1")
        create_recipe(db, test_user, title="Recipe 2")

        response = client.get("/api/recipes", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    def test_list_recipes_filter_by_category(
        self, client: TestClient, auth_headers: dict, db: Session, test_user: User
    ):
        """Can filter recipes by category."""
        category = create_category(db, "Desserts")
        create_recipe(db, test_user, title="With Category", category_id=category.id)
        create_recipe(db, test_user, title="Without Category")

        response = client.get(
            f"/api/recipes?category_id={category.id}", headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["title"] == "With Category"

    def test_list_recipes_search(
        self, client: TestClient, auth_headers: dict, db: Session, test_user: User
    ):
        """Can search recipes by title."""
        create_recipe(db, test_user, title="Chocolate Cake")
        create_recipe(db, test_user, title="Vanilla Ice Cream")

        response = client.get("/api/recipes?search=chocolate", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["title"] == "Chocolate Cake"

    def test_list_recipes_pagination(
        self, client: TestClient, auth_headers: dict, db: Session, test_user: User
    ):
        """Can paginate recipes."""
        for i in range(5):
            create_recipe(db, test_user, title=f"Recipe {i}")

        response = client.get("/api/recipes?skip=2&limit=2", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    def test_list_recipes_requires_auth(self, client: TestClient):
        """List recipes requires authentication."""
        response = client.get("/api/recipes")
        assert response.status_code == 401


class TestGetRecipe:
    def test_get_recipe(
        self, client: TestClient, auth_headers: dict, db: Session, test_user: User
    ):
        """Get single recipe by ID."""
        recipe = create_recipe(db, test_user)

        response = client.get(f"/api/recipes/{recipe.id}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == recipe.title
        assert data["id"] == str(recipe.id)

    def test_get_recipe_not_found(self, client: TestClient, auth_headers: dict):
        """Get non-existent recipe returns 404."""
        response = client.get(f"/api/recipes/{uuid4()}", headers=auth_headers)
        assert response.status_code == 404

    def test_get_recipe_requires_auth(self, client: TestClient, db: Session, test_user: User):
        """Get recipe requires authentication."""
        recipe = create_recipe(db, test_user)
        response = client.get(f"/api/recipes/{recipe.id}")
        assert response.status_code == 401

    def test_get_recipe_with_metadata_fields(
        self, client: TestClient, auth_headers: dict, db: Session, test_user: User
    ):
        """Get recipe returns all metadata fields."""
        recipe = create_recipe(
            db,
            test_user,
            complexity=RecipeComplexity.medium,
            special_equipment=["Blender", "Food processor"],
            source_author="Test Chef",
            source_url="https://example.com/test-recipe",
        )

        response = client.get(f"/api/recipes/{recipe.id}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["complexity"] == "medium"
        assert data["special_equipment"] == ["Blender", "Food processor"]
        assert data["source_author"] == "Test Chef"
        assert data["source_url"] == "https://example.com/test-recipe"


class TestCreateRecipe:
    def test_create_recipe_minimal(self, client: TestClient, auth_headers: dict):
        """Create recipe with minimal data."""
        response = client.post(
            "/api/recipes",
            json={"title": "New Recipe", "ingredients": [], "instructions": [], "tag_ids": []},
            headers=auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "New Recipe"

    def test_create_recipe_full(
        self, client: TestClient, auth_headers: dict, db: Session
    ):
        """Create recipe with all fields."""
        category = create_category(db)
        tag = create_tag(db)

        response = client.post(
            "/api/recipes",
            json={
                "title": "Full Recipe",
                "description": "A complete recipe",
                "ingredients": [{"name": "Salt", "quantity": "1", "unit": "tsp"}],
                "instructions": [{"step_number": 1, "text": "Mix"}],
                "prep_time_minutes": 10,
                "cook_time_minutes": 20,
                "servings": 4,
                "notes": "Some notes",
                "category_id": str(category.id),
                "tag_ids": [str(tag.id)],
            },
            headers=auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Full Recipe"
        assert data["category"]["id"] == str(category.id)
        assert len(data["tags"]) == 1

    def test_create_recipe_invalid_category(self, client: TestClient, auth_headers: dict):
        """Cannot create recipe with non-existent category."""
        response = client.post(
            "/api/recipes",
            json={
                "title": "Test",
                "category_id": str(uuid4()),
                "tag_ids": [],
            },
            headers=auth_headers,
        )
        assert response.status_code == 400
        assert "Category not found" in response.json()["detail"]

    def test_create_recipe_invalid_tags(
        self, client: TestClient, auth_headers: dict, db: Session
    ):
        """Cannot create recipe with non-existent tags."""
        response = client.post(
            "/api/recipes",
            json={
                "title": "Test",
                "tag_ids": [str(uuid4())],
            },
            headers=auth_headers,
        )
        assert response.status_code == 400
        assert "tags not found" in response.json()["detail"]

    def test_create_recipe_with_metadata_fields(
        self, client: TestClient, auth_headers: dict
    ):
        """Create recipe with all new metadata fields."""
        response = client.post(
            "/api/recipes",
            json={
                "title": "Recipe With Metadata",
                "ingredients": [],
                "instructions": [],
                "tag_ids": [],
                "complexity": "medium",
                "special_equipment": ["Stand mixer", "Thermometer"],
                "source_author": "Julia Child",
                "source_url": "https://example.com/recipe",
            },
            headers=auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["complexity"] == "medium"
        assert data["special_equipment"] == ["Stand mixer", "Thermometer"]
        assert data["source_author"] == "Julia Child"
        assert data["source_url"] == "https://example.com/recipe"

    def test_create_recipe_complexity_values(
        self, client: TestClient, auth_headers: dict
    ):
        """Test all complexity enum values are accepted."""
        for complexity in ["very_easy", "easy", "medium", "hard", "very_hard"]:
            response = client.post(
                "/api/recipes",
                json={
                    "title": f"Recipe {complexity}",
                    "ingredients": [],
                    "instructions": [],
                    "tag_ids": [],
                    "complexity": complexity,
                },
                headers=auth_headers,
            )
            assert response.status_code == 201
            assert response.json()["complexity"] == complexity

    def test_create_recipe_invalid_complexity(
        self, client: TestClient, auth_headers: dict
    ):
        """Invalid complexity value is rejected."""
        response = client.post(
            "/api/recipes",
            json={
                "title": "Test",
                "ingredients": [],
                "instructions": [],
                "tag_ids": [],
                "complexity": "super_easy",
            },
            headers=auth_headers,
        )
        assert response.status_code == 422

    def test_create_recipe_metadata_fields_optional(
        self, client: TestClient, auth_headers: dict
    ):
        """Metadata fields are optional and default to None."""
        response = client.post(
            "/api/recipes",
            json={
                "title": "Minimal Recipe",
                "ingredients": [],
                "instructions": [],
                "tag_ids": [],
            },
            headers=auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["complexity"] is None
        assert data["special_equipment"] is None
        assert data["source_author"] is None
        assert data["source_url"] is None


class TestUpdateRecipe:
    def test_update_own_recipe(
        self, client: TestClient, auth_headers: dict, db: Session, test_user: User
    ):
        """Can update own recipe."""
        recipe = create_recipe(db, test_user)

        response = client.put(
            f"/api/recipes/{recipe.id}",
            json={"title": "Updated Title"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert response.json()["title"] == "Updated Title"

    def test_update_other_user_recipe_forbidden(
        self, client: TestClient, auth_headers: dict, db: Session
    ):
        """Cannot update another user's recipe."""
        other_user = create_test_user(db, "other", "other@example.com")
        recipe = create_recipe(db, other_user)

        response = client.put(
            f"/api/recipes/{recipe.id}",
            json={"title": "Hacked Title"},
            headers=auth_headers,
        )
        assert response.status_code == 403

    def test_admin_can_update_any_recipe(
        self, client: TestClient, admin_auth_headers: dict, db: Session, test_user: User
    ):
        """Admin can update any recipe."""
        recipe = create_recipe(db, test_user)

        response = client.put(
            f"/api/recipes/{recipe.id}",
            json={"title": "Admin Updated"},
            headers=admin_auth_headers,
        )
        assert response.status_code == 200
        assert response.json()["title"] == "Admin Updated"

    def test_update_recipe_not_found(self, client: TestClient, auth_headers: dict):
        """Update non-existent recipe returns 404."""
        response = client.put(
            f"/api/recipes/{uuid4()}",
            json={"title": "New Title"},
            headers=auth_headers,
        )
        assert response.status_code == 404

    def test_update_recipe_metadata_fields(
        self, client: TestClient, auth_headers: dict, db: Session, test_user: User
    ):
        """Can update recipe metadata fields."""
        recipe = create_recipe(db, test_user)

        response = client.put(
            f"/api/recipes/{recipe.id}",
            json={
                "complexity": "hard",
                "special_equipment": ["Dutch oven"],
                "source_author": "Updated Author",
                "source_url": "https://updated.com/recipe",
            },
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["complexity"] == "hard"
        assert data["special_equipment"] == ["Dutch oven"]
        assert data["source_author"] == "Updated Author"
        assert data["source_url"] == "https://updated.com/recipe"

    def test_update_recipe_clear_special_equipment(
        self, client: TestClient, auth_headers: dict, db: Session, test_user: User
    ):
        """Can clear special_equipment by setting to empty list."""
        recipe = create_recipe(
            db, test_user, special_equipment=["Stand mixer", "Food processor"]
        )

        response = client.put(
            f"/api/recipes/{recipe.id}",
            json={"special_equipment": []},
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert response.json()["special_equipment"] == []

    def test_update_recipe_partial_metadata(
        self, client: TestClient, auth_headers: dict, db: Session, test_user: User
    ):
        """Can update only some metadata fields without affecting others."""
        recipe = create_recipe(
            db,
            test_user,
            complexity=RecipeComplexity.easy,
            source_author="Original Author",
        )

        response = client.put(
            f"/api/recipes/{recipe.id}",
            json={"complexity": "very_hard"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["complexity"] == "very_hard"
        assert data["source_author"] == "Original Author"


class TestDeleteRecipe:
    def test_delete_own_recipe(
        self, client: TestClient, auth_headers: dict, db: Session, test_user: User
    ):
        """Can delete own recipe."""
        recipe = create_recipe(db, test_user)

        response = client.delete(f"/api/recipes/{recipe.id}", headers=auth_headers)
        assert response.status_code == 204

        # Verify deleted
        response = client.get(f"/api/recipes/{recipe.id}", headers=auth_headers)
        assert response.status_code == 404

    def test_delete_other_user_recipe_forbidden(
        self, client: TestClient, auth_headers: dict, db: Session
    ):
        """Cannot delete another user's recipe."""
        other_user = create_test_user(db, "other", "other@example.com")
        recipe = create_recipe(db, other_user)

        response = client.delete(f"/api/recipes/{recipe.id}", headers=auth_headers)
        assert response.status_code == 403

    def test_admin_can_delete_any_recipe(
        self, client: TestClient, admin_auth_headers: dict, db: Session, test_user: User
    ):
        """Admin can delete any recipe."""
        recipe = create_recipe(db, test_user)

        response = client.delete(
            f"/api/recipes/{recipe.id}", headers=admin_auth_headers
        )
        assert response.status_code == 204

    def test_delete_recipe_not_found(self, client: TestClient, auth_headers: dict):
        """Delete non-existent recipe returns 404."""
        response = client.delete(f"/api/recipes/{uuid4()}", headers=auth_headers)
        assert response.status_code == 404
