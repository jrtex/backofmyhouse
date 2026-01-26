import pytest
from pydantic import ValidationError
from uuid import uuid4
from datetime import datetime

from app.schemas.user import UserCreate, UserUpdate, UserResponse, UserLogin
from app.models.user import UserRole


class TestUserCreate:
    def test_valid_user_create(self):
        data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "password123",
        }
        user = UserCreate(**data)
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.password == "password123"

    def test_username_too_short(self):
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(username="ab", email="test@example.com", password="password123")
        assert "String should have at least 3 characters" in str(exc_info.value)

    def test_username_too_long(self):
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(
                username="a" * 51,
                email="test@example.com",
                password="password123",
            )
        assert "String should have at most 50 characters" in str(exc_info.value)

    def test_invalid_email(self):
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(username="testuser", email="notanemail", password="password123")
        assert "email" in str(exc_info.value).lower()

    def test_password_too_short(self):
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(username="testuser", email="test@example.com", password="short")
        assert "String should have at least 8 characters" in str(exc_info.value)

    def test_password_too_long(self):
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(
                username="testuser",
                email="test@example.com",
                password="a" * 101,
            )
        assert "String should have at most 100 characters" in str(exc_info.value)

    def test_missing_required_fields(self):
        with pytest.raises(ValidationError):
            UserCreate(username="testuser")

        with pytest.raises(ValidationError):
            UserCreate(email="test@example.com")


class TestUserUpdate:
    def test_all_fields_optional(self):
        user = UserUpdate()
        assert user.username is None
        assert user.email is None
        assert user.password is None
        assert user.role is None

    def test_partial_update(self):
        user = UserUpdate(username="newname")
        assert user.username == "newname"
        assert user.email is None

    def test_role_update(self):
        user = UserUpdate(role=UserRole.admin)
        assert user.role == UserRole.admin

    def test_invalid_role(self):
        with pytest.raises(ValidationError):
            UserUpdate(role="superuser")

    def test_username_validation_when_provided(self):
        with pytest.raises(ValidationError):
            UserUpdate(username="ab")  # too short


class TestUserResponse:
    def test_valid_response(self):
        data = {
            "id": uuid4(),
            "username": "testuser",
            "email": "test@example.com",
            "role": UserRole.standard,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }
        response = UserResponse(**data)
        assert response.username == "testuser"
        assert response.role == UserRole.standard

    def test_from_attributes_config(self):
        # Test that from_attributes is set correctly
        assert UserResponse.model_config.get("from_attributes") is True


class TestUserLogin:
    def test_valid_login(self):
        login = UserLogin(username="testuser", password="password123")
        assert login.username == "testuser"
        assert login.password == "password123"

    def test_missing_username(self):
        with pytest.raises(ValidationError):
            UserLogin(password="password123")

    def test_missing_password(self):
        with pytest.raises(ValidationError):
            UserLogin(username="testuser")
