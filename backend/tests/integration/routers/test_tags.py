import pytest
from uuid import uuid4
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.tag import Tag


def create_tag(db: Session, name: str = "test-tag") -> Tag:
    """Helper to create a tag."""
    tag = Tag(name=name)
    db.add(tag)
    db.commit()
    db.refresh(tag)
    return tag


class TestListTags:
    def test_list_tags_empty(self, client: TestClient, auth_headers: dict):
        """List tags returns empty list when none exist."""
        response = client.get("/api/tags", headers=auth_headers)
        assert response.status_code == 200
        assert response.json() == []

    def test_list_tags(self, client: TestClient, auth_headers: dict, db: Session):
        """List tags returns all tags sorted by name."""
        create_tag(db, "vegetarian")
        create_tag(db, "gluten-free")
        create_tag(db, "quick")

        response = client.get("/api/tags", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        # Should be sorted alphabetically
        assert data[0]["name"] == "gluten-free"
        assert data[1]["name"] == "quick"
        assert data[2]["name"] == "vegetarian"

    def test_list_tags_requires_auth(self, client: TestClient):
        """List tags requires authentication."""
        response = client.get("/api/tags")
        assert response.status_code == 401


class TestGetTag:
    def test_get_tag(self, client: TestClient, auth_headers: dict, db: Session):
        """Get single tag by ID."""
        tag = create_tag(db, "test-tag")

        response = client.get(f"/api/tags/{tag.id}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "test-tag"

    def test_get_tag_not_found(self, client: TestClient, auth_headers: dict):
        """Get non-existent tag returns 404."""
        response = client.get(f"/api/tags/{uuid4()}", headers=auth_headers)
        assert response.status_code == 404


class TestCreateTag:
    def test_create_tag_as_admin(self, client: TestClient, admin_auth_headers: dict):
        """Admin can create tag."""
        response = client.post(
            "/api/tags",
            json={"name": "new-tag"},
            headers=admin_auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "new-tag"

    def test_create_tag_as_standard_user(
        self, client: TestClient, auth_headers: dict
    ):
        """Standard user cannot create tag."""
        response = client.post(
            "/api/tags",
            json={"name": "new-tag"},
            headers=auth_headers,
        )
        assert response.status_code == 403

    def test_create_duplicate_tag(
        self, client: TestClient, admin_auth_headers: dict, db: Session
    ):
        """Cannot create tag with duplicate name."""
        create_tag(db, "existing")

        response = client.post(
            "/api/tags",
            json={"name": "existing"},
            headers=admin_auth_headers,
        )
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"]

    def test_create_tag_empty_name(
        self, client: TestClient, admin_auth_headers: dict
    ):
        """Cannot create tag with empty name."""
        response = client.post(
            "/api/tags",
            json={"name": ""},
            headers=admin_auth_headers,
        )
        assert response.status_code == 422

    def test_create_tag_too_long(
        self, client: TestClient, admin_auth_headers: dict
    ):
        """Cannot create tag with name over 50 characters."""
        response = client.post(
            "/api/tags",
            json={"name": "a" * 51},
            headers=admin_auth_headers,
        )
        assert response.status_code == 422


class TestDeleteTag:
    def test_delete_tag_as_admin(
        self, client: TestClient, admin_auth_headers: dict, db: Session
    ):
        """Admin can delete tag."""
        tag = create_tag(db, "to-delete")

        response = client.delete(f"/api/tags/{tag.id}", headers=admin_auth_headers)
        assert response.status_code == 204

        # Verify deleted
        response = client.get(f"/api/tags/{tag.id}", headers=admin_auth_headers)
        assert response.status_code == 404

    def test_delete_tag_as_standard_user(
        self, client: TestClient, auth_headers: dict, db: Session
    ):
        """Standard user cannot delete tag."""
        tag = create_tag(db, "test")

        response = client.delete(f"/api/tags/{tag.id}", headers=auth_headers)
        assert response.status_code == 403

    def test_delete_tag_not_found(
        self, client: TestClient, admin_auth_headers: dict
    ):
        """Delete non-existent tag returns 404."""
        response = client.delete(f"/api/tags/{uuid4()}", headers=admin_auth_headers)
        assert response.status_code == 404
