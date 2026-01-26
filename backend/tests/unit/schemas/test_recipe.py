import pytest
from pydantic import ValidationError
from uuid import uuid4

from app.schemas.recipe import (
    Ingredient,
    Instruction,
    RecipeCreate,
    RecipeUpdate,
    RecipeResponse,
    RecipeListResponse,
)


class TestIngredient:
    def test_valid_ingredient(self):
        ingredient = Ingredient(name="Salt", quantity="1", unit="tsp", notes="to taste")
        assert ingredient.name == "Salt"
        assert ingredient.quantity == "1"
        assert ingredient.unit == "tsp"
        assert ingredient.notes == "to taste"

    def test_ingredient_name_required(self):
        with pytest.raises(ValidationError):
            Ingredient(quantity="1", unit="tsp")

    def test_optional_fields(self):
        ingredient = Ingredient(name="Salt")
        assert ingredient.quantity is None
        assert ingredient.unit is None
        assert ingredient.notes is None


class TestInstruction:
    def test_valid_instruction(self):
        instruction = Instruction(step_number=1, text="Mix ingredients well")
        assert instruction.step_number == 1
        assert instruction.text == "Mix ingredients well"

    def test_required_fields(self):
        with pytest.raises(ValidationError):
            Instruction(step_number=1)

        with pytest.raises(ValidationError):
            Instruction(text="Mix ingredients")


class TestRecipeCreate:
    def test_valid_recipe_create(self):
        data = {
            "title": "Test Recipe",
            "description": "A test recipe",
            "ingredients": [{"name": "Salt", "quantity": "1", "unit": "tsp"}],
            "instructions": [{"step_number": 1, "text": "Mix well"}],
            "prep_time_minutes": 10,
            "cook_time_minutes": 20,
            "servings": 4,
            "notes": "Test notes",
            "category_id": uuid4(),
            "tag_ids": [uuid4(), uuid4()],
        }
        recipe = RecipeCreate(**data)
        assert recipe.title == "Test Recipe"
        assert len(recipe.ingredients) == 1
        assert len(recipe.instructions) == 1

    def test_minimal_recipe(self):
        recipe = RecipeCreate(title="Minimal Recipe")
        assert recipe.title == "Minimal Recipe"
        assert recipe.ingredients == []
        assert recipe.instructions == []
        assert recipe.tag_ids == []

    def test_title_required(self):
        with pytest.raises(ValidationError):
            RecipeCreate(description="No title")

    def test_title_too_short(self):
        with pytest.raises(ValidationError) as exc_info:
            RecipeCreate(title="")
        assert "at least 1 character" in str(exc_info.value)

    def test_title_too_long(self):
        with pytest.raises(ValidationError) as exc_info:
            RecipeCreate(title="a" * 256)
        assert "at most 255 characters" in str(exc_info.value)

    def test_negative_prep_time(self):
        with pytest.raises(ValidationError) as exc_info:
            RecipeCreate(title="Test", prep_time_minutes=-5)
        assert "greater than or equal to 0" in str(exc_info.value)

    def test_negative_cook_time(self):
        with pytest.raises(ValidationError) as exc_info:
            RecipeCreate(title="Test", cook_time_minutes=-10)
        assert "greater than or equal to 0" in str(exc_info.value)

    def test_zero_servings_invalid(self):
        with pytest.raises(ValidationError) as exc_info:
            RecipeCreate(title="Test", servings=0)
        assert "greater than or equal to 1" in str(exc_info.value)

    def test_zero_prep_time_valid(self):
        recipe = RecipeCreate(title="Test", prep_time_minutes=0)
        assert recipe.prep_time_minutes == 0


class TestRecipeUpdate:
    def test_all_fields_optional(self):
        update = RecipeUpdate()
        assert update.title is None
        assert update.ingredients is None
        assert update.tag_ids is None

    def test_partial_update(self):
        update = RecipeUpdate(title="New Title", servings=6)
        assert update.title == "New Title"
        assert update.servings == 6
        assert update.description is None

    def test_clear_category(self):
        # Setting category_id to None in update should be valid
        update = RecipeUpdate(category_id=None)
        assert update.category_id is None

    def test_empty_tag_list(self):
        update = RecipeUpdate(tag_ids=[])
        assert update.tag_ids == []


class TestRecipeResponse:
    def test_from_attributes_config(self):
        assert RecipeResponse.model_config.get("from_attributes") is True


class TestRecipeListResponse:
    def test_from_attributes_config(self):
        assert RecipeListResponse.model_config.get("from_attributes") is True
