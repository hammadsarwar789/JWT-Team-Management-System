import os
from werkzeug.utils import secure_filename
from extensions import users_collection
from models.user import serialize_user, UserRole
from validators.file_validator import validate_profile_image


def upload_profile_picture(user_oid, file_obj, app_root_path):
    """Save profile picture file and update user document."""
    is_valid, error_msg, ext = validate_profile_image(file_obj)
    if not is_valid:
        return False, error_msg, None, 400

    upload_dir = os.path.join(app_root_path, "uploads", "profile_images")
    os.makedirs(upload_dir, exist_ok=True)

    filename = f"{str(user_oid)}{ext}"
    file_path = os.path.join(upload_dir, filename)
    file_obj.save(file_path)

    relative_url = f"/uploads/profile_images/{filename}"
    users_collection.update_one({"_id": user_oid}, {"$set": {"profile_picture": relative_url}})

    user = users_collection.find_one({"_id": user_oid})
    return True, "Profile picture uploaded successfully", serialize_user(user), 200



def get_user_profile(user_oid):
    """Retrieve user profile by ObjectId."""
    user = users_collection.find_one({"_id": user_oid})
    if not user:
        return False, "User not found", None, 404
    return True, None, serialize_user(user), 200


def update_user_profile(user_oid, updates):
    """Update user profile fields."""
    users_collection.update_one({"_id": user_oid}, {"$set": updates})
    user = users_collection.find_one({"_id": user_oid})
    if not user:
        return False, "User not found", None, 404
    return True, None, serialize_user(user), 200


def update_user_role(target_user_oid, new_role):
    """Update a user's role (Admin privilege)."""
    if new_role not in (UserRole.ADMIN, UserRole.MANAGER, UserRole.USER):
        return False, f"Invalid role. Allowed roles: {', '.join(UserRole.ALL)}", None, 400

    result = users_collection.update_one({"_id": target_user_oid}, {"$set": {"role": new_role}})
    if result.matched_count == 0:
        return False, "User not found", None, 404

    user = users_collection.find_one({"_id": target_user_oid})
    return True, f"Role updated to '{new_role}'", serialize_user(user), 200

