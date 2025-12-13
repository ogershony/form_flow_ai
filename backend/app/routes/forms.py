"""
Form management routes for FormFlow.
"""
import logging
from flask import Blueprint, request, g

from app import limiter
from app.services.firebase_service import (
    get_form,
    create_form as db_create_form,
    update_form as db_update_form,
    undo_form as db_undo_form,
    get_user_forms,
    add_form_response,
    get_form_responses,
)
from app.services.mcp_service import get_mcp_service
from app.services.document_service import get_document_service
from app.utils.decorators import require_auth, require_form_owner
from app.utils.validators import (
    sanitize_user_input,
    validate_schema,
    validate_answers,
    validate_documents,
)

logger = logging.getLogger(__name__)

forms_bp = Blueprint("forms", __name__)


@forms_bp.route("/create", methods=["POST"])
@require_auth
@limiter.limit("10 per hour")
def create_form():
    """
    Create a new form from natural language and/or documents.

    Request Body:
        userQuery: Natural language description
        documents: Optional array of documents

    Returns:
        formId and redirectUrl
    """
    data = request.get_json()

    if not data:
        return {"error": "Request body required"}, 400

    user_query = data.get("userQuery", "")
    documents = data.get("documents", [])

    # Validate inputs
    if not user_query and not documents:
        return {"error": "Either userQuery or documents required"}, 400

    user_query = sanitize_user_input(user_query)

    # Validate documents if provided
    if documents:
        is_valid, error = validate_documents(documents)
        if not is_valid:
            return {"error": error}, 400

    try:
        # Process documents
        doc_service = get_document_service()
        document_text = doc_service.process_documents(documents)

        # Combine context
        context_parts = []
        if user_query:
            context_parts.append(f"User Request: {user_query}")
        if document_text:
            context_parts.append(f"Document Content:\n{document_text}")

        context = "\n\n".join(context_parts)

        # Generate form using AI
        mcp_service = get_mcp_service()
        schema_data = mcp_service.create_form(context, g.user_id)

        # Extract schema components
        title = schema_data.get("title", "Untitled Form")
        description = schema_data.get("description", "")
        schema = {"components": schema_data.get("components", [])}

        # Save to database
        form_id = db_create_form(g.user_id, schema, title, description)

        logger.info(f"Created form {form_id} for user {g.user_id}")

        return {
            "formId": form_id,
            "redirectUrl": f"/{form_id}/edit"
        }, 201

    except Exception as e:
        logger.error(f"Form creation failed: {e}")
        return {"error": "Failed to create form", "message": str(e)}, 500


@forms_bp.route("/", methods=["GET"])
@require_auth
def list_forms():
    """
    List all forms owned by the authenticated user.

    Returns:
        Array of form summaries
    """
    try:
        forms = get_user_forms(g.user_id)
        return {"forms": forms}, 200
    except Exception as e:
        logger.error(f"Failed to list forms: {e}")
        return {"error": "Failed to list forms"}, 500


@forms_bp.route("/<form_id>", methods=["GET"])
def get_form_detail(form_id):
    """
    Retrieve form schema (public access).

    Returns:
        Form schema with title, description, and components
    """
    form = get_form(form_id)

    if not form:
        return {"error": "Form not found"}, 404

    return {
        "formId": form_id,
        "title": form.get("title", ""),
        "description": form.get("description", ""),
        "schema": form.get("schema", {"components": []})
    }, 200


@forms_bp.route("/<form_id>/save", methods=["POST"])
@require_auth
@require_form_owner
def save_form(form_id):
    """
    Manually save form schema changes.

    Request Body:
        schema: Updated form schema
        changeDescription: Optional description

    Returns:
        Success status and new version
    """
    data = request.get_json()

    if not data:
        return {"error": "Request body required"}, 400

    schema = data.get("schema")
    change_description = data.get("changeDescription", "Manual save")

    if not schema:
        return {"error": "Schema required"}, 400

    # Validate schema
    is_valid, error = validate_schema(schema)
    if not is_valid:
        return {"error": error}, 400

    try:
        new_version = db_update_form(form_id, schema, change_description)

        return {
            "success": True,
            "version": new_version
        }, 200

    except Exception as e:
        logger.error(f"Failed to save form {form_id}: {e}")
        return {"error": "Failed to save form"}, 500


