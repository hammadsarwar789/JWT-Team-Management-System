import datetime
from extensions import fellows_collection, users_collection
from models.fellow import serialize_fellow
from models.user import UserRole



def create_fellow(user_oid, cleaned_data):
    """Add a new fellow associated with user_oid."""
    fellow = {
        "owner_id": user_oid,
        "name": cleaned_data["name"],
        "email": cleaned_data.get("email", ""),
        "relation": cleaned_data.get("relation", ""),
        "notes": cleaned_data.get("notes", ""),
        "created_at": datetime.datetime.now(datetime.timezone.utc),
    }
    result = fellows_collection.insert_one(fellow)
    fellow["_id"] = result.inserted_id
    return serialize_fellow(fellow)


def get_user_fellows(user_oid, query_params=None, user_role=None):
    """Retrieve fellows owned by user_oid or ALL system fellows for Admin by default."""
    query_params = query_params or {}

    is_admin = (user_role in (UserRole.ADMIN, "Admin"))
    all_param = str(query_params.get("all", "true" if is_admin else "false")).lower()
    is_admin_all = (is_admin and all_param in ("true", "1"))

    if is_admin_all:
        filter_query = {}
    else:
        filter_query = {"owner_id": user_oid}

    # Search filter (q)
    search_str = str(query_params.get("q", "")).strip()
    if search_str:
        regex_pattern = {"$regex": search_str, "$options": "i"}
        search_or = [
            {"name": regex_pattern},
            {"email": regex_pattern},
            {"relation": regex_pattern},
            {"notes": regex_pattern},
        ]
        if is_admin_all:
            filter_query["$or"] = search_or
        else:
            filter_query["$and"] = [{"owner_id": user_oid}, {"$or": search_or}]

    # Total count matching filter
    total_count = fellows_collection.count_documents(filter_query)

    # Pagination parameters
    try:
        page = max(1, int(query_params.get("page", 1)))
    except (ValueError, TypeError):
        page = 1

    try:
        limit = max(1, min(100, int(query_params.get("limit", 10))))
    except (ValueError, TypeError):
        limit = 10

    skip = (page - 1) * limit
    total_pages = max(1, (total_count + limit - 1) // limit) if total_count > 0 else 1

    # Sorting parameters
    sort_field = str(query_params.get("sort", "created_at")).strip()
    if sort_field not in ("name", "email", "relation", "created_at"):
        sort_field = "created_at"

    order_str = str(query_params.get("order", "desc")).strip().lower()
    sort_direction = 1 if order_str in ("asc", "1") else -1

    cursor = fellows_collection.find(filter_query).sort(sort_field, sort_direction).skip(skip).limit(limit)

    items = []
    # Cache user names for owner lookup
    owner_cache = {}
    for f in cursor:
        serialized = serialize_fellow(f)
        owner_id = f.get("owner_id")
        if owner_id:
            owner_key = str(owner_id)
            if owner_key not in owner_cache:
                u = users_collection.find_one({"_id": owner_id})
                owner_cache[owner_key] = u.get("username", "Unknown") if u else "Unknown"
            serialized["owner_name"] = owner_cache[owner_key]
        items.append(serialized)

    return {
        "items": items,
        "total": total_count,
        "page": page,
        "limit": limit,
        "pages": total_pages,
        "is_admin_all": is_admin_all,
    }



def update_fellow(fellow_oid, user_oid, updates, user_role=None):
    """Update a fellow if owned by user_oid or if user is Admin."""
    if user_role == UserRole.ADMIN:
        query = {"_id": fellow_oid}
    else:
        query = {"_id": fellow_oid, "owner_id": user_oid}

    fellow = fellows_collection.find_one(query)
    if not fellow:
        return False, "Fellow not found", None, 404

    if updates:
        fellows_collection.update_one({"_id": fellow_oid}, {"$set": updates})

    updated_fellow = fellows_collection.find_one({"_id": fellow_oid})
    return True, None, serialize_fellow(updated_fellow), 200


def delete_fellow(fellow_oid, user_oid, user_role=None):
    """Delete a fellow if owned by user_oid or if user is Admin."""
    if user_role == UserRole.ADMIN:
        query = {"_id": fellow_oid}
    else:
        query = {"_id": fellow_oid, "owner_id": user_oid}

    result = fellows_collection.delete_one(query)
    if result.deleted_count == 0:
        return False, "Fellow not found", 404
    return True, "Fellow deleted", 200


import os
import uuid
from werkzeug.utils import secure_filename

ALLOWED_ATTACHMENT_EXTENSIONS = {"pdf", "docx", "txt", "png", "jpg", "jpeg"}


def add_fellow_attachment(fellow_oid, user_oid, file_obj, app_root_path, user_role=None):
    """Save an uploaded file attachment to fellow document."""
    if user_role == UserRole.ADMIN:
        query = {"_id": fellow_oid}
    else:
        query = {"_id": fellow_oid, "owner_id": user_oid}

    fellow = fellows_collection.find_one(query)
    if not fellow:
        return False, "Fellow not found", None, 404

    if not file_obj or not file_obj.filename:
        return False, "No file provided", None, 400

    filename = secure_filename(file_obj.filename)
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in ALLOWED_ATTACHMENT_EXTENSIONS:
        return False, f"File extension .{ext} not allowed", None, 400

    unique_filename = f"{uuid.uuid4().hex}_{filename}"
    attach_dir = os.path.join(app_root_path, "uploads", "attachments", str(fellow_oid))
    os.makedirs(attach_dir, exist_ok=True)
    file_path = os.path.join(attach_dir, unique_filename)
    file_obj.save(file_path)

    relative_url = f"/uploads/attachments/{fellow_oid}/{unique_filename}"
    attachment_record = {
        "filename": filename,
        "url": relative_url,
        "uploaded_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }

    fellows_collection.update_one(
        {"_id": fellow_oid},
        {"$push": {"attachments": attachment_record}}
    )

    updated_fellow = fellows_collection.find_one({"_id": fellow_oid})
    return True, "Attachment uploaded", serialize_fellow(updated_fellow), 200


def delete_fellow_attachment(fellow_oid, user_oid, filename, app_root_path, user_role=None):
    """Remove a file attachment from fellow document and delete physical file."""
    if user_role == UserRole.ADMIN:
        query = {"_id": fellow_oid}
    else:
        query = {"_id": fellow_oid, "owner_id": user_oid}

    fellow = fellows_collection.find_one(query)
    if not fellow:
        return False, "Fellow not found", 404

    attachments = fellow.get("attachments", [])
    target = None
    for att in attachments:
        if att.get("filename") == filename:
            target = att
            break

    if not target:
        return False, "Attachment not found", 404

    # Remove from MongoDB
    fellows_collection.update_one(
        {"_id": fellow_oid},
        {"$pull": {"attachments": {"filename": filename}}}
    )

    # Delete disk file if exists
    try:
        url = target.get("url", "")
        if url.startswith("/uploads/"):
            rel_path = url[len("/uploads/"):].replace("/", os.sep)
            full_path = os.path.join(app_root_path, "uploads", rel_path)
            if os.path.exists(full_path):
                os.remove(full_path)
    except Exception:
        pass

    return True, "Attachment deleted", 200



