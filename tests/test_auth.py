def test_signup_success(client):
    """Test registering a new user."""
    payload = {
        "username": "alice",
        "email": "alice@example.com",
        "password": "securepassword123",
        "full_name": "Alice Smith",
        "bio": "Developer",
    }
    res = client.post("/api/auth/signup", json=payload)
    assert res.status_code == 201
    data = res.get_json()
    assert data["message"] == "Account created"
    assert "token" in data


def test_signup_missing_fields(client):
    """Test signup validation for missing required fields."""
    res = client.post("/api/auth/signup", json={"email": "incomplete@example.com"})
    assert res.status_code == 400
    assert "username, email and password are required" in res.get_json()["error"]


def test_signup_short_password(client):
    """Test signup validation for passwords under 6 characters."""
    payload = {
        "username": "bob",
        "email": "bob@example.com",
        "password": "123",
    }
    res = client.post("/api/auth/signup", json=payload)
    assert res.status_code == 400
    assert "password must be at least 6 characters" in res.get_json()["error"]


def test_signup_duplicate_email(client):
    """Test signup with an email that is already registered."""
    payload = {
        "username": "charlie",
        "email": "charlie@example.com",
        "password": "password123",
    }
    res1 = client.post("/api/auth/signup", json=payload)
    assert res1.status_code == 201

    res2 = client.post("/api/auth/signup", json=payload)
    assert res2.status_code == 409
    assert "Email already registered" in res2.get_json()["error"]


def test_signin_success(client):
    """Test signin with valid credentials."""
    signup_payload = {
        "username": "dave",
        "email": "dave@example.com",
        "password": "mypassword123",
    }
    client.post("/api/auth/signup", json=signup_payload)

    signin_payload = {
        "email": "dave@example.com",
        "password": "mypassword123",
    }
    res = client.post("/api/auth/signin", json=signin_payload)
    assert res.status_code == 200
    data = res.get_json()
    assert data["message"] == "Signed in"
    assert "token" in data


def test_signin_invalid_credentials(client):
    """Test signin with wrong password or unregistered email."""
    # Non-existent email
    res1 = client.post("/api/auth/signin", json={"email": "nobody@example.com", "password": "pass"})
    assert res1.status_code == 401
    assert "Invalid email or password" in res1.get_json()["error"]

    # Wrong password
    client.post("/api/auth/signup", json={"username": "eve", "email": "eve@example.com", "password": "correct"})
    res2 = client.post("/api/auth/signin", json={"email": "eve@example.com", "password": "wrong"})
    assert res2.status_code == 401
    assert "Invalid email or password" in res2.get_json()["error"]
