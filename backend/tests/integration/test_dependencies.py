import pytest
from uuid import uuid4

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.dependencies import get_current_user, get_current_user_optional, require_admin
from app.services.auth import AuthService
from app.models.user import User, UserRole


class TestGetCurrentUser:
    def test_no_token_raises_401(self, db: Session):
        """Test that missing token raises 401."""
        with pytest.raises(HTTPException) as exc_info:
            # Simulate dependency with no token
            gen = get_current_user(access_token=None, db=db)
            next(gen) if hasattr(gen, '__next__') else gen
        assert exc_info.value.status_code == 401
        assert "Not authenticated" in exc_info.value.detail

    def test_invalid_token_raises_401(self, db: Session):
        """Test that invalid token raises 401."""
        with pytest.raises(HTTPException) as exc_info:
            get_current_user(access_token="invalid.token.here", db=db)
        assert exc_info.value.status_code == 401
        assert "Invalid or expired token" in exc_info.value.detail

    def test_refresh_token_raises_401(self, db: Session, test_user: User):
        """Test that refresh token (wrong type) raises 401."""
        refresh_token = AuthService.create_refresh_token(test_user.id)
        with pytest.raises(HTTPException) as exc_info:
            get_current_user(access_token=refresh_token, db=db)
        assert exc_info.value.status_code == 401
        assert "Invalid token type" in exc_info.value.detail

    def test_user_not_found_raises_401(self, db: Session):
        """Test that token for non-existent user raises 401."""
        fake_user_id = uuid4()
        access_token = AuthService.create_access_token(fake_user_id, UserRole.standard)
        with pytest.raises(HTTPException) as exc_info:
            get_current_user(access_token=access_token, db=db)
        assert exc_info.value.status_code == 401
        assert "User not found" in exc_info.value.detail

    def test_valid_token_returns_user(self, db: Session, test_user: User):
        """Test that valid token returns the user."""
        access_token = AuthService.create_access_token(test_user.id, test_user.role)
        user = get_current_user(access_token=access_token, db=db)
        assert user.id == test_user.id
        assert user.username == test_user.username


class TestGetCurrentUserOptional:
    def test_no_token_returns_none(self, db: Session):
        """Test that missing token returns None."""
        result = get_current_user_optional(access_token=None, db=db)
        assert result is None

    def test_invalid_token_returns_none(self, db: Session):
        """Test that invalid token returns None."""
        result = get_current_user_optional(access_token="invalid.token", db=db)
        assert result is None

    def test_refresh_token_returns_none(self, db: Session, test_user: User):
        """Test that refresh token returns None."""
        refresh_token = AuthService.create_refresh_token(test_user.id)
        result = get_current_user_optional(access_token=refresh_token, db=db)
        assert result is None

    def test_valid_token_returns_user(self, db: Session, test_user: User):
        """Test that valid token returns the user."""
        access_token = AuthService.create_access_token(test_user.id, test_user.role)
        user = get_current_user_optional(access_token=access_token, db=db)
        assert user is not None
        assert user.id == test_user.id


class TestRequireAdmin:
    def test_standard_user_raises_403(self, test_user: User):
        """Test that standard user raises 403."""
        with pytest.raises(HTTPException) as exc_info:
            require_admin(current_user=test_user)
        assert exc_info.value.status_code == 403
        assert "Admin access required" in exc_info.value.detail

    def test_admin_user_passes(self, admin_user: User):
        """Test that admin user passes through."""
        result = require_admin(current_user=admin_user)
        assert result.id == admin_user.id
        assert result.role == UserRole.admin
