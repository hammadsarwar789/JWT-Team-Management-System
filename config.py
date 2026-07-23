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

    # Redis & Celery settings
    REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
    CELERY_BROKER_URL = REDIS_URL
    CELERY_RESULT_BACKEND = REDIS_URL
    CELERY_TASK_ALWAYS_EAGER = os.environ.get("CELERY_TASK_ALWAYS_EAGER", "False").lower() in ("true", "1", "t")

