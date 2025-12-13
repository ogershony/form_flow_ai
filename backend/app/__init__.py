"""
FormFlow Backend Application Factory
"""
import os
import logging
from flask import Flask
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask extensions
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)


def create_app(config_name=None):
    """Application factory function."""
    app = Flask(__name__)

    # Load configuration
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-key")
    app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024  # 10MB max upload

    # Initialize CORS
    allowed_origins = [
        os.environ.get("FRONTEND_URL", "http://localhost:3000"),
        "https://*.appspot.com",
    ]

    CORS(app, resources={
        r"/api/*": {
            "origins": allowed_origins,
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"],
            "supports_credentials": True
        }
    })

    # Initialize rate limiter
    limiter.init_app(app)

    # Initialize Firebase
    from app.services.firebase_service import init_firebase
    init_firebase()

    # Register blueprints
    from app.routes.auth import auth_bp
    from app.routes.forms import forms_bp

    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(forms_bp, url_prefix="/api/forms")

    # Health check endpoint
    @app.route("/health")
    def health_check():
        return {"status": "healthy"}, 200

    # Error handlers
    @app.errorhandler(400)
    def bad_request(error):
        return {"error": "Bad request", "message": str(error)}, 400

    @app.errorhandler(401)
    def unauthorized(error):
        return {"error": "Unauthorized", "message": "Authentication required"}, 401

    @app.errorhandler(403)
    def forbidden(error):
        return {"error": "Forbidden", "message": "Access denied"}, 403

    @app.errorhandler(404)
    def not_found(error):
        return {"error": "Not found", "message": "Resource not found"}, 404

    @app.errorhandler(429)
    def rate_limit_exceeded(error):
        return {"error": "Rate limit exceeded", "message": "Too many requests"}, 429

    @app.errorhandler(500)
    def internal_error(error):
        logger.error(f"Internal server error: {error}")
        return {"error": "Internal server error", "message": "Something went wrong"}, 500

    logger.info("FormFlow backend initialized successfully")
    return app
