import datetime
import jwt
from bson import ObjectId
from flask import jsonify

from auth.utils import generate_token, decode_token, token_required


def test_generate_and_decode_token(app):
    """Test generating a valid JWT token and decoding it."""
    with app.app_context():
        user_id = str(ObjectId())
        token = generate_token(user_id)
        assert isinstance(token, str)

        payload = decode_token(token)
        assert payload is not None
        assert payload["sub"] == user_id


def test_decode_token_invalid(app):
    """Test decoding invalid and tampered tokens."""
    with app.app_context():
        assert decode_token("invalid-token-string") is None

        # Expired token test
        now = datetime.datetime.now(datetime.timezone.utc)
        payload = {
            "sub": str(ObjectId()),
            "iat": now - datetime.timedelta(hours=2),
            "exp": now - datetime.timedelta(hours=1),
        }
        expired_token = jwt.encode(payload, app.config["SECRET_KEY"], algorithm="HS256")
        assert decode_token(expired_token) is None


from auth.utils import generate_token, decode_token
from middleware.auth import token_required, role_required
from models.user import UserRole
from extensions import users_collection


def test_role_required_decorator(app, client, mock_db):
    """Test @role_required RBAC permission enforcement."""
    @app.route("/test-admin-only")
    @token_required
    @role_required(UserRole.ADMIN)
    def admin_route():
        return jsonify({"message": "admin access granted"}), 200

    # Create normal user
    res_signup = client.post("/api/auth/signup", json={
        "username": "regular_user",
        "email": "regular@example.com",
        "password": "password123",
        "role": UserRole.USER,
    })
    token = res_signup.get_json()["token"]

    # Regular user gets 403 Forbidden
    res_forbidden = client.get("/test-admin-only", headers={"Authorization": f"Bearer {token}"})
    assert res_forbidden.status_code == 403
    assert "Access forbidden" in res_forbidden.get_json()["error"]

    # Promote user to Admin in DB
    users_collection.update_one({"email": "regular@example.com"}, {"$set": {"role": UserRole.ADMIN}})

    # Admin user gets 200 OK
    res_allowed = client.get("/test-admin-only", headers={"Authorization": f"Bearer {token}"})
    assert res_allowed.status_code == 200
    assert res_allowed.get_json()["message"] == "admin access granted"

