"""Unit tests for schema.org to RecipeExtraction mapper."""

import pytest

from app.schemas.import_schemas import RecipeExtraction
from app.services.schema_mapper import map_schema_org_to_extraction


class TestMapSchemaOrgToExtraction:
    """Tests for the schema.org mapping function."""

    def test_maps_full_recipe_data(self):
        """Should map all fields from a complete schema.org Recipe."""
        schema_data = {
            "@type": "Recipe",
            "name": "Chocolate Chip Cookies",
            "description": "Classic homemade cookies",
            "recipeIngredient": [
                "2 1/4 cups all-purpose flour",
                "1 cup butter, softened",
                "2 cups chocolate chips",
            ],
            "recipeInstructions": [
                {"@type": "HowToStep", "text": "Preheat oven to 375F."},
                {"@type": "HowToStep", "text": "Mix ingredients."},
                {"@type": "HowToStep", "text": "Bake for 10 minutes."},
            ],
            "prepTime": "PT15M",
            "cookTime": "PT10M",
            "recipeYield": "24 cookies",
        }

        result = map_schema_org_to_extraction(schema_data)

        assert isinstance(result, RecipeExtraction)
        assert result.title == "Chocolate Chip Cookies"
        assert result.description == "Classic homemade cookies"
        assert len(result.ingredients) == 3
        assert len(result.instructions) == 3
        assert result.prep_time_minutes == 15
        assert result.cook_time_minutes == 10
        assert result.servings == 24
        assert result.confidence == 0.9  # High confidence for schema.org

    def test_maps_minimal_recipe_data(self):
        """Should handle recipe with only required fields."""
        schema_data = {
            "@type": "Recipe",
            "name": "Simple Recipe",
        }

        result = map_schema_org_to_extraction(schema_data)

        assert result.title == "Simple Recipe"
        assert result.description is None
        assert result.ingredients == []
        assert result.instructions == []
        assert result.prep_time_minutes is None
        assert result.cook_time_minutes is None
        assert result.servings is None

    def test_parses_iso8601_duration_minutes(self):
        """Should correctly parse PT30M format."""
        schema_data = {
            "@type": "Recipe",
            "name": "Test",
            "prepTime": "PT30M",
            "cookTime": "PT45M",
        }

        result = map_schema_org_to_extraction(schema_data)

        assert result.prep_time_minutes == 30
        assert result.cook_time_minutes == 45

    def test_parses_iso8601_duration_hours(self):
        """Should correctly parse PT1H30M format."""
        schema_data = {
            "@type": "Recipe",
            "name": "Test",
            "prepTime": "PT1H30M",
            "cookTime": "PT2H",
        }

        result = map_schema_org_to_extraction(schema_data)

        assert result.prep_time_minutes == 90  # 1h30m = 90min
        assert result.cook_time_minutes == 120  # 2h = 120min

    def test_parses_iso8601_duration_days(self):
        """Should handle P1DT2H30M format (for marinating, etc)."""
        schema_data = {
            "@type": "Recipe",
            "name": "Test",
            "prepTime": "P1DT2H30M",  # 1 day, 2 hours, 30 minutes
        }

        result = map_schema_org_to_extraction(schema_data)

        # 1 day = 1440min, 2h = 120min, 30min = 30min = 1590min
        assert result.prep_time_minutes == 1590

    def test_handles_invalid_duration_gracefully(self):
        """Should return None for unparseable durations."""
        schema_data = {
            "@type": "Recipe",
            "name": "Test",
            "prepTime": "30 minutes",  # Not ISO 8601
            "cookTime": "invalid",
        }

        result = map_schema_org_to_extraction(schema_data)

        assert result.prep_time_minutes is None
        assert result.cook_time_minutes is None
        assert any("prep" in w.lower() or "time" in w.lower() for w in result.warnings)

    def test_parses_ingredient_with_quantity_and_unit(self):
        """Should parse ingredient strings into structured data."""
        schema_data = {
            "@type": "Recipe",
            "name": "Test",
            "recipeIngredient": [
                "2 cups all-purpose flour",
                "1/2 teaspoon salt",
                "3 large eggs",
            ],
        }

        result = map_schema_org_to_extraction(schema_data)

        assert len(result.ingredients) == 3
        # First ingredient
        assert result.ingredients[0].quantity == "2"
        assert result.ingredients[0].unit == "cups"
        assert result.ingredients[0].name == "all-purpose flour"
        # Second ingredient
        assert result.ingredients[1].quantity == "1/2"
        assert result.ingredients[1].unit == "teaspoon"
        # Third ingredient
        assert result.ingredients[2].quantity == "3"

    def test_parses_ingredient_without_unit(self):
        """Should handle ingredients with quantity but no unit."""
        schema_data = {
            "@type": "Recipe",
            "name": "Test",
            "recipeIngredient": [
                "3 eggs",
                "1 lemon",
            ],
        }

        result = map_schema_org_to_extraction(schema_data)

        assert result.ingredients[0].quantity == "3"
        assert result.ingredients[0].name == "eggs"
        assert result.ingredients[1].quantity == "1"
        assert result.ingredients[1].name == "lemon"

    def test_parses_ingredient_name_only(self):
        """Should handle ingredients without quantity."""
        schema_data = {
            "@type": "Recipe",
            "name": "Test",
            "recipeIngredient": [
                "salt to taste",
                "fresh herbs",
            ],
        }

        result = map_schema_org_to_extraction(schema_data)

        assert len(result.ingredients) == 2
        # Name should contain the full text when no quantity detected
        assert "salt" in result.ingredients[0].name.lower()
        assert "herbs" in result.ingredients[1].name.lower()

    def test_handles_howto_step_instructions(self):
        """Should parse HowToStep format instructions."""
        schema_data = {
            "@type": "Recipe",
            "name": "Test",
            "recipeInstructions": [
                {"@type": "HowToStep", "text": "First step."},
                {"@type": "HowToStep", "text": "Second step."},
            ],
        }

        result = map_schema_org_to_extraction(schema_data)

        assert len(result.instructions) == 2
        assert result.instructions[0].step_number == 1
        assert result.instructions[0].text == "First step."
        assert result.instructions[1].step_number == 2
        assert result.instructions[1].text == "Second step."

    def test_handles_string_instructions(self):
        """Should parse string format instructions."""
        schema_data = {
            "@type": "Recipe",
            "name": "Test",
            "recipeInstructions": [
                "First step.",
                "Second step.",
            ],
        }

        result = map_schema_org_to_extraction(schema_data)

        assert len(result.instructions) == 2
        assert result.instructions[0].text == "First step."
        assert result.instructions[1].text == "Second step."

    def test_handles_single_string_instruction(self):
        """Should handle single string instruction (not in array)."""
        schema_data = {
            "@type": "Recipe",
            "name": "Test",
            "recipeInstructions": "Mix all ingredients and bake at 350F for 30 minutes.",
        }

        result = map_schema_org_to_extraction(schema_data)

        assert len(result.instructions) >= 1
        assert "Mix all ingredients" in result.instructions[0].text

    def test_handles_howto_section_instructions(self):
        """Should handle HowToSection format with nested steps."""
        schema_data = {
            "@type": "Recipe",
            "name": "Test",
            "recipeInstructions": [
                {
                    "@type": "HowToSection",
                    "name": "Prepare",
                    "itemListElement": [
                        {"@type": "HowToStep", "text": "Preheat oven."},
                        {"@type": "HowToStep", "text": "Grease pan."},
                    ],
                },
                {
                    "@type": "HowToSection",
                    "name": "Bake",
                    "itemListElement": [
                        {"@type": "HowToStep", "text": "Pour batter."},
                    ],
                },
            ],
        }

        result = map_schema_org_to_extraction(schema_data)

        assert len(result.instructions) == 3
        assert result.instructions[0].text == "Preheat oven."
        assert result.instructions[2].text == "Pour batter."

    def test_extracts_servings_from_yield_number(self):
        """Should extract number from recipeYield."""
        schema_data = {
            "@type": "Recipe",
            "name": "Test",
            "recipeYield": "12 servings",
        }

        result = map_schema_org_to_extraction(schema_data)

        assert result.servings == 12

    def test_extracts_servings_from_yield_range(self):
        """Should use first number from yield range."""
        schema_data = {
            "@type": "Recipe",
            "name": "Test",
            "recipeYield": "8-10 servings",
        }

        result = map_schema_org_to_extraction(schema_data)

        assert result.servings == 8

    def test_handles_numeric_yield(self):
        """Should handle numeric recipeYield."""
        schema_data = {
            "@type": "Recipe",
            "name": "Test",
            "recipeYield": 6,
        }

        result = map_schema_org_to_extraction(schema_data)

        assert result.servings == 6

    def test_adds_warning_for_unmapped_fields(self):
        """Should add warning when fields cannot be mapped."""
        schema_data = {
            "@type": "Recipe",
            "name": "Test",
            "prepTime": "not-valid-duration",
        }

        result = map_schema_org_to_extraction(schema_data)

        assert len(result.warnings) > 0

    def test_confidence_is_09_for_schema_org(self):
        """Should set confidence to 0.9 for schema.org extraction."""
        schema_data = {
            "@type": "Recipe",
            "name": "Test",
        }

        result = map_schema_org_to_extraction(schema_data)

        assert result.confidence == 0.9

    def test_handles_missing_name_field(self):
        """Should raise error or use fallback when name is missing."""
        schema_data = {
            "@type": "Recipe",
            "description": "A recipe without a name",
        }

        # Should either raise ValueError or use a fallback title
        with pytest.raises(ValueError):
            map_schema_org_to_extraction(schema_data)

    def test_handles_empty_ingredients_list(self):
        """Should handle empty recipeIngredient array."""
        schema_data = {
            "@type": "Recipe",
            "name": "Test",
            "recipeIngredient": [],
        }

        result = map_schema_org_to_extraction(schema_data)

        assert result.ingredients == []

    def test_handles_complex_ingredient_strings(self):
        """Should handle complex ingredient descriptions."""
        schema_data = {
            "@type": "Recipe",
            "name": "Test",
            "recipeIngredient": [
                "2 1/2 cups (310g) all-purpose flour, sifted",
                "1 (14 oz) can coconut milk",
                "8 ounces cream cheese, softened",
            ],
        }

        result = map_schema_org_to_extraction(schema_data)

        assert len(result.ingredients) == 3
        # Should extract some meaningful data from each
        assert result.ingredients[0].name  # Should have a name
        assert result.ingredients[1].name
        assert result.ingredients[2].name
