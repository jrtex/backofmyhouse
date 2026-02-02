"""Service for mapping schema.org Recipe data to RecipeExtraction."""

import re
from typing import Any, List, Optional

from app.schemas.import_schemas import RecipeExtraction
from app.schemas.recipe import Ingredient, Instruction


# Confidence score for schema.org extraction (high but not perfect)
SCHEMA_ORG_CONFIDENCE = 0.9

# Common units for ingredient parsing
UNITS = [
    "cups?", "cup", "tablespoons?", "tbsp", "teaspoons?", "tsp",
    "ounces?", "oz", "pounds?", "lbs?", "lb", "grams?", "g",
    "kilograms?", "kg", "milliliters?", "ml", "liters?", "l",
    "pints?", "quarts?", "gallons?", "pinch", "dash", "slice",
    "slices", "piece", "pieces", "cloves?", "stalks?", "sprigs?",
    "bunches?", "heads?", "cans?", "packages?", "sticks?",
]


def map_schema_org_to_extraction(schema_data: dict) -> RecipeExtraction:
    """Map schema.org Recipe data to RecipeExtraction schema.

    Args:
        schema_data: Dictionary containing schema.org Recipe data.

    Returns:
        RecipeExtraction object with mapped data.

    Raises:
        ValueError: If required fields (name) are missing.
    """
    warnings: List[str] = []

    # Extract title (required)
    title = schema_data.get("name")
    if not title:
        raise ValueError("Recipe name is required in schema.org data")

    # Extract description
    description = schema_data.get("description")

    # Parse prep and cook times
    prep_time = _parse_iso8601_duration(schema_data.get("prepTime"))
    if schema_data.get("prepTime") and prep_time is None:
        warnings.append(f"Could not parse prep time: {schema_data.get('prepTime')}")

    cook_time = _parse_iso8601_duration(schema_data.get("cookTime"))
    if schema_data.get("cookTime") and cook_time is None:
        warnings.append(f"Could not parse cook time: {schema_data.get('cookTime')}")

    # Parse servings from recipeYield
    servings = _parse_servings(schema_data.get("recipeYield"))

    # Parse ingredients
    raw_ingredients = schema_data.get("recipeIngredient", [])
    if not isinstance(raw_ingredients, list):
        raw_ingredients = [raw_ingredients] if raw_ingredients else []
    ingredients = [_parse_ingredient(ing) for ing in raw_ingredients if ing]

    # Parse instructions
    raw_instructions = schema_data.get("recipeInstructions", [])
    instructions = _parse_instructions(raw_instructions)

    return RecipeExtraction(
        title=title,
        description=description,
        ingredients=ingredients,
        instructions=instructions,
        prep_time_minutes=prep_time,
        cook_time_minutes=cook_time,
        servings=servings,
        notes=None,
        special_equipment=None,
        confidence=SCHEMA_ORG_CONFIDENCE,
        warnings=warnings,
    )


def _parse_iso8601_duration(duration: Optional[str]) -> Optional[int]:
    """Parse ISO 8601 duration string to minutes.

    Supports formats like:
    - PT30M (30 minutes)
    - PT1H30M (1 hour 30 minutes)
    - PT2H (2 hours)
    - P1DT2H30M (1 day 2 hours 30 minutes)

    Args:
        duration: ISO 8601 duration string.

    Returns:
        Total minutes, or None if parsing fails.
    """
    if not duration or not isinstance(duration, str):
        return None

    # Match ISO 8601 duration pattern
    pattern = r"^P(?:(\d+)D)?(?:T(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?)?$"
    match = re.match(pattern, duration.upper())

    if not match:
        return None

    days = int(match.group(1) or 0)
    hours = int(match.group(2) or 0)
    minutes = int(match.group(3) or 0)
    # We ignore seconds for recipe times

    total_minutes = (days * 24 * 60) + (hours * 60) + minutes

    return total_minutes if total_minutes > 0 else None


