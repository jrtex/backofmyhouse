import pytest
from uuid import uuid4
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.category import Category


def create_category(db: Session, name: str = "Test Category", description: str = None) -> Category:
    """Helper to create a category."""
    category = Category(name=name, description=description)
    db.add(category)
    db.commit()
    db.refresh(category)
    return category


class TestListCategories:
    def test_list_categories_empty(self, client: TestClient, auth_headers: dict):
        """List categories returns empty list when none exist."""
        response = client.get("/api/categories", headers=auth_headers)
        assert response.status_code == 200
        assert response.json() == []

    def test_list_categories(
        self, client: TestClient, auth_headers: dict, db: Session
    ):
        """List categories returns all categories sorted by name."""
        create_category(db, "Desserts")
        create_category(db, "Appetizers")
        create_category(db, "Main Course")

        response = client.get("/api/categories", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        # Should be sorted alphabetically
        assert data[0]["name"] == "Appetizers"
        assert data[1]["name"] == "Desserts"
        assert data[2]["name"] == "Main Course"

    def test_list_categories_requires_auth(self, client: TestClient):
        """List categories requires authentication."""
        response = client.get("/api/categories")
        assert response.status_code == 401


class TestGetCategory:
    def test_get_category(
        self, client: TestClient, auth_headers: dict, db: Session
    ):
        """Get single category by ID."""
        category = create_category(db, "Test", "Test description")

        response = client.get(f"/api/categories/{category.id}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Test"
        assert data["description"] == "Test description"

    def test_get_category_not_found(self, client: TestClient, auth_headers: dict):
        """Get non-existent category returns 404."""
        response = client.get(f"/api/categories/{uuid4()}", headers=auth_headers)
        assert response.status_code == 404


class TestCreateCategory:
    def test_create_category_as_admin(
        self, client: TestClient, admin_auth_headers: dict
    ):
        """Admin can create category."""
        response = client.post(
            "/api/categories",
            json={"name": "New Category", "description": "Description"},
            headers=admin_auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "New Category"
        assert data["description"] == "Description"

    def test_create_category_minimal(
        self, client: TestClient, admin_auth_headers: dict
    ):
        """Can create category without description."""
        response = client.post(
            "/api/categories",
            json={"name": "Minimal Category"},
            headers=admin_auth_headers,
        )
        assert response.status_code == 201
        assert response.json()["description"] is None

    def test_create_category_as_standard_user(
        self, client: TestClient, auth_headers: dict
    ):
        """Standard user cannot create category."""
        response = client.post(
            "/api/categories",
            json={"name": "New Category"},
            headers=auth_headers,
        )
        assert response.status_code == 403

    def test_create_duplicate_category(
        self, client: TestClient, admin_auth_headers: dict, db: Session
    ):
        """Cannot create category with duplicate name."""
        create_category(db, "Existing")

        response = client.post(
            "/api/categories",
            json={"name": "Existing"},
            headers=admin_auth_headers,
        )
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"]

    def test_create_category_empty_name(
        self, client: TestClient, admin_auth_headers: dict
    ):
        """Cannot create category with empty name."""
        response = client.post(
            "/api/categories",
            json={"name": ""},
            headers=admin_auth_headers,
        )
        assert response.status_code == 422


class TestUpdateCategory:
    def test_update_category_as_admin(
        self, client: TestClient, admin_auth_headers: dict, db: Session
    ):
        """Admin can update category."""
        category = create_category(db, "Original")

        response = client.put(
            f"/api/categories/{category.id}",
            json={"name": "Updated"},
            headers=admin_auth_headers,
        )
        assert response.status_code == 200
        assert response.json()["name"] == "Updated"

    def test_update_category_description_only(
        self, client: TestClient, admin_auth_headers: dict, db: Session
    ):
        """Can update only description."""
        category = create_category(db, "Test")

        response = client.put(
            f"/api/categories/{category.id}",
            json={"description": "New description"},
            headers=admin_auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Test"
        assert data["description"] == "New description"

    def test_update_category_as_standard_user(
        self, client: TestClient, auth_headers: dict, db: Session
    ):
        """Standard user cannot update category."""
        category = create_category(db, "Test")

        response = client.put(
            f"/api/categories/{category.id}",
            json={"name": "Hacked"},
            headers=auth_headers,
        )
        assert response.status_code == 403

    def test_update_category_duplicate_name(
        self, client: TestClient, admin_auth_headers: dict, db: Session
    ):
        """Cannot update category to duplicate name."""
        create_category(db, "Existing")
        category = create_category(db, "Original")

        response = client.put(
            f"/api/categories/{category.id}",
            json={"name": "Existing"},
            headers=admin_auth_headers,
        )
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"]

    def test_update_category_not_found(
        self, client: TestClient, admin_auth_headers: dict
    ):
        """Update non-existent category returns 404."""
        response = client.put(
            f"/api/categories/{uuid4()}",
            json={"name": "New Name"},
            headers=admin_auth_headers,
        )
        assert response.status_code == 404


class TestDeleteCategory:
    def test_delete_category_as_admin(
        self, client: TestClient, admin_auth_headers: dict, db: Session
    ):
        """Admin can delete category."""
        category = create_category(db, "To Delete")

        response = client.delete(
            f"/api/categories/{category.id}", headers=admin_auth_headers
        )
        assert response.status_code == 204

        # Verify deleted
        response = client.get(
            f"/api/categories/{category.id}", headers=admin_auth_headers
        )
        assert response.status_code == 404

    def test_delete_category_as_standard_user(
        self, client: TestClient, auth_headers: dict, db: Session
    ):
        """Standard user cannot delete category."""
        category = create_category(db, "Test")

        response = client.delete(
            f"/api/categories/{category.id}", headers=auth_headers
        )
        assert response.status_code == 403

    def test_delete_category_not_found(
        self, client: TestClient, admin_auth_headers: dict
    ):
        """Delete non-existent category returns 404."""
        response = client.delete(
            f"/api/categories/{uuid4()}", headers=admin_auth_headers
        )
        assert response.status_code == 404
