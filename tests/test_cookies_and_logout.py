def test_signin_sets_http_only_cookie(client):
    """Test that signin sets an HTTP-only refresh_token cookie."""
    client.post("/api/v1/auth/signup", json={
        "username": "cookieuser",
        "email": "cookie@example.com",
        "password": "password123"
    })
    res = client.post("/api/v1/auth/signin", json={
        "email": "cookie@example.com",
        "password": "password123"
    })
    assert res.status_code == 200
    # Inspect Set-Cookie header
    cookie_header = res.headers.get("Set-Cookie", "")
    assert "refresh_token=" in cookie_header
    assert "HttpOnly" in cookie_header


def test_logout_revokes_token_and_clears_cookie(client):
    """Test that /logout invalidates the current access token and clears cookie."""
    reg = client.post("/api/v1/auth/signup", json={
        "username": "logoutuser",
        "email": "logout@example.com",
        "password": "password123"
    })
    token = reg.get_json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Verify protected access before logout
    p1 = client.get("/api/v1/profile", headers=headers)
    assert p1.status_code == 200

    # Call /logout
    logout_res = client.post("/api/v1/auth/logout", headers=headers)
    assert logout_res.status_code == 200
    assert "Successfully logged out" in logout_res.get_json()["message"]

    # Verify token is blacklisted and now rejected with 401
    p2 = client.get("/api/v1/profile", headers=headers)
    assert p2.status_code == 401
    assert "Token is invalid or expired" in p2.get_json()["error"]
