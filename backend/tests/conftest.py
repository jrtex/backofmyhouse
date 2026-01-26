import os
import pytest
from typing import Generator
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database import Base, get_db
from app.models.user import User, UserRole
from app.services.auth import AuthService


def get_test_database_url():
    """Get database URL from environment or default to SQLite."""
    return os.environ.get("DATABASE_URL", "sqlite:///:memory:")


def create_test_engine():
    """Create engine based on database URL."""
    database_url = get_test_database_url()

    if database_url.startswith("sqlite"):
        # SQLite configuration (local development)
        engine = create_engine(
            database_url,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )

        # Enable foreign key support in SQLite
        @event.listens_for(engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()
    else:
        # PostgreSQL configuration (CI environment)
        engine = create_engine(database_url)

    return engine


engine = create_test_engine()
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db() -> Generator[Session, None, None]:
    """Create a fresh database for each test."""
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db: Session) -> Generator[TestClient, None, None]:
    """Create a test client with database dependency override."""
    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def test_user(db: Session) -> User:
    """Create a standard test user."""
    user = User(
        id=uuid4(),
        username="testuser",
        email="test@example.com",
        hashed_password=AuthService.hash_password("testpassword123"),
        role=UserRole.standard,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def admin_user(db: Session) -> User:
    """Create an admin test user."""
    user = User(
        id=uuid4(),
        username="adminuser",
        email="admin@example.com",
        hashed_password=AuthService.hash_password("adminpassword123"),
        role=UserRole.admin,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def auth_headers(test_user: User) -> dict:
    """Get authentication headers for a standard user."""
    access_token = AuthService.create_access_token(test_user.id, test_user.role)
    return {"Cookie": f"access_token={access_token}"}


@pytest.fixture
def admin_auth_headers(admin_user: User) -> dict:
    """Get authentication headers for an admin user."""
    access_token = AuthService.create_access_token(admin_user.id, admin_user.role)
    return {"Cookie": f"access_token={access_token}"}


def create_test_user(
    db: Session,
    username: str = "user",
    email: str = "user@example.com",
    password: str = "password123",
    role: UserRole = UserRole.standard,
) -> User:
    """Helper function to create a user with custom attributes."""
    user = User(
        id=uuid4(),
        username=username,
        email=email,
        hashed_password=AuthService.hash_password(password),
        role=role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
