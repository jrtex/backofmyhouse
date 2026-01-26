import factory
from uuid import uuid4

from app.models.recipe import Recipe


class RecipeFactory(factory.Factory):
    class Meta:
        model = Recipe

    id = factory.LazyFunction(uuid4)
    title = factory.Sequence(lambda n: f"Recipe {n}")
    description = factory.Faker("paragraph")
    ingredients = factory.LazyFunction(lambda: [
        {"name": "Salt", "quantity": "1", "unit": "tsp", "notes": None},
        {"name": "Pepper", "quantity": "1/2", "unit": "tsp", "notes": None},
    ])
    instructions = factory.LazyFunction(lambda: [
        {"step_number": 1, "text": "Prepare ingredients"},
        {"step_number": 2, "text": "Cook and serve"},
    ])
    prep_time_minutes = 15
    cook_time_minutes = 30
    servings = 4
    notes = None
    category_id = None
    user_id = None