@forms_bp.route("/<form_id>/edit", methods=["POST"])
@require_auth
@require_form_owner
@limiter.limit("20 per hour")
def edit_form(form_id):
    """
    AI-assisted form editing with natural language.

    Request Body:
        userQuery: Natural language edit instructions
        documents: Optional array of documents

    Returns:
        Success status, updated schema, and version
    """
    data = request.get_json()

    if not data:
        return {"error": "Request body required"}, 400

    user_query = data.get("userQuery", "")
    documents = data.get("documents", [])

    if not user_query and not documents:
        return {"error": "Either userQuery or documents required"}, 400

    user_query = sanitize_user_input(user_query)

    # Validate documents if provided
    if documents:
        is_valid, error = validate_documents(documents)
        if not is_valid:
            return {"error": error}, 400

    try:
        # Get current schema
        current_schema = g.form.get("schema", {"components": []})

        # Process documents
        doc_service = get_document_service()
        document_text = doc_service.process_documents(documents)

        # Combine context
        context_parts = []
        if user_query:
            context_parts.append(f"User Request: {user_query}")
        if document_text:
            context_parts.append(f"Document Content:\n{document_text}")

        context = "\n\n".join(context_parts)

        # Generate updated form using AI
        mcp_service = get_mcp_service()
        schema_data = mcp_service.update_form(
            form_id,
            context,
            current_schema,
            g.user_id
        )

        # Generate change description
        change_description = mcp_service.generate_change_description(
            current_schema,
            schema_data
        )

        # Build new schema
        new_schema = {"components": schema_data.get("components", [])}

        # Update in database
        new_version = db_update_form(form_id, new_schema, change_description)

        logger.info(f"Updated form {form_id} to version {new_version}")

        return {
            "success": True,
            "schema": new_schema,
            "title": schema_data.get("title", g.form.get("title", "")),
            "description": schema_data.get("description", g.form.get("description", "")),
            "version": new_version
        }, 200

    except Exception as e:
        logger.error(f"Form edit failed: {e}")
        return {"error": "Failed to edit form", "message": str(e)}, 500


@forms_bp.route("/<form_id>/undo", methods=["POST"])
@require_auth
@require_form_owner
def undo_form_change(form_id):
    """
    Revert to previous form version.

    Returns:
        Success status, previous schema, and version
    """
    try:
        result = db_undo_form(form_id)

        if result is None:
            return {
                "success": False,
                "message": "Already at initial version"
            }, 400

        return {
            "success": True,
            "schema": result["schema"],
            "version": result["version"]
        }, 200

    except Exception as e:
        logger.error(f"Failed to undo form {form_id}: {e}")
        return {"error": "Failed to undo"}, 500


@forms_bp.route("/<form_id>/submit", methods=["POST"])
def submit_response(form_id):
    """
    Submit form response (public access).

    Request Body:
        answers: Object mapping component IDs to answers

    Returns:
        Success status and response ID
    """
    data = request.get_json()

    if not data:
        return {"error": "Request body required"}, 400

    answers = data.get("answers", {})

    if not answers:
        return {"error": "Answers required"}, 400

    # Get form schema for validation
    form = get_form(form_id)
    if not form:
        return {"error": "Form not found"}, 404

    schema = form.get("schema", {"components": []})

    # Validate answers
    is_valid, error = validate_answers(answers, schema)
    if not is_valid:
        return {"error": error}, 400

    try:
        response_id = add_form_response(form_id, answers)

        return {
            "success": True,
            "responseId": response_id
        }, 201

    except Exception as e:
        logger.error(f"Failed to submit response: {e}")
        return {"error": "Failed to submit response"}, 500


@forms_bp.route("/<form_id>/responses", methods=["GET"])
@require_auth
@require_form_owner
def get_responses(form_id):
    """
    Retrieve all responses for a form (owner only).

    Returns:
        Array of responses
    """
    try:
        responses = get_form_responses(form_id)

        return {
            "formId": form_id,
            "responses": responses
        }, 200

    except Exception as e:
        logger.error(f"Failed to get responses: {e}")
        return {"error": "Failed to get responses"}, 500
