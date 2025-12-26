"""
Firebase Service - Handles Firebase Admin SDK operations for Auth and Firestore.
"""
import os
import logging
from datetime import datetime
from typing import Optional, Dict, List, Any
import firebase_admin
from firebase_admin import credentials, auth, firestore

logger = logging.getLogger(__name__)

# Global Firestore client
db = None


def init_firebase():
    """Initialize Firebase Admin SDK."""
    global db

    if firebase_admin._apps:
        logger.info("Firebase already initialized")
        db = firestore.client()
        return

    try:
        # Try to load credentials from environment or file
        cred_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
        firebase_config = os.environ.get("FIREBASE_SERVICE_ACCOUNT")

        if firebase_config:
            import json
            cred_dict = json.loads(firebase_config)
            cred = credentials.Certificate(cred_dict)
        elif cred_path and os.path.exists(cred_path):
            cred = credentials.Certificate(cred_path)
        else:
            # Use application default credentials (for App Engine)
            cred = credentials.ApplicationDefault()

        firebase_admin.initialize_app(cred)
        db = firestore.client()
        logger.info("Firebase initialized successfully")

    except Exception as e:
        logger.error(f"Failed to initialize Firebase: {e}")
        raise


def verify_token(id_token: str) -> Optional[Dict[str, Any]]:
    """
    Verify a Firebase ID token and return the decoded claims.

    Args:
        id_token: The Firebase ID token to verify

    Returns:
        Decoded token claims or None if invalid
    """
    try:
        decoded_token = auth.verify_id_token(id_token)
        return decoded_token
    except auth.InvalidIdTokenError as e:
        logger.warning(f"Invalid ID token: {e}")
        return None
    except auth.ExpiredIdTokenError as e:
        logger.warning(f"Expired ID token: {e}")
        return None
    except Exception as e:
        logger.error(f"Token verification error: {e}")
        return None


def get_user(user_id: str) -> Optional[Dict[str, Any]]:
    """
    Get user document from Firestore.

    Args:
        user_id: Firebase user ID

    Returns:
        User data or None if not found
    """
    try:
        doc = db.collection("users").document(user_id).get()
        if doc.exists:
            data = doc.to_dict()
            data["userId"] = doc.id
            return data
        return None
    except Exception as e:
        logger.error(f"Error getting user {user_id}: {e}")
        return None


def create_user(user_id: str, email: str, display_name: str = "") -> Dict[str, Any]:
    """
    Create a new user document in Firestore.

    Args:
        user_id: Firebase user ID
        email: User email
        display_name: User display name

    Returns:
        Created user data
    """
    user_data = {
        "email": email,
        "displayName": display_name or email.split("@")[0],
        "createdAt": firestore.SERVER_TIMESTAMP,
        "forms": []
    }

    try:
        db.collection("users").document(user_id).set(user_data)
        user_data["userId"] = user_id
        logger.info(f"Created user: {user_id}")
        return user_data
    except Exception as e:
        logger.error(f"Error creating user {user_id}: {e}")
        raise


def get_form(form_id: str) -> Optional[Dict[str, Any]]:
    """
    Get form document from Firestore.

    Args:
        form_id: Form document ID

    Returns:
        Form data with current schema or None if not found
    """
    try:
        doc = db.collection("forms").document(form_id).get()
        if doc.exists:
            data = doc.to_dict()
            data["formId"] = doc.id

            # Return the current version's schema
            current_version = data.get("currentVersion", 0)
            states = data.get("states", [])

            if states and current_version < len(states):
                data["schema"] = states[current_version]["schema"]
            else:
                data["schema"] = {"components": []}

            return data
        return None
    except Exception as e:
        logger.error(f"Error getting form {form_id}: {e}")
        return None


def create_form(
    user_id: str,
    schema: Dict[str, Any],
    title: str = "",
    description: str = ""
) -> str:
    """
    Create a new form document in Firestore.

    Args:
        user_id: Owner's user ID
        schema: Form schema with components
        title: Form title
        description: Form description

    Returns:
        Created form ID
    """
    now = datetime.utcnow()

    form_data = {
        "userId": user_id,
        "title": title,
        "description": description,
        "createdAt": now,
        "updatedAt": now,
        "currentVersion": 0,
        "states": [
            {
                "version": 0,
                "schema": schema,
                "timestamp": now,
                "changeDescription": "Initial form creation"
            }
        ],
        "responses": []
    }

    try:
        # Create form document
        doc_ref = db.collection("forms").document()
        doc_ref.set(form_data)
        form_id = doc_ref.id

        # Add form ID to user's forms list
        user_ref = db.collection("users").document(user_id)
        user_ref.update({
            "forms": firestore.ArrayUnion([form_id])
        })

        logger.info(f"Created form: {form_id} for user: {user_id}")
        return form_id

    except Exception as e:
        logger.error(f"Error creating form: {e}")
        raise


