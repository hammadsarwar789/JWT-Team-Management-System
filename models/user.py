class UserRole:
    ADMIN = "Admin"
    MANAGER = "Manager"
    USER = "User"

    ALL = [ADMIN, MANAGER, USER]


def serialize_user(user):
    """Serialize MongoDB user document to dictionary."""
    if not user:
        return None
    return {
        "id": str(user["_id"]),
        "username": user["username"],
        "email": user["email"],
        "full_name": user.get("full_name", ""),
        "bio": user.get("bio", ""),
        "role": user.get("role", UserRole.USER),
        "is_verified": bool(user.get("is_verified", False)),
        "profile_picture": user.get("profile_picture", ""),
    }

