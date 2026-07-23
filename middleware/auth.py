from functools import wraps
from flask import request, jsonify

from extensions import db
from auth.utils import decode_token
from models.user import User, UserRole


def parse_oid(id_str):
    try:
        return int(id_str)
    except (ValueError, TypeError):
        return None


def token_required(f):
    """Decorator requiring a valid token header, query param, or form field."""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header.split(" ", 1)[1].strip()
        elif request.args.get("token"):
            token = request.args.get("token").strip()
        elif request.form.get("token"):
            token = request.form.get("token").strip()

        if not token:
            return jsonify({"error": "Missing or invalid Authorization header"}), 401

        payload = decode_token(token)
        if payload is None:
            return jsonify({"error": "Token is invalid or expired"}), 401

        user_id = payload.get("sub")
        user_id_int = parse_oid(user_id)
        if user_id_int is None:
            return jsonify({"error": "Invalid user id"}), 400

        user = db.session.get(User, user_id_int)
        if not user:
            return jsonify({"error": "User not found"}), 404

        request.token = token
        request.token_payload = payload
        request.token_jti = payload.get("jti")
        request.user_id = str(user.id)
        request.user_oid = user.id
        request.user_role = user.role or UserRole.USER
        request.current_user = user

        return f(*args, **kwargs)

    return decorated


def role_required(*allowed_roles):
    """Decorator restricting route access to specified RBAC roles."""
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            current_role = getattr(request, "user_role", None)
            if not current_role or current_role not in allowed_roles:
                return jsonify({
                    "error": f"Access forbidden. Required role: {', '.join(allowed_roles)}"
                }), 403
            return f(*args, **kwargs)
        return decorated
    return decorator
