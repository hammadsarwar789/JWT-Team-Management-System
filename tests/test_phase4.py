from extensions import users_collection, audit_logs_collection
from models.user import UserRole
from services.audit_service import log_event, get_audit_logs


def test_security_headers(client):
    """Test that all API responses attach defensive security headers."""
    res = client.get("/api/v1/profile")
    assert res.headers.get("X-Frame-Options") == "DENY"
    assert res.headers.get("X-Content-Type-Options") == "nosniff"
    assert res.headers.get("X-XSS-Protection") == "1; mode=block"


def test_audit_log_service_and_admin_endpoint(client, mock_db):
    """Test audit log creation and Admin audit log endpoint."""
    # 1. Direct log_event
    log_event("system_user", "TEST_SECURITY_EVENT", {"ip": "127.0.0.1"})
    logs = get_audit_logs()
    assert logs["total"] >= 1
    assert logs["items"][0]["action"] == "TEST_SECURITY_EVENT"

    # 2. Signup normal user
    res_user = client.post("/api/v1/auth/signup", json={
        "username": "audituser",
        "email": "audituser@example.com",
        "password": "password123",
    })
    user_token = res_user.get_json()["access_token"]

    # 3. Signup admin user
    res_admin = client.post("/api/v1/auth/signup", json={
        "username": "auditadmin",
        "email": "auditadmin@example.com",
        "password": "password123",
    })
    admin_token = res_admin.get_json()["access_token"]
    users_collection.update_one({"email": "auditadmin@example.com"}, {"$set": {"role": UserRole.ADMIN}})

    # Non-admin access to /admin/audit-logs -> 403 Forbidden
    res_unauth = client.get("/api/v1/admin/audit-logs", headers={"Authorization": f"Bearer {user_token}"})
    assert res_unauth.status_code == 403

    # Admin access to /admin/audit-logs -> 200 OK
    res_auth = client.get("/api/v1/admin/audit-logs", headers={"Authorization": f"Bearer {admin_token}"})
    assert res_auth.status_code == 200
    items = res_auth.get_json()["items"]
    assert len(items) > 0


def test_api_v1_versioning_and_legacy_redirect(client):
    """Test that /api/v1/ routes work and legacy /api/ routes rewrite cleanly."""
    res_signup = client.post("/api/v1/auth/signup", json={
        "username": "v1user",
        "email": "v1user@example.com",
        "password": "password123",
    })
    assert res_signup.status_code == 201
    token = res_signup.get_json()["access_token"]

    # Call versioned route
    res_v1 = client.get("/api/v1/profile", headers={"Authorization": f"Bearer {token}"})
    assert res_v1.status_code == 200
    assert res_v1.get_json()["username"] == "v1user"

    # Call legacy route /api/profile -> rewritten by app.before_request middleware
    res_legacy = client.get("/api/profile", headers={"Authorization": f"Bearer {token}"})
    assert res_legacy.status_code == 200
    assert res_legacy.get_json()["username"] == "v1user"
