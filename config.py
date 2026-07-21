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
