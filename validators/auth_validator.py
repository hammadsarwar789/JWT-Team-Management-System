def validate_signup_payload(data):
    """Validate user registration payload."""
    data = data or {}
    username = str(data.get("username", "")).strip()
    email = str(data.get("email", "")).strip().lower()
    password = str(data.get("password", ""))

    if not username or not email or not password:
        return False, "username, email and password are required", None

    if len(password) < 6:
        return False, "password must be at least 6 characters", None

    cleaned_data = {
        "username": username,
        "email": email,
        "password": password,
        "full_name": str(data.get("full_name", "")).strip(),
        "bio": str(data.get("bio", "")).strip(),
        "role": data.get("role"),
    }
    return True, None, cleaned_data


def validate_signin_payload(data):
    """Validate user signin payload."""
    data = data or {}
    email = str(data.get("email", "")).strip().lower()
    password = str(data.get("password", ""))

    if not email or not password:
        return False, "Invalid email or password", None

    return True, None, {"email": email, "password": password}
