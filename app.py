import os
from flask import Flask, render_template, jsonify, request, send_from_directory
from sqlalchemy.exc import SQLAlchemyError

from config import Config
from extensions import init_db
from middleware.logger import setup_logger
from middleware.security import setup_security_headers
from auth.routes import auth_bp
from profiles.routes import profile_bp


def create_app(config_class=Config, test_config=None):
    app = Flask(__name__)
    app.config.from_object(config_class)
    if test_config:
        app.config.update(test_config)

    setup_logger(app)
    setup_security_headers(app)

    # Initialize SQLAlchemy DB tables
    init_db(app)

    # API blueprints (mounted under both /api/v1 and legacy /api)
    app.register_blueprint(auth_bp, url_prefix="/api/v1/auth")
    app.register_blueprint(profile_bp, url_prefix="/api/v1")

    # Legacy route aliases for backward compatibility
    app.register_blueprint(auth_bp, url_prefix="/api/auth", name="auth_legacy")
    app.register_blueprint(profile_bp, url_prefix="/api", name="profile_legacy")

    # Database connection / transaction error handler
    @app.errorhandler(SQLAlchemyError)
    def handle_db_error(error):
        app.logger.error(f"Database Error: {str(error)}")
        return jsonify({"error": "Database error occurred", "details": str(error)}), 503

    # HTML page routes
    @app.route("/")
    @app.route("/signin")
    def signin_page():
        return render_template("signin.html")

    @app.route("/signup")
    def signup_page():
        return render_template("signup.html")

    @app.route("/profile")
    def profile_page():
        return render_template("profile.html")

    @app.route("/uploads/<path:filename>")
    def serve_uploads(filename):
        upload_dir = os.path.join(app.root_path, "uploads")
        return send_from_directory(upload_dir, filename)

    return app
