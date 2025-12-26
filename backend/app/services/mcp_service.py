"""
MCP Service - Model Context Protocol integration with Claude API for form generation.
"""
import os
import json
import logging
import re
from typing import Dict, Any, Optional
import anthropic

logger = logging.getLogger(__name__)

# Prompt templates
CREATE_FORM_PROMPT = """You are a form builder assistant. Based on the following user requirements, create a form schema.

USER REQUIREMENTS:
{context}

SCHEMA SPECIFICATION:
- Forms consist of components
- Each component has: id (unique string starting with "comp_"), type (multiple-choice | short-answer), data (object)
- Multiple-choice components have: question (string), options (array of up to 4 strings), required (boolean)
- Short-answer components have: question (string), required (boolean)

Generate a form with an appropriate title and description. Return ONLY valid JSON in this exact format, with no additional text or markdown:
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
    }},
    {{
      "id": "comp_2",
      "type": "short-answer",
      "data": {{
        "question": "Question text",
        "required": false
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
- Preserve existing component IDs unless explicitly replacing components
- Generate new unique IDs for new components (format: comp_1, comp_2, etc.)
- Each component has: id (unique string), type (multiple-choice | short-answer), data (object)
- Multiple-choice components have: question (string), options (array of up to 4 strings), required (boolean)
- Short-answer components have: question (string), required (boolean)

Return ONLY the complete updated JSON schema in this exact format, with no additional text or markdown:
{{
  "title": "Form Title",
  "description": "Brief description",
  "components": [...]
}}"""


