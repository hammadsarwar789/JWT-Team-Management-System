import os
from werkzeug.utils import secure_filename
from extensions import db
from models.user import User, serialize_user, UserRole
from validators.file_validator import validate_profile_image


def upload_profile_picture(user_id, file_obj, app_root_path):
    """Save profile picture file and update user record."""
    is_valid, error_msg, ext = validate_profile_image(file_obj)
    if not is_valid:
        return False, error_msg, None, 400

    upload_dir = os.path.join(app_root_path, "uploads", "profile_images")
    os.makedirs(upload_dir, exist_ok=True)

    filename = f"{str(user_id)}{ext}"
    file_path = os.path.join(upload_dir, filename)
    file_obj.save(file_path)

    relative_url = f"/uploads/profile_images/{filename}"

    user = db.session.get(User, user_id)
    if not user:
        return False, "User not found", None, 404

    user.profile_picture = relative_url
    db.session.commit()

    return True, "Profile picture uploaded successfully", serialize_user(user), 200


def get_user_profile(user_id):
    """Retrieve user profile by ID."""
    user = db.session.get(User, user_id)
    if not user:
        return False, "User not found", None, 404
    return True, None, serialize_user(user), 200


def update_user_profile(user_id, updates):
    """Update user profile fields."""
    user = db.session.get(User, user_id)
    if not user:
        return False, "User not found", None, 404

    for key, value in updates.items():
        if hasattr(user, key) and key not in ("id", "password"):
            setattr(user, key, value)

    db.session.commit()
    return True, None, serialize_user(user), 200


def update_user_role(target_user_id, new_role):
    """Update a user's role (Admin privilege)."""
    if new_role not in (UserRole.ADMIN, UserRole.MANAGER, UserRole.USER):
        return False, f"Invalid role. Allowed roles: {', '.join(UserRole.ALL)}", None, 400

    user = db.session.get(User, target_user_id)
    if not user:
        return False, "User not found", None, 404

    user.role = new_role
    db.session.commit()
    return True, f"Role updated to '{new_role}'", serialize_user(user), 200
