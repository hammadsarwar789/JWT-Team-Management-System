import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.exc import IntegrityError

from extensions import db
from auth.utils import generate_token, generate_tokens_pair, decode_token
from models.user import User, UserRole


from sqlalchemy import func


from flask import current_app
from services.password_reset_service import generate_verification_token


def register_user(cleaned_data):
    """Business logic to register a new user."""
    email = cleaned_data["email"].strip().lower()

    if User.query.filter(func.lower(User.email) == email).first():
        return False, "Email already registered", None, 409

    role = cleaned_data.get("role")
    if role not in UserRole.ALL:
        role = UserRole.USER

    user = User(
        username=cleaned_data["username"],
        email=email,
        password=generate_password_hash(cleaned_data["password"]),
        full_name=cleaned_data.get("full_name", ""),
        bio=cleaned_data.get("bio", ""),
        role=role,
        is_verified=False,
        profile_picture="",
        created_at=datetime.datetime.now(datetime.timezone.utc),
    )

    try:
        db.session.add(user)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return False, "Email already registered", None, 409

    # Generate verification token and dispatch Celery email task
    verification_token = generate_verification_token(user.id)

    tokens = generate_tokens_pair(user.id)
    if isinstance(tokens, dict):
        tokens["verification_token"] = verification_token

    return True, "Account created", tokens, 201


def authenticate_user(email, password):
    """Business logic to authenticate user credentials."""
    clean_email = email.strip().lower()
    user = User.query.filter(func.lower(User.email) == clean_email).first()
    if not user or not check_password_hash(user.password, password):
        return False, "Invalid email or password", None, 401

    require_verify = current_app.config.get("REQUIRE_EMAIL_VERIFICATION", True)
    is_testing = current_app.config.get("TESTING", False)

    # Block signin if email verification is required and user email is unverified
    if require_verify and not is_testing and not user.is_verified:
        return False, "Email not verified. Please verify your email before logging in.", None, 403

    tokens = generate_tokens_pair(user.id)
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
        user_id_int = int(user_id)
    except (ValueError, TypeError):
        return False, "Invalid user id", None, 400

    user = db.session.get(User, user_id_int)
    if not user:
        return False, "User not found", None, 404

    new_access_token = generate_token(user.id, token_type="access")
    return True, "Token refreshed", {"access_token": new_access_token, "token": new_access_token}, 200