class MCPService:
    """
    MCP Service for Claude API integration.
    Handles form creation and updates using AI.
    """

    def __init__(self):
        """Initialize the MCP service with Anthropic client."""
        self.api_key = os.environ.get("CLAUDE_API_KEY") or os.environ.get("ANTHROPIC_API_KEY")

        if not self.api_key:
            logger.warning("Claude API key not found in environment")
            self.client = None
        else:
            self.client = anthropic.Anthropic(api_key=self.api_key)
            logger.info("MCP Service initialized with Claude API")

    def _call_claude(self, prompt: str, max_tokens: int = 4096) -> str:
        """
        Call Claude API with a prompt.

        Args:
            prompt: The prompt to send
            max_tokens: Maximum tokens in response

        Returns:
            Claude's response text
        """
        if not self.client:
            raise RuntimeError("Claude API client not initialized. Check API key.")

        try:
            message = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=max_tokens,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            response_text = message.content[0].text
            logger.debug(f"Claude response: {response_text[:200]}...")
            return response_text

        except anthropic.APIConnectionError as e:
            logger.error(f"Claude API connection error: {e}")
            raise RuntimeError(f"Failed to connect to Claude API: {e}")
        except anthropic.RateLimitError as e:
            logger.error(f"Claude API rate limit: {e}")
            raise RuntimeError("Claude API rate limit exceeded. Please try again later.")
        except anthropic.APIError as e:
            logger.error(f"Claude API error: {e}")
            raise RuntimeError(f"Claude API error: {e}")

    def _parse_json_response(self, response: str) -> Dict[str, Any]:
        """
        Parse JSON from Claude's response.

        Args:
            response: Raw response text

        Returns:
            Parsed JSON object
        """
        # Try to extract JSON from response
        # Sometimes Claude wraps JSON in markdown code blocks
        json_match = re.search(r'```(?:json)?\s*([\s\S]*?)```', response)
        if json_match:
            json_str = json_match.group(1).strip()
        else:
            # Try to find JSON object directly
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                json_str = json_match.group(0)
            else:
                json_str = response.strip()

        try:
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON: {e}\nResponse: {response}")
            raise ValueError(f"Failed to parse AI response as JSON: {e}")

    def _validate_schema(self, schema: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate and normalize a form schema.

        Args:
            schema: Schema to validate

        Returns:
            Validated schema
        """
        # Ensure required fields exist
        if "components" not in schema:
            schema["components"] = []

        if "title" not in schema:
            schema["title"] = "Untitled Form"

        if "description" not in schema:
            schema["description"] = ""

        # Validate each component
        valid_types = {"multiple-choice", "short-answer"}
        validated_components = []

        for i, component in enumerate(schema.get("components", [])):
            # Ensure component has required fields
            if "id" not in component:
                component["id"] = f"comp_{i + 1}"

            if "type" not in component or component["type"] not in valid_types:
                logger.warning(f"Invalid component type: {component.get('type')}")
                continue

            if "data" not in component:
                component["data"] = {}

            # Validate component data based on type
            if component["type"] == "multiple-choice":
                data = component["data"]
                if "question" not in data:
                    data["question"] = "Question"
                if "options" not in data or not isinstance(data["options"], list):
                    data["options"] = ["Option 1", "Option 2"]
                if "required" not in data:
                    data["required"] = False
                # Ensure options is limited to 4
                data["options"] = data["options"][:4]

            elif component["type"] == "short-answer":
                data = component["data"]
                if "question" not in data:
                    data["question"] = "Question"
                if "required" not in data:
                    data["required"] = False

            validated_components.append(component)

        schema["components"] = validated_components
        return schema

    def create_form(self, context: str, user_id: str) -> Dict[str, Any]:
        """
        Create a new form schema based on user context.

        Args:
            context: Combined user query and document text
            user_id: Firebase user ID

        Returns:
            Form schema with title, description, and components
        """
        logger.info(f"Creating form for user {user_id} with context length: {len(context)}")

        prompt = CREATE_FORM_PROMPT.format(context=context)

        try:
            response = self._call_claude(prompt)
            schema = self._parse_json_response(response)
            validated_schema = self._validate_schema(schema)

            logger.info(f"Created form with {len(validated_schema.get('components', []))} components")
            return validated_schema

        except Exception as e:
            logger.error(f"Form creation failed: {e}")
            # Return a basic fallback schema
            return self._create_fallback_schema(context)

    def update_form(
        self,
        form_id: str,
        context: str,
        current_schema: Dict[str, Any],
        user_id: str
    ) -> Dict[str, Any]:
        """
        Update an existing form schema based on user context.

        Args:
            form_id: Form document ID
            context: Update request and document text
            current_schema: Current form schema
            user_id: Firebase user ID

        Returns:
            Updated form schema
        """
        logger.info(f"Updating form {form_id} for user {user_id}")

        prompt = UPDATE_FORM_PROMPT.format(
            context=context,
            current_schema=json.dumps(current_schema, indent=2)
        )

        try:
            response = self._call_claude(prompt)
            schema = self._parse_json_response(response)
            validated_schema = self._validate_schema(schema)

            logger.info(f"Updated form with {len(validated_schema.get('components', []))} components")
            return validated_schema

        except Exception as e:
            logger.error(f"Form update failed: {e}")
            raise RuntimeError(f"Failed to update form: {e}")

    def _create_fallback_schema(self, context: str) -> Dict[str, Any]:
        """
        Create a basic fallback schema when AI fails.

        Args:
            context: Original user context

        Returns:
            Basic form schema
        """
        logger.warning("Using fallback schema due to AI failure")

        return {
            "title": "New Form",
            "description": "Form created from: " + context[:100] + "..." if len(context) > 100 else context,
            "components": [
                {
                    "id": "comp_1",
                    "type": "short-answer",
                    "data": {
                        "question": "Please describe your request",
                        "required": True
                    }
                }
            ]
        }

    def generate_change_description(
        self,
        old_schema: Dict[str, Any],
        new_schema: Dict[str, Any]
    ) -> str:
        """
        Generate a description of changes between schemas.

        Args:
            old_schema: Previous schema
            new_schema: New schema

        Returns:
            Human-readable change description
        """
        old_components = {c["id"]: c for c in old_schema.get("components", [])}
        new_components = {c["id"]: c for c in new_schema.get("components", [])}

        added = set(new_components.keys()) - set(old_components.keys())
        removed = set(old_components.keys()) - set(new_components.keys())
        modified = set()

        for comp_id in set(old_components.keys()) & set(new_components.keys()):
            if old_components[comp_id] != new_components[comp_id]:
                modified.add(comp_id)

        changes = []
        if added:
            changes.append(f"Added {len(added)} component(s)")
        if removed:
            changes.append(f"Removed {len(removed)} component(s)")
        if modified:
            changes.append(f"Modified {len(modified)} component(s)")

        if old_schema.get("title") != new_schema.get("title"):
            changes.append("Updated title")

        if old_schema.get("description") != new_schema.get("description"):
            changes.append("Updated description")

        return "; ".join(changes) if changes else "No changes detected"

    def generate_detailed_diff(
        self,
        old_schema: Dict[str, Any],
        new_schema: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate detailed structured diff between schemas.

        Args:
            old_schema: Previous schema
            new_schema: New schema

        Returns:
            Structured diff with detailed change information
        """
        old_components = {c["id"]: c for c in old_schema.get("components", [])}
        new_components = {c["id"]: c for c in new_schema.get("components", [])}

        changes = []

        # Track added components
        added_ids = set(new_components.keys()) - set(old_components.keys())
        for comp_id in added_ids:
            component = new_components[comp_id]
            question = component.get("data", {}).get("question", "")
            comp_type = component.get("type", "")
            type_name = "multiple choice" if comp_type == "multiple-choice" else "short answer"

            changes.append({
                "type": "added",
                "componentId": comp_id,
                "component": component,
                "details": f"Added {type_name} question: '{question}'"
            })

        # Track removed components
        removed_ids = set(old_components.keys()) - set(new_components.keys())
        for comp_id in removed_ids:
            component = old_components[comp_id]
            question = component.get("data", {}).get("question", "")
            comp_type = component.get("type", "")
            type_name = "multiple choice" if comp_type == "multiple-choice" else "short answer"

            changes.append({
                "type": "removed",
                "componentId": comp_id,
                "component": component,
                "details": f"Removed {type_name} question: '{question}'"
            })

        # Track modified components
        common_ids = set(old_components.keys()) & set(new_components.keys())
        for comp_id in common_ids:
            old_comp = old_components[comp_id]
            new_comp = new_components[comp_id]

            if old_comp != new_comp:
                details_parts = self._compare_components(old_comp, new_comp)
                if details_parts:
                    changes.append({
                        "type": "modified",
                        "componentId": comp_id,
                        "before": old_comp,
                        "after": new_comp,
                        "details": "; ".join(details_parts)
                    })

        # Track metadata changes
        if old_schema.get("title") != new_schema.get("title"):
            changes.append({
                "type": "metadata",
                "field": "title",
                "before": old_schema.get("title", ""),
                "after": new_schema.get("title", ""),
                "details": f"Changed form title from '{old_schema.get('title', '')}' to '{new_schema.get('title', '')}'"
            })

        if old_schema.get("description") != new_schema.get("description"):
            changes.append({
                "type": "metadata",
                "field": "description",
                "before": old_schema.get("description", ""),
                "after": new_schema.get("description", ""),
                "details": f"Changed form description"
            })

        # Generate summary using existing method
        summary = self.generate_change_description(old_schema, new_schema)

        return {
            "summary": summary,
            "changes": changes
        }

    def _compare_components(
        self,
        old_comp: Dict[str, Any],
        new_comp: Dict[str, Any]
    ) -> list:
        """
        Compare two components and return list of changes.

        Args:
            old_comp: Old component
            new_comp: New component

        Returns:
            List of change descriptions
        """
        changes = []
        old_data = old_comp.get("data", {})
        new_data = new_comp.get("data", {})

        # Check type change (rare but possible)
        if old_comp.get("type") != new_comp.get("type"):
            old_type = "multiple choice" if old_comp.get("type") == "multiple-choice" else "short answer"
            new_type = "multiple choice" if new_comp.get("type") == "multiple-choice" else "short answer"
            changes.append(f"Changed type from {old_type} to {new_type}")

        # Check question text change
        old_question = old_data.get("question", "")
        new_question = new_data.get("question", "")
        if old_question != new_question:
            changes.append(f"Changed question text")

        # Check required status
        old_required = old_data.get("required", False)
        new_required = new_data.get("required", False)
        if old_required != new_required:
            status = "required" if new_required else "optional"
            changes.append(f"Made {status}")

        # Multiple choice specific changes
        if new_comp.get("type") == "multiple-choice":
            old_opts = set(old_data.get("options", []))
            new_opts = set(new_data.get("options", []))

            added_opts = new_opts - old_opts
            removed_opts = old_opts - new_opts

            if added_opts:
                opts_str = "', '".join(added_opts)
                changes.append(f"Added option(s): '{opts_str}'")
            if removed_opts:
                opts_str = "', '".join(removed_opts)
                changes.append(f"Removed option(s): '{opts_str}'")

        # Short answer specific changes
        if new_comp.get("type") == "short-answer":
            old_max_length = old_data.get("maxLength")
            new_max_length = new_data.get("maxLength")
            if old_max_length != new_max_length:
                if new_max_length:
                    changes.append(f"Set maximum length to {new_max_length}")
                else:
                    changes.append("Removed maximum length limit")

        return changes


# Singleton instance
_mcp_service = None


def get_mcp_service() -> MCPService:
    """Get or create the MCP service singleton."""
    global _mcp_service
    if _mcp_service is None:
        _mcp_service = MCPService()
    return _mcp_service
