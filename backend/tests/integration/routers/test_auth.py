import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.user import User, UserRole
from tests.conftest import create_test_user


class TestRegister:
    def test_register_first_user_becomes_admin(self, client: TestClient):
        """First registered user should become admin."""
        response = client.post(
            "/api/auth/register",
            json={
                "username": "firstuser",
                "email": "first@example.com",
                "password": "password123",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["message"] == "User registered successfully"
        assert data["role"] == "admin"

    def test_register_subsequent_user_is_standard(
        self, client: TestClient, db: Session
    ):
        """Subsequent users should be standard role."""
        # Create first user
        create_test_user(db, "admin", "admin@example.com")

        response = client.post(
            "/api/auth/register",
            json={
                "username": "seconduser",
                "email": "second@example.com",
                "password": "password123",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["role"] == "standard"

    def test_register_duplicate_username(self, client: TestClient, test_user: User):
        """Cannot register with existing username."""
        response = client.post(
            "/api/auth/register",
            json={
                "username": test_user.username,
                "email": "different@example.com",
                "password": "password123",
            },
        )
        assert response.status_code == 400
        assert "Username already registered" in response.json()["detail"]

    def test_register_duplicate_email(self, client: TestClient, test_user: User):
        """Cannot register with existing email."""
        response = client.post(
            "/api/auth/register",
            json={
                "username": "differentuser",
                "email": test_user.email,
                "password": "password123",
            },
        )
        assert response.status_code == 400
        assert "Email already registered" in response.json()["detail"]

    def test_register_invalid_email(self, client: TestClient):
        """Cannot register with invalid email format."""
        response = client.post(
            "/api/auth/register",
            json={
                "username": "testuser",
                "email": "notanemail",
                "password": "password123",
            },
        )
        assert response.status_code == 422

    def test_register_short_password(self, client: TestClient):
        """Cannot register with password less than 8 characters."""
        response = client.post(
            "/api/auth/register",
            json={
                "username": "testuser",
                "email": "test@example.com",
                "password": "short",
            },
        )
        assert response.status_code == 422


class TestLogin:
    def test_login_success(self, client: TestClient, test_user: User):
        """Successful login sets cookies."""
        response = client.post(
            "/api/auth/login",
            json={"username": "testuser", "password": "testpassword123"},
        )
        assert response.status_code == 200
        assert response.json()["message"] == "Login successful"

        # Check cookies are set
        cookies = response.cookies
        assert "access_token" in cookies
        assert "refresh_token" in cookies
        assert "logged_in" in cookies

    def test_login_wrong_password(self, client: TestClient, test_user: User):
        """Login fails with wrong password."""
        response = client.post(
            "/api/auth/login",
            json={"username": "testuser", "password": "wrongpassword"},
        )
        assert response.status_code == 401
        assert "Invalid username or password" in response.json()["detail"]

    def test_login_nonexistent_user(self, client: TestClient):
        """Login fails for non-existent user."""
        response = client.post(
            "/api/auth/login",
            json={"username": "nonexistent", "password": "password123"},
        )
        assert response.status_code == 401


class TestLogout:
    def test_logout_success(self, client: TestClient, auth_headers: dict):
        """Successful logout clears cookies."""
        response = client.post("/api/auth/logout", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["message"] == "Logged out successfully"

    def test_logout_without_auth(self, client: TestClient):
        """Logout without authentication returns 401."""
        response = client.post("/api/auth/logout")
        assert response.status_code == 401


class TestRefresh:
    def test_refresh_token_success(self, client: TestClient, test_user: User):
        """Refresh token generates new access token."""
        from app.services.auth import AuthService

        refresh_token = AuthService.create_refresh_token(test_user.id)
        client.cookies.set("refresh_token", refresh_token)

        response = client.post("/api/auth/refresh")
        assert response.status_code == 200
        assert response.json()["message"] == "Token refreshed successfully"
        assert "access_token" in response.cookies

    def test_refresh_without_token(self, client: TestClient):
        """Refresh without token returns 401."""
        response = client.post("/api/auth/refresh")
        assert response.status_code == 401
        assert "No refresh token provided" in response.json()["detail"]

    def test_refresh_with_invalid_token(self, client: TestClient):
        """Refresh with invalid token returns 401."""
        client.cookies.set("refresh_token", "invalid.token.here")
        response = client.post("/api/auth/refresh")
        assert response.status_code == 401
        assert "Invalid refresh token" in response.json()["detail"]

    def test_refresh_with_access_token(self, client: TestClient, test_user: User):
        """Cannot use access token as refresh token."""
        from app.services.auth import AuthService

        access_token = AuthService.create_access_token(test_user.id, test_user.role)
        client.cookies.set("refresh_token", access_token)

        response = client.post("/api/auth/refresh")
        assert response.status_code == 401


class TestMe:
    def test_get_current_user_info(self, client: TestClient, auth_headers: dict, test_user: User):
        """Get current user info returns user data."""
        response = client.get("/api/auth/me", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == test_user.username
        assert data["email"] == test_user.email
        assert data["role"] == test_user.role.value

    def test_get_me_without_auth(self, client: TestClient):
        """Get me without authentication returns 401."""
        response = client.get("/api/auth/me")
        assert response.status_code == 401
