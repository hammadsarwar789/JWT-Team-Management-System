from validators.schemas import (
    ProfileUpdateSchema,
    FellowSchema,
    validate_with_pydantic,
)


def validate_profile_update(data):
    """Validate profile update payload using Pydantic."""
    data = data or {}
    updates = {k: data[k] for k in ("username", "full_name", "bio") if k in data}

    if not updates:
        return False, "No valid fields to update", None

    is_valid, err_msg, cleaned = validate_with_pydantic(ProfileUpdateSchema, updates)
    if not is_valid:
        if "empty" in (err_msg or "").lower() or "username" in (err_msg or "").lower():
            err_msg = "Username cannot be empty"
        return False, err_msg, None

    cleaned_updates = {k: v for k, v in cleaned.items() if v is not None}
    if not cleaned_updates:
        return False, "No valid fields to update", None

    return True, None, cleaned_updates


def validate_fellow_payload(data):
    """Validate fellow payload using Pydantic FellowSchema."""
    is_valid, err_msg, cleaned = validate_with_pydantic(FellowSchema, data or {})
    if not is_valid:
        return False, "name is required", None
    return True, None, cleaned

