from flask import Flask, render_template, jsonify
from pymongo.errors import PyMongoError

from config import Config
from extensions import init_indexes
from middleware.logger import setup_logger
from auth.routes import auth_bp
from profiles.routes import profile_bp


from middleware.security import setup_security_headers
from flask import request


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    setup_logger(app)
    setup_security_headers(app)

    # API blueprints (mounted under both /api/v1 and legacy /api)
    app.register_blueprint(auth_bp, url_prefix="/api/v1/auth")
    app.register_blueprint(profile_bp, url_prefix="/api/v1")

    # Legacy route aliases for backward compatibility
    app.register_blueprint(auth_bp, url_prefix="/api/auth", name="auth_legacy")
    app.register_blueprint(profile_bp, url_prefix="/api", name="profile_legacy")



    # HTML page routes (these just render the templates;
    # the templates call the API above using JavaScript)
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

    from flask import send_from_directory
    import os

    @app.route("/uploads/<path:filename>")
    def serve_uploads(filename):
        upload_dir = os.path.join(app.root_path, "uploads")
        return send_from_directory(upload_dir, filename)

    return app


