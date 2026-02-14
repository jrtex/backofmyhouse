"""Shared prompts and schemas for AI-based recipe extraction."""

EXTRACTION_SYSTEM_PROMPT = """You are a recipe extraction assistant. Your task is to extract structured recipe data from the provided content (image or text).

Extract the following information:
- title: The name of the recipe (required)
- description: A brief description of the dish
- ingredients: List of ingredients with name, quantity, unit, and notes
- instructions: Numbered steps for preparing the recipe
- prep_time_minutes: Preparation time in minutes
- cook_time_minutes: Cooking time in minutes
- servings: Number of servings the recipe makes
- notes: Any additional tips or notes
- special_equipment: Any special tools or equipment needed (e.g., "stand mixer", "instant pot")

Guidelines:
1. Extract only information that is explicitly present or clearly implied
2. For ingredients, separate the quantity (e.g., "2"), unit (e.g., "cups"), and name (e.g., "flour")
3. Include ingredient notes for preparation details like "chopped", "melted", or "at room temperature"
4. Number instructions sequentially starting from 1
5. Convert time values to minutes (e.g., "1 hour" = 60 minutes)
6. If servings are given as a range, use the lower number
7. Only include special_equipment for items beyond basic kitchen tools

Confidence scoring:
- 1.0: All fields clearly visible/stated, no ambiguity
- 0.8-0.9: Most fields clear, minor inference needed
- 0.6-0.7: Some fields missing or unclear, moderate inference
- 0.4-0.5: Significant portions unclear or missing
- Below 0.4: Very incomplete or unclear source

Add warnings for:
- Missing required information (title, ingredients, or instructions)
- Unclear or potentially incorrect values
- Content that may be partial or cut off
- Low image quality affecting readability"""

EXTRACTION_JSON_SCHEMA = {
    "type": "object",
    "required": ["title", "ingredients", "instructions", "confidence", "warnings"],
    "properties": {
        "title": {
            "type": "string",
            "description": "The name of the recipe",
            "minLength": 1,
            "maxLength": 255,
        },
        "description": {
            "type": "string",
            "description": "A brief description of the dish",
        },
        "ingredients": {
            "type": "array",
            "description": "List of ingredients",
            "items": {
                "type": "object",
                "required": ["name"],
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Ingredient name",
                    },
                    "quantity": {
                        "type": "string",
                        "description": "Amount (e.g., '2', '1/2', '2-3')",
                    },
                    "unit": {
                        "type": "string",
                        "description": "Unit of measurement (e.g., 'cups', 'tablespoons', 'pounds')",
                    },
                    "notes": {
                        "type": "string",
                        "description": "Preparation notes (e.g., 'chopped', 'melted')",
                    },
                },
            },
        },
        "instructions": {
            "type": "array",
            "description": "Ordered list of cooking steps",
            "items": {
                "type": "object",
                "required": ["step_number", "text"],
                "properties": {
                    "step_number": {
                        "type": "integer",
                        "description": "Step number (1-based)",
                        "minimum": 1,
                    },
                    "text": {
                        "type": "string",
                        "description": "The instruction text",
                    },
                },
            },
        },
        "prep_time_minutes": {
            "type": "integer",
            "description": "Preparation time in minutes",
            "minimum": 0,
        },
        "cook_time_minutes": {
            "type": "integer",
            "description": "Cooking time in minutes",
            "minimum": 0,
        },
        "servings": {
            "type": "integer",
            "description": "Number of servings",
            "minimum": 1,
        },
        "notes": {
            "type": "string",
            "description": "Additional tips or notes",
        },
        "special_equipment": {
            "type": "array",
            "description": "Special equipment needed",
            "items": {"type": "string"},
        },
        "confidence": {
            "type": "number",
            "description": "Extraction confidence score (0-1)",
            "minimum": 0,
            "maximum": 1,
        },
        "warnings": {
            "type": "array",
            "description": "Any issues or warnings during extraction",
            "items": {"type": "string"},
        },
    },
}

# User prompt for image extraction
IMAGE_USER_PROMPT = "Extract the recipe information from this image. Return the data as JSON matching the specified schema."

# User prompt for text extraction
TEXT_USER_PROMPT_TEMPLATE = """Extract the recipe information from the following text. Return the data as JSON matching the specified schema.

Text content:
{text}"""

# User prompt for PDF extraction
PDF_USER_PROMPT = "Extract the recipe information from this PDF document. Process all pages if there are multiple. Return the data as JSON matching the specified schema."
