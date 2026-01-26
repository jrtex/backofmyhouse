import pytest
from uuid import uuid4
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.user import User, UserRole
from tests.conftest import create_test_user


class TestListUsers:
    def test_list_users_as_admin(
        self, client: TestClient, admin_auth_headers: dict, db: Session, admin_user: User
    ):
        """Admin can list all users."""
        # Create some additional users
        create_test_user(db, "user1", "user1@example.com")
        create_test_user(db, "user2", "user2@example.com")

        response = client.get("/api/users", headers=admin_auth_headers)
        assert response.status_code == 200
        data = response.json()
        # admin_user + 2 created users
        assert len(data) == 3

    def test_list_users_as_standard_user(
        self, client: TestClient, auth_headers: dict
    ):
        """Standard user cannot list users."""
        response = client.get("/api/users", headers=auth_headers)
        assert response.status_code == 403

    def test_list_users_requires_auth(self, client: TestClient):
        """List users requires authentication."""
        response = client.get("/api/users")
        assert response.status_code == 401


class TestGetUser:
    def test_get_user_as_admin(
        self, client: TestClient, admin_auth_headers: dict, db: Session
    ):
        """Admin can get any user."""
        user = create_test_user(db, "testuser", "test@example.com")

        response = client.get(f"/api/users/{user.id}", headers=admin_auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "testuser"

    def test_get_user_as_standard_user(
        self, client: TestClient, auth_headers: dict, test_user: User
    ):
        """Standard user cannot get user details."""
        response = client.get(f"/api/users/{test_user.id}", headers=auth_headers)
        assert response.status_code == 403

    def test_get_user_not_found(
        self, client: TestClient, admin_auth_headers: dict
    ):
        """Get non-existent user returns 404."""
        response = client.get(f"/api/users/{uuid4()}", headers=admin_auth_headers)
        assert response.status_code == 404


class TestCreateUser:
    def test_create_user_as_admin(
        self, client: TestClient, admin_auth_headers: dict
    ):
        """Admin can create user."""
        response = client.post(
            "/api/users",
            json={
                "username": "newuser",
                "email": "new@example.com",
                "password": "password123",
            },
            headers=admin_auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["username"] == "newuser"
        assert data["role"] == "standard"

    def test_create_user_as_standard_user(
        self, client: TestClient, auth_headers: dict
    ):
        """Standard user cannot create users."""
        response = client.post(
            "/api/users",
            json={
                "username": "newuser",
                "email": "new@example.com",
                "password": "password123",
            },
            headers=auth_headers,
        )
        assert response.status_code == 403

    def test_create_user_duplicate_username(
        self, client: TestClient, admin_auth_headers: dict, db: Session
    ):
        """Cannot create user with duplicate username."""
        create_test_user(db, "existing", "existing@example.com")

        response = client.post(
            "/api/users",
            json={
                "username": "existing",
                "email": "different@example.com",
                "password": "password123",
            },
            headers=admin_auth_headers,
        )
        assert response.status_code == 400
        assert "Username already registered" in response.json()["detail"]

    def test_create_user_duplicate_email(
        self, client: TestClient, admin_auth_headers: dict, db: Session
    ):
        """Cannot create user with duplicate email."""
        create_test_user(db, "existing", "existing@example.com")

        response = client.post(
            "/api/users",
            json={
                "username": "different",
                "email": "existing@example.com",
                "password": "password123",
            },
            headers=admin_auth_headers,
        )
        assert response.status_code == 400
        assert "Email already registered" in response.json()["detail"]


class TestUpdateUser:
    def test_update_user_as_admin(
        self, client: TestClient, admin_auth_headers: dict, db: Session
    ):
        """Admin can update any user."""
        user = create_test_user(db, "testuser", "test@example.com")

        response = client.put(
            f"/api/users/{user.id}",
            json={"username": "updateduser"},
            headers=admin_auth_headers,
        )
        assert response.status_code == 200
        assert response.json()["username"] == "updateduser"

    def test_update_user_role(
        self, client: TestClient, admin_auth_headers: dict, db: Session
    ):
        """Admin can update user role."""
        user = create_test_user(db, "testuser", "test@example.com")

        response = client.put(
            f"/api/users/{user.id}",
            json={"role": "admin"},
            headers=admin_auth_headers,
        )
        assert response.status_code == 200
        assert response.json()["role"] == "admin"

    def test_update_user_password(
        self, client: TestClient, admin_auth_headers: dict, db: Session
    ):
        """Admin can update user password."""
        user = create_test_user(db, "testuser", "test@example.com")

        response = client.put(
            f"/api/users/{user.id}",
            json={"password": "newpassword123"},
            headers=admin_auth_headers,
        )
        assert response.status_code == 200

    def test_update_user_as_standard_user(
        self, client: TestClient, auth_headers: dict, db: Session
    ):
        """Standard user cannot update users."""
        user = create_test_user(db, "other", "other@example.com")

        response = client.put(
            f"/api/users/{user.id}",
            json={"username": "hacked"},
            headers=auth_headers,
        )
        assert response.status_code == 403

    def test_update_user_duplicate_username(
        self, client: TestClient, admin_auth_headers: dict, db: Session
    ):
        """Cannot update user to duplicate username."""
        create_test_user(db, "existing", "existing@example.com")
        user = create_test_user(db, "original", "original@example.com")

        response = client.put(
            f"/api/users/{user.id}",
            json={"username": "existing"},
            headers=admin_auth_headers,
        )
        assert response.status_code == 400
        assert "Username already taken" in response.json()["detail"]

    def test_update_user_duplicate_email(
        self, client: TestClient, admin_auth_headers: dict, db: Session
    ):
        """Cannot update user to duplicate email."""
        create_test_user(db, "existing", "existing@example.com")
        user = create_test_user(db, "original", "original@example.com")

        response = client.put(
            f"/api/users/{user.id}",
            json={"email": "existing@example.com"},
            headers=admin_auth_headers,
        )
        assert response.status_code == 400
        assert "Email already taken" in response.json()["detail"]

    def test_update_user_not_found(
        self, client: TestClient, admin_auth_headers: dict
    ):
        """Update non-existent user returns 404."""
        response = client.put(
            f"/api/users/{uuid4()}",
            json={"username": "new"},
            headers=admin_auth_headers,
        )
        assert response.status_code == 404


class TestDeleteUser:
    def test_delete_user_as_admin(
        self, client: TestClient, admin_auth_headers: dict, db: Session
    ):
        """Admin can delete other users."""
        user = create_test_user(db, "todelete", "delete@example.com")

        response = client.delete(
            f"/api/users/{user.id}", headers=admin_auth_headers
        )
        assert response.status_code == 204

        # Verify deleted
        response = client.get(f"/api/users/{user.id}", headers=admin_auth_headers)
        assert response.status_code == 404

    def test_delete_self_forbidden(
        self, client: TestClient, admin_auth_headers: dict, admin_user: User
    ):
        """Admin cannot delete their own account."""
        response = client.delete(
            f"/api/users/{admin_user.id}", headers=admin_auth_headers
        )
        assert response.status_code == 400
        assert "Cannot delete your own account" in response.json()["detail"]

    def test_delete_user_as_standard_user(
        self, client: TestClient, auth_headers: dict, db: Session
    ):
        """Standard user cannot delete users."""
        user = create_test_user(db, "other", "other@example.com")

        response = client.delete(f"/api/users/{user.id}", headers=auth_headers)
        assert response.status_code == 403

    def test_delete_user_not_found(
        self, client: TestClient, admin_auth_headers: dict
    ):
        """Delete non-existent user returns 404."""
        response = client.delete(
            f"/api/users/{uuid4()}", headers=admin_auth_headers
        )
        assert response.status_code == 404
