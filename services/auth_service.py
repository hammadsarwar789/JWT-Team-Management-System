import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from pymongo.errors import DuplicateKeyError

from extensions import users_collection
from extensions import users_collection
from auth.utils import generate_token, generate_tokens_pair, decode_token
from models.user import UserRole
from bson import ObjectId
from bson.errors import InvalidId


def register_user(cleaned_data):
    """Business logic to register a new user."""
    email = cleaned_data["email"]

    if users_collection.find_one({"email": email}):
        return False, "Email already registered", None, 409

    role = cleaned_data.get("role")
    if role not in UserRole.ALL:
        role = UserRole.USER

    user = {
        "username": cleaned_data["username"],
        "email": email,
        "password": generate_password_hash(cleaned_data["password"]),
        "full_name": cleaned_data.get("full_name", ""),
        "bio": cleaned_data.get("bio", ""),
        "role": role,
        "is_verified": False,
        "profile_picture": "",
        "created_at": datetime.datetime.now(datetime.timezone.utc),
    }

    try:
        result = users_collection.insert_one(user)
    except DuplicateKeyError:
        return False, "Email already registered", None, 409

    tokens = generate_tokens_pair(result.inserted_id)
    return True, "Account created", tokens, 201


def authenticate_user(email, password):
    """Business logic to authenticate user credentials."""
    user = users_collection.find_one({"email": email})
    if not user or not check_password_hash(user["password"], password):
        return False, "Invalid email or password", None, 401

    tokens = generate_tokens_pair(user["_id"])
    return True, "Signed in", tokens, 200


def refresh_access_token(refresh_token):
    """Generate a new access token from a valid refresh token."""
    if not refresh_token:
        return False, "refresh_token is required", None, 400

    payload = decode_token(refresh_token, expected_type="refresh")
    if not payload:
        return False, "Refresh token is invalid or expired", None, 401

    user_id = payload.get("sub")
    try:
        user_oid = ObjectId(user_id)
    except (InvalidId, TypeError):
        return False, "Invalid user id", None, 400

    user = users_collection.find_one({"_id": user_oid})
    if not user:
        return False, "User not found", None, 404

    new_access_token = generate_token(user["_id"], token_type="access")
    return True, "Token refreshed", {"access_token": new_access_token, "token": new_access_token}, 200

