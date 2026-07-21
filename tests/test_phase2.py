import io
from extensions import db
from models.user import User


def test_dual_token_and_refresh_endpoint(client):
    """Test signup returns access_token & refresh_token, and refresh endpoint works."""
    signup_res = client.post("/api/auth/signup", json={
        "username": "dualtok",
        "email": "dualtok@example.com",
        "password": "password123",
    })
    assert signup_res.status_code == 201
    data = signup_res.get_json()
    assert "access_token" in data
    assert "refresh_token" in data

    refresh_token = data["refresh_token"]

    ref_res = client.post("/api/auth/refresh", json={"refresh_token": refresh_token})
    assert ref_res.status_code == 200
    ref_data = ref_res.get_json()
    assert "access_token" in ref_data
    assert ref_data["message"] == "Token refreshed"

    headers = {"Authorization": f"Bearer {ref_data['access_token']}"}
    prof_res = client.get("/api/profile", headers=headers)
    assert prof_res.status_code == 200
    assert prof_res.get_json()["username"] == "dualtok"


def test_password_reset_workflow(client):
    """Test forgot-password and reset-password workflow."""
    client.post("/api/auth/signup", json={
        "username": "resetuser",
        "email": "resetuser@example.com",
        "password": "oldpassword123",
    })

    forgot_res = client.post("/api/auth/forgot-password", json={"email": "resetuser@example.com"})
    assert forgot_res.status_code == 200
    forgot_data = forgot_res.get_json()
    assert "reset_token" in forgot_data
    reset_token = forgot_data["reset_token"]

    reset_res = client.post("/api/auth/reset-password", json={
        "reset_token": reset_token,
        "new_password": "newsecurepassword123",
    })
    assert reset_res.status_code == 200
    assert reset_res.get_json()["message"] == "Password updated successfully"

    signin_old = client.post("/api/auth/signin", json={
        "email": "resetuser@example.com",
        "password": "oldpassword123",
    })
    assert signin_old.status_code == 401

    signin_new = client.post("/api/auth/signin", json={
        "email": "resetuser@example.com",
        "password": "newsecurepassword123",
    })
    assert signin_new.status_code == 200


def test_email_verification_workflow(client, app):
    """Test generating verification token and verifying email."""
    signup_res = client.post("/api/auth/signup", json={
        "username": "verifyuser",
        "email": "verifyuser@example.com",
        "password": "password123",
    })
    access_token = signup_res.get_json()["access_token"]

    prof_res = client.get("/api/profile", headers={"Authorization": f"Bearer {access_token}"})
    assert prof_res.get_json()["is_verified"] is False

    from services.password_reset_service import generate_verification_token
    with app.app_context():
        user = User.query.filter_by(email="verifyuser@example.com").first()
        v_token = generate_verification_token(user.id)

    v_res = client.post("/api/auth/verify-email", json={"verification_token": v_token})
    assert v_res.status_code == 200
    assert v_res.get_json()["message"] == "Email verified successfully"

    prof_res2 = client.get("/api/profile", headers={"Authorization": f"Bearer {access_token}"})
    assert prof_res2.get_json()["is_verified"] is True


def test_profile_picture_upload(client, app):
    """Test profile picture image upload and static file serving."""
    signup_res = client.post("/api/auth/signup", json={
        "username": "avataruser",
        "email": "avataruser@example.com",
        "password": "password123",
    })
    token = signup_res.get_json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    data_bad = {"picture": (io.BytesIO(b"fake image data"), "test.txt")}
    res_bad = client.post("/api/profile/picture", data=data_bad, headers=headers, content_type="multipart/form-data")
    assert res_bad.status_code == 400
    assert "Invalid file type" in res_bad.get_json()["error"]

    data_valid = {"picture": (io.BytesIO(b"\x89PNG\r\n\x1a\nfake_image_bytes"), "avatar.png")}
    res_valid = client.post("/api/profile/picture", data=data_valid, headers=headers, content_type="multipart/form-data")
    assert res_valid.status_code == 200
    user_data = res_valid.get_json()["user"]
    assert user_data["profile_picture"].startswith("/uploads/profile_images/")

    img_res = client.get(user_data["profile_picture"])
    assert img_res.status_code == 200
    assert b"fake_image_bytes" in img_res.data
