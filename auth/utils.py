import datetime
from functools import wraps

import jwt
from flask import request, jsonify, current_app


def generate_token(user_id, token_type="access", expires_delta=None):
    """Create a signed JWT for access or refresh purposes."""
    now = datetime.datetime.now(datetime.timezone.utc)
    if expires_delta is None:
        if token_type == "refresh":
            expires_delta = current_app.config.get("JWT_REFRESH_EXPIRES", datetime.timedelta(days=7))
        else:
            expires_delta = current_app.config.get("JWT_ACCESS_EXPIRES", datetime.timedelta(minutes=30))

    payload = {
        "sub": str(user_id),
        "type": token_type,
        "iat": now,
        "exp": now + expires_delta,
    }
    return jwt.encode(payload, current_app.config["SECRET_KEY"], algorithm="HS256")


def generate_tokens_pair(user_id):
    """Generate both short-lived access_token and long-lived refresh_token."""
    access_token = generate_token(user_id, token_type="access")
    refresh_token = generate_token(user_id, token_type="refresh")
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token": access_token,  # for backward compatibility
    }


def decode_token(token, expected_type=None):
    """Return payload if valid, or None if expired/tampered/invalid/wrong type."""
    try:
        payload = jwt.decode(
            token,
            current_app.config["SECRET_KEY"],
            algorithms=["HS256"],
        )
        if expected_type and payload.get("type") != expected_type:
            # If payload type is set and doesn't match expected_type, return None
            if "type" in payload:
                return None
        return payload
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return None


from middleware.auth import token_required  # noqa: F401


