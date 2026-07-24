import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()


class Config:
    # In production, ALWAYS load this from an environment variable / .env file
    SECRET_KEY = os.environ.get("SECRET_KEY", "change-this-in-production")

    # PostgreSQL Connection URL (Loaded from .env / DATABASE_URL)
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL",
        "postgresql://postgres:postgres@localhost:5432/jwt_auth_app"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # JWT Expiry settings
    JWT_EXPIRES = timedelta(hours=24)
    JWT_ACCESS_EXPIRES = timedelta(minutes=30)
    JWT_REFRESH_EXPIRES = timedelta(days=7)

    # JWT Cookie settings
    JWT_COOKIE_SECURE = os.environ.get("JWT_COOKIE_SECURE", "False").lower() in ("true", "1", "t")
    JWT_COOKIE_HTTPONLY = True
    JWT_COOKIE_SAMESITE = "Lax"

    # Email Verification Enforcement
    REQUIRE_EMAIL_VERIFICATION = os.environ.get("REQUIRE_EMAIL_VERIFICATION", "True").lower() in ("true", "1", "t")

    # Redis & Celery settings
    REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
    CELERY_BROKER_URL = REDIS_URL
    CELERY_RESULT_BACKEND = REDIS_URL
    CELERY_TASK_ALWAYS_EAGER = os.environ.get("CELERY_TASK_ALWAYS_EAGER", "False").lower() in ("true", "1", "t")

    # Mail / SMTP Configuration
    MAIL_SERVER = os.environ.get("MAIL_SERVER", "smtp.gmail.com")
    MAIL_PORT = int(os.environ.get("MAIL_PORT", 587))
    MAIL_USE_TLS = os.environ.get("MAIL_USE_TLS", "True").lower() in ("true", "1", "t")
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME", "")
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD", "")
    APP_BASE_URL = os.environ.get("APP_BASE_URL", "http://localhost:5000")


