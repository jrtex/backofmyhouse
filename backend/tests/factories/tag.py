import factory
from uuid import uuid4

from app.models.tag import Tag


class TagFactory(factory.Factory):
    class Meta:
        model = Tag

    id = factory.LazyFunction(uuid4)
    name = factory.Sequence(lambda n: f"tag{n}")
