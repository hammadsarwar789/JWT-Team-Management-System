import io
from bson import ObjectId
from extensions import users_collection


def test_dual_token_and_refresh_endpoint(client):
    """Test signup returns access_token & refresh_token, and refresh endpoint works."""
    # 1. Signup
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

    # 2. Refresh access token
    ref_res = client.post("/api/auth/refresh", json={"refresh_token": refresh_token})
    assert ref_res.status_code == 200
    ref_data = ref_res.get_json()
    assert "access_token" in ref_data
    assert ref_data["message"] == "Token refreshed"

    # Test protected route with new access token
    headers = {"Authorization": f"Bearer {ref_data['access_token']}"}
    prof_res = client.get("/api/profile", headers=headers)
    assert prof_res.status_code == 200
    assert prof_res.get_json()["username"] == "dualtok"


def test_password_reset_workflow(client):
    """Test forgot-password and reset-password workflow."""
    # Signup user
    client.post("/api/auth/signup", json={
        "username": "resetuser",
        "email": "resetuser@example.com",
        "password": "oldpassword123",
    })

    # Forgot password request
    forgot_res = client.post("/api/auth/forgot-password", json={"email": "resetuser@example.com"})
    assert forgot_res.status_code == 200
    forgot_data = forgot_res.get_json()
    assert "reset_token" in forgot_data
    reset_token = forgot_data["reset_token"]

    # Reset password
    reset_res = client.post("/api/auth/reset-password", json={
        "reset_token": reset_token,
        "new_password": "newsecurepassword123",
    })
    assert reset_res.status_code == 200
    assert reset_res.get_json()["message"] == "Password updated successfully"

    # Signin with old password fails
    signin_old = client.post("/api/auth/signin", json={
        "email": "resetuser@example.com",
        "password": "oldpassword123",
    })
    assert signin_old.status_code == 401

    # Signin with new password succeeds
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

    # Profile initially shows is_verified = False
    prof_res = client.get("/api/profile", headers={"Authorization": f"Bearer {access_token}"})
    assert prof_res.get_json()["is_verified"] is False

    # Generate verification token
    from services.password_reset_service import generate_verification_token
    user_doc = users_collection.find_one({"email": "verifyuser@example.com"})
    with app.app_context():
        v_token = generate_verification_token(user_doc["_id"])


    # Verify email
    v_res = client.post("/api/auth/verify-email", json={"verification_token": v_token})
    assert v_res.status_code == 200
    assert v_res.get_json()["message"] == "Email verified successfully"

    # Profile now shows is_verified = True
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

    # Invalid file extension
    data_bad = {"picture": (io.BytesIO(b"fake image data"), "test.txt")}
    res_bad = client.post("/api/profile/picture", data=data_bad, headers=headers, content_type="multipart/form-data")
    assert res_bad.status_code == 400
    assert "Invalid file type" in res_bad.get_json()["error"]

    # Valid PNG image upload
    data_valid = {"picture": (io.BytesIO(b"\x89PNG\r\n\x1a\nfake_image_bytes"), "avatar.png")}
    res_valid = client.post("/api/profile/picture", data=data_valid, headers=headers, content_type="multipart/form-data")
    assert res_valid.status_code == 200
    user_data = res_valid.get_json()["user"]
    assert user_data["profile_picture"].startswith("/uploads/profile_images/")

    # Fetch uploaded image via static route
    img_res = client.get(user_data["profile_picture"])
    assert img_res.status_code == 200
    assert b"fake_image_bytes" in img_res.data
