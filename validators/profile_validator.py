def validate_profile_update(data):
    """Validate profile update payload."""
    data = data or {}
    updates = {k: data[k] for k in ("username", "full_name", "bio") if k in data}

    if "username" in updates and not str(updates["username"]).strip():
        return False, "Username cannot be empty", None

    if not updates:
        return False, "No valid fields to update", None

    return True, None, updates


def validate_fellow_payload(data):
    """Validate fellow payload."""
    data = data or {}
    name = str(data.get("name", "")).strip()

    if not name:
        return False, "name is required", None

    cleaned_data = {
        "name": name,
        "email": str(data.get("email", "")).strip(),
        "relation": str(data.get("relation", "")).strip(),
        "notes": str(data.get("notes", "")).strip(),
    }
    return True, None, cleaned_data