def _parse_servings(recipe_yield: Any) -> Optional[int]:
    """Extract number of servings from recipeYield.

    Args:
        recipe_yield: recipeYield value (string or number).

    Returns:
        Number of servings, or None if not parseable.
    """
    if recipe_yield is None:
        return None

    # Handle numeric yield
    if isinstance(recipe_yield, (int, float)):
        return int(recipe_yield)

    if not isinstance(recipe_yield, str):
        return None

    # Extract first number from string (handles "12 servings", "8-10", etc.)
    match = re.search(r"(\d+)", recipe_yield)
    if match:
        return int(match.group(1))

    return None


def _parse_ingredient(ingredient_str: str) -> Ingredient:
    """Parse an ingredient string into structured data.

    Attempts to extract quantity, unit, and name from strings like:
    - "2 cups all-purpose flour"
    - "1/2 teaspoon salt"
    - "3 large eggs"
    - "salt to taste"

    Args:
        ingredient_str: Raw ingredient string.

    Returns:
        Ingredient object with parsed data.
    """
    ingredient_str = ingredient_str.strip()

    # Try to match quantity at the start
    # Patterns: "2", "1/2", "2 1/2", "2.5"
    quantity_pattern = r"^(\d+(?:\s+\d+)?(?:/\d+)?|\d+(?:\.\d+)?)\s*"
    quantity_match = re.match(quantity_pattern, ingredient_str)

    quantity = None
    remaining = ingredient_str

    if quantity_match:
        quantity = quantity_match.group(1).strip()
        remaining = ingredient_str[quantity_match.end():].strip()

    # Try to match unit
    unit = None
    unit_pattern = r"^(" + "|".join(UNITS) + r")\b\.?\s*"
    unit_match = re.match(unit_pattern, remaining, re.IGNORECASE)

    if unit_match:
        unit = unit_match.group(1).lower()
        remaining = remaining[unit_match.end():].strip()

    # Handle parenthetical metric equivalents like "(310g)"
    remaining = re.sub(r"\(\d+g?\)", "", remaining).strip()

    # Clean up the name
    name = remaining.strip(" ,")

    # If no quantity was found, use the full string as the name
    if not quantity and not unit:
        name = ingredient_str

    return Ingredient(
        name=name if name else ingredient_str,
        quantity=quantity,
        unit=unit,
        notes=None,
    )


def _parse_instructions(raw_instructions: Any) -> List[Instruction]:
    """Parse instructions from various schema.org formats.

    Handles:
    - List of HowToStep objects
    - List of strings
    - Single string
    - HowToSection with nested steps

    Args:
        raw_instructions: recipeInstructions value.

    Returns:
        List of Instruction objects with step numbers.
    """
    if not raw_instructions:
        return []

    # Handle single string instruction
    if isinstance(raw_instructions, str):
        return [Instruction(step_number=1, text=raw_instructions)]

    if not isinstance(raw_instructions, list):
        return []

    instructions: List[Instruction] = []
    step_number = 1

    for item in raw_instructions:
        if isinstance(item, str):
            # Plain string instruction
            instructions.append(Instruction(step_number=step_number, text=item))
            step_number += 1

        elif isinstance(item, dict):
            item_type = item.get("@type", "")

            if item_type == "HowToStep":
                text = item.get("text", "")
                if text:
                    instructions.append(Instruction(step_number=step_number, text=text))
                    step_number += 1

            elif item_type == "HowToSection":
                # Extract steps from nested itemListElement
                nested_steps = item.get("itemListElement", [])
                for nested in nested_steps:
                    if isinstance(nested, dict) and nested.get("@type") == "HowToStep":
                        text = nested.get("text", "")
                        if text:
                            instructions.append(
                                Instruction(step_number=step_number, text=text)
                            )
                            step_number += 1

            else:
                # Try to get text from unknown dict format
                text = item.get("text", "")
                if text:
                    instructions.append(Instruction(step_number=step_number, text=text))
                    step_number += 1

    return instructions
