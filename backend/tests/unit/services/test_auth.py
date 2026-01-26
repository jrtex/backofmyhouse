import pytest
from uuid import uuid4
from datetime import datetime, timedelta

from app.services.auth import AuthService
from app.models.user import User, UserRole


class TestPasswordHashing:
    def test_hash_password_returns_different_value(self):
        password = "mysecretpassword"
        hashed = AuthService.hash_password(password)
        assert hashed != password
        assert len(hashed) > 0

    def test_hash_password_produces_unique_hashes(self):
        password = "mysecretpassword"
        hash1 = AuthService.hash_password(password)
        hash2 = AuthService.hash_password(password)
        # Bcrypt produces different hashes for same password (due to salt)
        assert hash1 != hash2

    def test_verify_password_correct(self):
        password = "mysecretpassword"
        hashed = AuthService.hash_password(password)
        assert AuthService.verify_password(password, hashed) is True

    def test_verify_password_incorrect(self):
        password = "mysecretpassword"
        hashed = AuthService.hash_password(password)
        assert AuthService.verify_password("wrongpassword", hashed) is False

    def test_verify_password_empty_password(self):
        hashed = AuthService.hash_password("somepassword")
        assert AuthService.verify_password("", hashed) is False


class TestAccessToken:
    def test_create_access_token(self):
        user_id = uuid4()
        role = UserRole.standard
        token = AuthService.create_access_token(user_id, role)
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0

    def test_create_access_token_different_roles(self):
        user_id = uuid4()
        standard_token = AuthService.create_access_token(user_id, UserRole.standard)
        admin_token = AuthService.create_access_token(user_id, UserRole.admin)
        # Tokens should be different due to different role claims
        assert standard_token != admin_token

    def test_decode_access_token(self):
        user_id = uuid4()
        role = UserRole.admin
        token = AuthService.create_access_token(user_id, role)
        payload = AuthService.decode_token(token)

        assert payload is not None
        assert payload["sub"] == str(user_id)
        assert payload["role"] == role.value
        assert payload["type"] == "access"
        assert "exp" in payload

    def test_decode_invalid_token(self):
        payload = AuthService.decode_token("invalid.token.here")
        assert payload is None

    def test_decode_tampered_token(self):
        user_id = uuid4()
        token = AuthService.create_access_token(user_id, UserRole.standard)
        # Tamper with the token
        tampered_token = token[:-5] + "xxxxx"
        payload = AuthService.decode_token(tampered_token)
        assert payload is None


class TestRefreshToken:
    def test_create_refresh_token(self):
        user_id = uuid4()
        token = AuthService.create_refresh_token(user_id)
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0

    def test_decode_refresh_token(self):
        user_id = uuid4()
        token = AuthService.create_refresh_token(user_id)
        payload = AuthService.decode_token(token)

        assert payload is not None
        assert payload["sub"] == str(user_id)
        assert payload["type"] == "refresh"
        assert "exp" in payload
        # Refresh token should not have role claim
        assert "role" not in payload

    def test_access_and_refresh_tokens_differ(self):
        user_id = uuid4()
        access_token = AuthService.create_access_token(user_id, UserRole.standard)
        refresh_token = AuthService.create_refresh_token(user_id)
        assert access_token != refresh_token


class TestUserQueries:
    def test_get_user_by_username(self, db, test_user):
        found_user = AuthService.get_user_by_username(db, test_user.username)
        assert found_user is not None
        assert found_user.id == test_user.id

    def test_get_user_by_username_not_found(self, db):
        found_user = AuthService.get_user_by_username(db, "nonexistent")
        assert found_user is None

    def test_get_user_by_email(self, db, test_user):
        found_user = AuthService.get_user_by_email(db, test_user.email)
        assert found_user is not None
        assert found_user.id == test_user.id

    def test_get_user_by_email_not_found(self, db):
        found_user = AuthService.get_user_by_email(db, "nonexistent@example.com")
        assert found_user is None

    def test_get_user_by_id(self, db, test_user):
        found_user = AuthService.get_user_by_id(db, test_user.id)
        assert found_user is not None
        assert found_user.username == test_user.username

    def test_get_user_by_id_not_found(self, db):
        found_user = AuthService.get_user_by_id(db, uuid4())
        assert found_user is None


class TestCreateUser:
    def test_create_first_user_is_admin(self, db):
        user = AuthService.create_user(
            db,
            username="firstuser",
            email="first@example.com",
            password="password123",
        )
        assert user.role == UserRole.admin

    def test_create_second_user_is_standard(self, db):
        # Create first user (will be admin)
        AuthService.create_user(db, "first", "first@example.com", "password123")

        # Create second user (should be standard)
        user = AuthService.create_user(
            db,
            username="seconduser",
            email="second@example.com",
            password="password123",
        )
        assert user.role == UserRole.standard

    def test_create_user_hashes_password(self, db):
        plain_password = "mypassword123"
        user = AuthService.create_user(
            db,
            username="testuser",
            email="test@example.com",
            password=plain_password,
        )
        assert user.hashed_password != plain_password
        assert AuthService.verify_password(plain_password, user.hashed_password)


class TestAuthenticateUser:
    def test_authenticate_user_success(self, db, test_user):
        # test_user has password "testpassword123"
        user = AuthService.authenticate_user(db, "testuser", "testpassword123")
        assert user is not None
        assert user.id == test_user.id

    def test_authenticate_user_wrong_password(self, db, test_user):
        user = AuthService.authenticate_user(db, "testuser", "wrongpassword")
        assert user is None

    def test_authenticate_user_nonexistent_username(self, db):
        user = AuthService.authenticate_user(db, "nonexistent", "password")
        assert user is None
