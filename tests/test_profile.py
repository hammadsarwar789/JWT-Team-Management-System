from extensions import db
from models.user import User, UserRole
from auth.utils import generate_token


def signup_and_get_token(client, email="user@example.com"):
    signup_payload = {
        "username": "user1",
        "email": email,
        "password": "password123",
        "full_name": "User One",
        "bio": "Hello world",
    }
    res = client.post("/api/auth/signup", json=signup_payload)
    return res.get_json()["token"]


def test_get_profile_success(app, client):
    token = signup_and_get_token(client, "profile_get@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    res = client.get("/api/profile", headers=headers)
    assert res.status_code == 200
    data = res.get_json()
    assert data["username"] == "user1"
    assert data["email"] == "profile_get@example.com"
    assert data["full_name"] == "User One"


def test_get_profile_invalid_id(app, client):
    with app.app_context():
        token = generate_token("invalid-object-id-string")

    res = client.get("/api/profile", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 400
    assert "Invalid user id" in res.get_json()["error"]


def test_edit_profile_success(client):
    token = signup_and_get_token(client, "profile_edit@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    update_payload = {
        "username": "new_username",
        "full_name": "Updated Name",
        "bio": "Updated Bio",
    }
    res = client.put("/api/profile", json=update_payload, headers=headers)
    assert res.status_code == 200
    data = res.get_json()
    assert data["username"] == "new_username"
    assert data["full_name"] == "Updated Name"
    assert data["bio"] == "Updated Bio"


def test_edit_profile_invalid_validation(client):
    token = signup_and_get_token(client, "profile_val@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    # Empty username update
    res = client.put("/api/profile", json={"username": ""}, headers=headers)
    assert res.status_code == 400
    assert "Username cannot be empty" in res.get_json()["error"]

    # No fields to update
    res2 = client.put("/api/profile", json={}, headers=headers)
    assert res2.status_code == 400


def test_fellows_crud(client):
    token = signup_and_get_token(client, "fellows@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Add fellow
    add_payload = {
        "name": "Jane Doe",
        "email": "jane@example.com",
        "relation": "Colleague",
    }
    res_add = client.post("/api/fellows", json=add_payload, headers=headers)
    assert res_add.status_code == 201
    fellow = res_add.get_json()
    assert fellow["name"] == "Jane Doe"
    assert fellow["relation"] == "Colleague"
    fellow_id = fellow["id"]

    # 2. List fellows
    res_list = client.get("/api/fellows", headers=headers)
    assert res_list.status_code == 200
    res_json = res_list.get_json()
    fellows_list = res_json.get("items", res_json) if isinstance(res_json, dict) else res_json
    assert len(fellows_list) == 1
    assert fellows_list[0]["id"] == fellow_id

    # 3. Edit fellow
    edit_payload = {"relation": "Best Friend"}
    res_edit = client.put(f"/api/fellows/{fellow_id}", json=edit_payload, headers=headers)
    assert res_edit.status_code == 200
    assert res_edit.get_json()["relation"] == "Best Friend"

    # 4. Delete fellow
    res_del = client.delete(f"/api/fellows/{fellow_id}", headers=headers)
    assert res_del.status_code == 200
    assert res_del.get_json()["message"] == "Fellow deleted"

    # Verify deleted
    res_list2 = client.get("/api/fellows", headers=headers)
    res_json2 = res_list2.get_json()
    fellows_list2 = res_json2.get("items", res_json2) if isinstance(res_json2, dict) else res_json2
    assert len(fellows_list2) == 0


def test_fellows_invalid_id(client):
    token = signup_and_get_token(client, "fellows_invalid@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    # Invalid fellow id format
    res_edit = client.put("/api/fellows/bad-id", json={"name": "X"}, headers=headers)
    assert res_edit.status_code == 400

    # Non-existent fellow id
    res_del = client.delete("/api/fellows/999999", headers=headers)
    assert res_del.status_code == 404


def test_change_user_role_admin(app, client):
    # User 1 (Target user)
    token_target = signup_and_get_token(client, "target_user@example.com")
    res_prof = client.get("/api/profile", headers={"Authorization": f"Bearer {token_target}"})
    target_id = res_prof.get_json()["id"]

    # User 2 (Admin user)
    token_admin = signup_and_get_token(client, "admin_user@example.com")
    with app.app_context():
        admin_user = User.query.filter_by(email="admin_user@example.com").first()
        admin_user.role = UserRole.ADMIN
        db.session.commit()

    # Non-admin attempt -> 403
    res_unauth = client.put(f"/api/admin/users/{target_id}/role", json={"role": UserRole.MANAGER}, headers={"Authorization": f"Bearer {token_target}"})
    assert res_unauth.status_code == 403

    # Admin attempt -> 200
    res_admin = client.put(f"/api/admin/users/{target_id}/role", json={"role": UserRole.MANAGER}, headers={"Authorization": f"Bearer {token_admin}"})
    assert res_admin.status_code == 200
    assert res_admin.get_json()["user"]["role"] == UserRole.MANAGER
