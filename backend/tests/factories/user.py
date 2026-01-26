import factory
from uuid import uuid4

from app.models.user import User, UserRole
from app.services.auth import AuthService


class UserFactory(factory.Factory):
    class Meta:
        model = User

    id = factory.LazyFunction(uuid4)
    username = factory.Sequence(lambda n: f"user{n}")
    email = factory.LazyAttribute(lambda obj: f"{obj.username}@example.com")
    hashed_password = factory.LazyFunction(lambda: AuthService.hash_password("password123"))
    role = UserRole.standard

    @classmethod
    def create_admin(cls, **kwargs):
        return cls(role=UserRole.admin, **kwargs)
