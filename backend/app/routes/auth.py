"""
Authentication routes for FormFlow.
"""
import logging
from flask import Blueprint, request, g

from app.services.firebase_service import verify_token, get_user, create_user
from app.utils.decorators import require_auth

logger = logging.getLogger(__name__)

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/verify", methods=["POST"])
def verify_auth():
    """
    Verify Firebase ID token and return user info.
    Creates user document if it doesn't exist.

    Request Headers:
        Authorization: Bearer <firebase_token>

    Returns:
        User info including userId and email
    """
    auth_header = request.headers.get("Authorization")

    if not auth_header:
        return {"error": "Authorization header required"}, 401

    # Extract token
    parts = auth_header.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return {"error": "Invalid authorization header format"}, 401

    token = parts[1]

    # Verify token
    decoded = verify_token(token)
    if not decoded:
        return {"error": "Invalid or expired token"}, 401

    user_id = decoded.get("uid")
    email = decoded.get("email", "")
    display_name = decoded.get("name", "")

    # Get or create user document
    user = get_user(user_id)
    if not user:
        logger.info(f"Creating new user document for: {user_id}")
        user = create_user(user_id, email, display_name)

    return {
        "userId": user_id,
        "email": email,
        "displayName": user.get("displayName", display_name),
        "forms": user.get("forms", [])
    }, 200


@auth_bp.route("/me", methods=["GET"])
@require_auth
def get_current_user():
    """
    Get current authenticated user info.

    Returns:
        Current user info
    """
    user = get_user(g.user_id)
    if not user:
        return {"error": "User not found"}, 404

    return {
        "userId": g.user_id,
        "email": g.user_email,
        "displayName": user.get("displayName", ""),
        "forms": user.get("forms", []),
        "createdAt": str(user.get("createdAt", ""))
    }, 200
