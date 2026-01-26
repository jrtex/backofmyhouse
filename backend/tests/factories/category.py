import factory
from uuid import uuid4

from app.models.category import Category


class CategoryFactory(factory.Factory):
    class Meta:
        model = Category

    id = factory.LazyFunction(uuid4)
    name = factory.Sequence(lambda n: f"Category {n}")
    description = factory.Faker("sentence")