def update_form(
    form_id: str,
    schema: Dict[str, Any],
    change_description: str = "",
    title: Optional[str] = None,
    description: Optional[str] = None,
    detailed_diff: Optional[Dict[str, Any]] = None
) -> int:
    """
    Update form with a new schema version and optionally update metadata.

    Args:
        form_id: Form document ID
        schema: New schema
        change_description: Description of changes
        title: Optional new title
        description: Optional new description
        detailed_diff: Optional structured diff data

    Returns:
        New version number
    """
    try:
        form_ref = db.collection("forms").document(form_id)
        form_doc = form_ref.get()

        if not form_doc.exists:
            raise ValueError(f"Form {form_id} not found")

        form_data = form_doc.to_dict()
        current_version = form_data.get("currentVersion", 0)
        new_version = current_version + 1

        now = datetime.utcnow()

        new_state = {
            "version": new_version,
            "schema": schema,
            "timestamp": now,
            "changeDescription": change_description
        }

        # Add detailed diff if provided
        if detailed_diff is not None:
            new_state["detailedDiff"] = detailed_diff

        update_data = {
            "currentVersion": new_version,
            "updatedAt": now,
            "states": firestore.ArrayUnion([new_state])
        }

        # Update title and description if provided
        if title is not None:
            update_data["title"] = title
        if description is not None:
            update_data["description"] = description

        form_ref.update(update_data)

        logger.info(f"Updated form {form_id} to version {new_version}")
        return new_version

    except Exception as e:
        logger.error(f"Error updating form {form_id}: {e}")
        raise


def undo_form(form_id: str) -> Optional[Dict[str, Any]]:
    """
    Revert form to previous version.

    Args:
        form_id: Form document ID

    Returns:
        Previous schema or None if at version 0
    """
    try:
        form_ref = db.collection("forms").document(form_id)
        form_doc = form_ref.get()

        if not form_doc.exists:
            raise ValueError(f"Form {form_id} not found")

        form_data = form_doc.to_dict()
        current_version = form_data.get("currentVersion", 0)

        if current_version <= 0:
            logger.info(f"Form {form_id} already at version 0, cannot undo")
            return None

        states = form_data.get("states", [])
        new_version = current_version - 1

        # Remove the last state and update current version
        form_ref.update({
            "currentVersion": new_version,
            "updatedAt": datetime.utcnow(),
            "states": states[:-1]  # Remove last state
        })

        previous_schema = states[new_version]["schema"] if new_version < len(states) else {"components": []}

        logger.info(f"Reverted form {form_id} to version {new_version}")
        return {
            "schema": previous_schema,
            "version": new_version
        }

    except Exception as e:
        logger.error(f"Error undoing form {form_id}: {e}")
        raise


def delete_form(form_id: str, user_id: str) -> bool:
    """
    Delete a form document.

    Args:
        form_id: Form document ID
        user_id: User ID (for removing from user's forms list)

    Returns:
        True if deleted successfully
    """
    try:
        # Delete form document
        db.collection("forms").document(form_id).delete()

        # Remove from user's forms list
        user_ref = db.collection("users").document(user_id)
        user_ref.update({
            "forms": firestore.ArrayRemove([form_id])
        })

        logger.info(f"Deleted form: {form_id}")
        return True

    except Exception as e:
        logger.error(f"Error deleting form {form_id}: {e}")
        raise


def get_user_forms(user_id: str) -> List[Dict[str, Any]]:
    """
    Get all forms owned by a user.

    Args:
        user_id: User ID

    Returns:
        List of form summaries
    """
    try:
        forms_query = db.collection("forms").where("userId", "==", user_id)
        docs = forms_query.stream()

        forms = []
        for doc in docs:
            data = doc.to_dict()
            forms.append({
                "formId": doc.id,
                "title": data.get("title", "Untitled Form"),
                "description": data.get("description", ""),
                "createdAt": data.get("createdAt"),
                "updatedAt": data.get("updatedAt"),
                "responseCount": len(data.get("responses", []))
            })

        return sorted(forms, key=lambda x: x.get("updatedAt") or x.get("createdAt"), reverse=True)

    except Exception as e:
        logger.error(f"Error getting forms for user {user_id}: {e}")
        raise


def add_form_response(form_id: str, answers: Dict[str, Any]) -> str:
    """
    Add a response to a form.

    Args:
        form_id: Form document ID
        answers: Dictionary of component ID to answer

    Returns:
        Response ID
    """
    try:
        form_ref = db.collection("forms").document(form_id)
        form_doc = form_ref.get()

        if not form_doc.exists:
            raise ValueError(f"Form {form_id} not found")

        import uuid
        response_id = str(uuid.uuid4())

        response = {
            "responseId": response_id,
            "submittedAt": datetime.utcnow(),
            "answers": answers
        }

        form_ref.update({
            "responses": firestore.ArrayUnion([response])
        })

        logger.info(f"Added response {response_id} to form {form_id}")
        return response_id

    except Exception as e:
        logger.error(f"Error adding response to form {form_id}: {e}")
        raise


def get_form_responses(form_id: str) -> List[Dict[str, Any]]:
    """
    Get all responses for a form.

    Args:
        form_id: Form document ID

    Returns:
        List of responses
    """
    try:
        form_doc = db.collection("forms").document(form_id).get()

        if not form_doc.exists:
            raise ValueError(f"Form {form_id} not found")

        form_data = form_doc.to_dict()
        return form_data.get("responses", [])

    except Exception as e:
        logger.error(f"Error getting responses for form {form_id}: {e}")
        raise
