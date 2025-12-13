"""
Decorator utilities for FormFlow.
"""
import logging
from functools import wraps
from flask import request, g

from app.services.firebase_service import verify_token, get_form

logger = logging.getLogger(__name__)


def require_auth(f):
    """
    Decorator to require Firebase authentication.
    Sets g.user_id and g.user_email on success.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get("Authorization")

        if not auth_header:
            return {"error": "Authorization header required"}, 401

        # Extract token from "Bearer <token>"
        parts = auth_header.split()
        if len(parts) != 2 or parts[0].lower() != "bearer":
            return {"error": "Invalid authorization header format"}, 401

        token = parts[1]

        # Verify token
        decoded = verify_token(token)
        if not decoded:
            return {"error": "Invalid or expired token"}, 401

        # Set user info in request context
        g.user_id = decoded.get("uid")
        g.user_email = decoded.get("email")

        logger.debug(f"Authenticated user: {g.user_id}")
        return f(*args, **kwargs)

    return decorated_function


def require_form_owner(f):
    """
    Decorator to require form ownership.
    Must be used after @require_auth.
    Expects 'form_id' in route parameters.
    Sets g.form on success.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Get form_id from route parameters
        form_id = kwargs.get("form_id")
        if not form_id:
            return {"error": "Form ID required"}, 400

        # Get form from database
        form = get_form(form_id)
        if not form:
            return {"error": "Form not found"}, 404

        # Check ownership
        if form.get("userId") != g.user_id:
            logger.warning(f"User {g.user_id} attempted to access form {form_id} owned by {form.get('userId')}")
            return {"error": "Access denied"}, 403

        # Set form in request context
        g.form = form

        return f(*args, **kwargs)

    return decorated_function
