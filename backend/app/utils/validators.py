"""
Input validation utilities for FormFlow.
"""
import re
import logging
from typing import Dict, Any, List, Optional
import bleach

logger = logging.getLogger(__name__)

# Valid component types
VALID_COMPONENT_TYPES = {"multiple-choice", "short-answer"}

# Maximum lengths
MAX_QUERY_LENGTH = 5000
MAX_TITLE_LENGTH = 200
MAX_DESCRIPTION_LENGTH = 1000
MAX_QUESTION_LENGTH = 500
MAX_OPTION_LENGTH = 200
MAX_ANSWER_LENGTH = 2000

# File validation
ALLOWED_FILE_EXTENSIONS = {"pdf", "txt"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
MAX_FILES_PER_REQUEST = 5


def sanitize_user_input(text: str, max_length: int = MAX_QUERY_LENGTH) -> str:
    """
    Sanitize user input text.

    Args:
        text: Raw user input
        max_length: Maximum allowed length

    Returns:
        Sanitized text
    """
    if not text:
        return ""

    # Remove HTML tags
    clean_text = bleach.clean(text, tags=[], strip=True)

    # Normalize whitespace
    clean_text = re.sub(r"\s+", " ", clean_text)

    # Trim to max length
    if len(clean_text) > max_length:
        clean_text = clean_text[:max_length]

    return clean_text.strip()


def validate_schema(schema: Dict[str, Any]) -> tuple[bool, Optional[str]]:
    """
    Validate a form schema.

    Args:
        schema: Form schema to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not isinstance(schema, dict):
        return False, "Schema must be an object"

    # Validate title
    title = schema.get("title", "")
    if title and len(title) > MAX_TITLE_LENGTH:
        return False, f"Title exceeds maximum length of {MAX_TITLE_LENGTH}"

    # Validate description
    description = schema.get("description", "")
    if description and len(description) > MAX_DESCRIPTION_LENGTH:
        return False, f"Description exceeds maximum length of {MAX_DESCRIPTION_LENGTH}"

    # Validate components
    components = schema.get("components", [])
    if not isinstance(components, list):
        return False, "Components must be an array"

    component_ids = set()

    for i, component in enumerate(components):
        is_valid, error = _validate_component(component, i)
        if not is_valid:
            return False, error

        # Check for duplicate IDs
        comp_id = component.get("id")
        if comp_id in component_ids:
            return False, f"Duplicate component ID: {comp_id}"
        component_ids.add(comp_id)

    return True, None


def _validate_component(component: Dict[str, Any], index: int) -> tuple[bool, Optional[str]]:
    """
    Validate a single form component.

    Args:
        component: Component to validate
        index: Component index (for error messages)

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not isinstance(component, dict):
        return False, f"Component {index} must be an object"

    # Validate ID
    comp_id = component.get("id")
    if not comp_id or not isinstance(comp_id, str):
        return False, f"Component {index} missing valid ID"

    # Validate type
    comp_type = component.get("type")
    if comp_type not in VALID_COMPONENT_TYPES:
        return False, f"Component {index} has invalid type: {comp_type}"

    # Validate data
    data = component.get("data")
    if not isinstance(data, dict):
        return False, f"Component {index} missing valid data"

    # Validate question
    question = data.get("question")
    if not question or not isinstance(question, str):
        return False, f"Component {index} missing question"
    if len(question) > MAX_QUESTION_LENGTH:
        return False, f"Component {index} question exceeds maximum length"

    # Type-specific validation
    if comp_type == "multiple-choice":
        options = data.get("options")
        if not isinstance(options, list) or len(options) < 2:
            return False, f"Component {index} must have at least 2 options"
        if len(options) > 4:
            return False, f"Component {index} cannot have more than 4 options"
        for opt in options:
            if not isinstance(opt, str) or len(opt) > MAX_OPTION_LENGTH:
                return False, f"Component {index} has invalid option"

    return True, None


def validate_answers(
    answers: Dict[str, Any],
    schema: Dict[str, Any]
) -> tuple[bool, Optional[str]]:
    """
    Validate form answers against schema.

    Args:
        answers: Submitted answers
        schema: Form schema

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not isinstance(answers, dict):
        return False, "Answers must be an object"

    components = {c["id"]: c for c in schema.get("components", [])}

    # Check required fields
    for comp_id, component in components.items():
        data = component.get("data", {})
        is_required = data.get("required", False)

        if is_required and comp_id not in answers:
            return False, f"Missing required answer for component {comp_id}"

    # Validate each answer
    for comp_id, answer in answers.items():
        if comp_id not in components:
            # Allow extra answers (could be from previous schema version)
            logger.warning(f"Answer for unknown component: {comp_id}")
            continue

        component = components[comp_id]
        is_valid, error = _validate_answer(answer, component)
        if not is_valid:
            return False, error

    return True, None


def _validate_answer(answer: Any, component: Dict[str, Any]) -> tuple[bool, Optional[str]]:
    """
    Validate a single answer against its component.

    Args:
        answer: The submitted answer
        component: The component definition

    Returns:
        Tuple of (is_valid, error_message)
    """
    comp_id = component.get("id")
    comp_type = component.get("type")
    data = component.get("data", {})

    if comp_type == "multiple-choice":
        options = data.get("options", [])

        # Can be a string (single selection) or list (multiple selection)
        if isinstance(answer, str):
            if answer not in options:
                return False, f"Invalid option for {comp_id}: {answer}"
        elif isinstance(answer, list):
            for ans in answer:
                if ans not in options:
                    return False, f"Invalid option for {comp_id}: {ans}"
        else:
            return False, f"Invalid answer type for {comp_id}"

    elif comp_type == "short-answer":
        if not isinstance(answer, str):
            return False, f"Answer for {comp_id} must be a string"
        if len(answer) > MAX_ANSWER_LENGTH:
            return False, f"Answer for {comp_id} exceeds maximum length"

    return True, None


def validate_file_upload(file_info: Dict[str, Any]) -> tuple[bool, Optional[str]]:
    """
    Validate a file upload.

    Args:
        file_info: File information dictionary

    Returns:
        Tuple of (is_valid, error_message)
    """
    name = file_info.get("name", "")
    file_type = file_info.get("type", "")
    content = file_info.get("content", "")

    # Validate name
    if not name:
        return False, "File name is required"

    # Extract extension
    if "." in name:
        ext = name.rsplit(".", 1)[1].lower()
        if ext not in ALLOWED_FILE_EXTENSIONS:
            return False, f"File type not allowed: {ext}"

    # Validate type
    if file_type not in {"text", "pdf"}:
        return False, f"Invalid file type: {file_type}"

    # Validate content
    if not content:
        return False, "File content is required"

    # Check approximate size (base64 is ~4/3 larger than original)
    approx_size = len(content) * 3 / 4
    if approx_size > MAX_FILE_SIZE:
        return False, f"File too large (max {MAX_FILE_SIZE / 1024 / 1024}MB)"

    return True, None


def validate_documents(documents: List[Dict[str, Any]]) -> tuple[bool, Optional[str]]:
    """
    Validate a list of document uploads.

    Args:
        documents: List of document dictionaries

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not isinstance(documents, list):
        return False, "Documents must be an array"

    if len(documents) > MAX_FILES_PER_REQUEST:
        return False, f"Maximum {MAX_FILES_PER_REQUEST} files allowed per request"

    for i, doc in enumerate(documents):
        is_valid, error = validate_file_upload(doc)
        if not is_valid:
            return False, f"Document {i + 1}: {error}"

    return True, None
