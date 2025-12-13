"""
MCP Server Entry Point for FormFlow.
This module provides MCP tools for form generation and updates using Claude API.
"""
import os
import json
import logging
from typing import Dict, Any
from dotenv import load_dotenv

load_dotenv()

import anthropic

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Anthropic client
api_key = os.environ.get("CLAUDE_API_KEY") or os.environ.get("ANTHROPIC_API_KEY")
client = anthropic.Anthropic(api_key=api_key) if api_key else None

# Prompt templates
CREATE_FORM_PROMPT = """You are a form builder assistant. Based on the following user requirements, create a form schema.

USER REQUIREMENTS:
{context}

SCHEMA SPECIFICATION:
- Forms consist of components
- Each component has: id (unique string starting with "comp_"), type (multiple-choice | short-answer), data (object)
- Multiple-choice components have: question (string), options (array of up to 4 strings), required (boolean)
- Short-answer components have: question (string), required (boolean)

Generate a form with an appropriate title and description. Return ONLY valid JSON in this exact format:
{{
  "title": "Form Title",
  "description": "Brief description",
  "components": [
    {{
      "id": "comp_1",
      "type": "multiple-choice",
      "data": {{
        "question": "Question text",
        "options": ["Option 1", "Option 2", "Option 3", "Option 4"],
        "required": true
      }}
    }}
  ]
}}"""

UPDATE_FORM_PROMPT = """You are a form builder assistant. Update the existing form schema based on user requirements.

USER UPDATE REQUEST:
{context}

CURRENT FORM SCHEMA:
{current_schema}

RULES:
- Preserve existing component IDs unless explicitly replacing
- Generate new unique IDs for new components
- Return the complete updated schema

Return ONLY valid JSON in the same format as the current schema."""


def create_form(context: str, user_id: str) -> Dict[str, Any]:
    """
    Create a new form schema using Claude API.

    Args:
        context: User requirements and document text
        user_id: Firebase user ID

    Returns:
        Form schema with title, description, and components
    """
    if not client:
        raise RuntimeError("Claude API client not initialized")

    prompt = CREATE_FORM_PROMPT.format(context=context)

    try:
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            messages=[{"role": "user", "content": prompt}]
        )

        response_text = message.content[0].text
        schema = _parse_json(response_text)

        logger.info(f"Created form for user {user_id}")
        return schema

    except Exception as e:
        logger.error(f"Form creation failed: {e}")
        raise


def update_form(
    form_id: str,
    context: str,
    current_schema: Dict[str, Any],
    user_id: str
) -> Dict[str, Any]:
    """
    Update an existing form schema using Claude API.

    Args:
        form_id: Form document ID
        context: Update request and document text
        current_schema: Current form schema
        user_id: Firebase user ID

    Returns:
        Updated form schema
    """
    if not client:
        raise RuntimeError("Claude API client not initialized")

    prompt = UPDATE_FORM_PROMPT.format(
        context=context,
        current_schema=json.dumps(current_schema, indent=2)
    )

    try:
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            messages=[{"role": "user", "content": prompt}]
        )

        response_text = message.content[0].text
        schema = _parse_json(response_text)

        logger.info(f"Updated form {form_id} for user {user_id}")
        return schema

    except Exception as e:
        logger.error(f"Form update failed: {e}")
        raise


def _parse_json(response: str) -> Dict[str, Any]:
    """Parse JSON from Claude's response."""
    import re

    # Try to extract JSON from markdown code blocks
    json_match = re.search(r'```(?:json)?\s*([\s\S]*?)```', response)
    if json_match:
        json_str = json_match.group(1).strip()
    else:
        json_match = re.search(r'\{[\s\S]*\}', response)
        if json_match:
            json_str = json_match.group(0)
        else:
            json_str = response.strip()

    return json.loads(json_str)


if __name__ == "__main__":
    # Test the MCP server
    test_context = "Create a customer feedback form with questions about satisfaction and suggestions"
    result = create_form(test_context, "test_user")
    print(json.dumps(result, indent=2))
