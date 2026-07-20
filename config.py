import os
from datetime import timedelta


class Config:
    # In production, ALWAYS load this from an environment variable / .env file
    SECRET_KEY = os.environ.get("SECRET_KEY", "change-this-in-production")

    # MongoDB connection string. Local example:
    # mongodb://localhost:27017/jwt_auth_app
    # Atlas example:
    # mongodb+srv://<user>:<password>@cluster0.mongodb.net/jwt_auth_app
    MONGO_URI = os.environ.get("MONGO_URI", "mongodb://localhost:27017/jwt_auth_app")

    # JWT Expiry settings
    JWT_EXPIRES = timedelta(hours=24)
    JWT_ACCESS_EXPIRES = timedelta(minutes=30)
    JWT_REFRESH_EXPIRES = timedelta(days=7)

