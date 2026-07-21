import datetime
import os
import uuid
from sqlalchemy import or_, desc, asc
from sqlalchemy.orm.attributes import flag_modified
from werkzeug.utils import secure_filename

from extensions import db
from models.fellow import Fellow, serialize_fellow
from models.user import User, UserRole

ALLOWED_ATTACHMENT_EXTENSIONS = {"pdf", "docx", "txt", "png", "jpg", "jpeg"}


def create_fellow(user_id, cleaned_data):
    """Add a new fellow associated with user_id."""
    owner_id_int = int(user_id)
    fellow = Fellow(
        owner_id=owner_id_int,
        name=cleaned_data["name"],
        email=cleaned_data.get("email", ""),
        relation=cleaned_data.get("relation", ""),
        notes=cleaned_data.get("notes", ""),
        attachments=[],
        created_at=datetime.datetime.now(datetime.timezone.utc),
    )
    db.session.add(fellow)
    db.session.commit()
    return serialize_fellow(fellow)


def get_user_fellows(user_id, query_params=None, user_role=None):
    """Retrieve fellows owned by user_id or ALL system fellows for Admin by default."""
    query_params = query_params or {}

    is_admin = (user_role in (UserRole.ADMIN, "Admin"))
    all_param = str(query_params.get("all", "true" if is_admin else "false")).lower()
    is_admin_all = (is_admin and all_param in ("true", "1"))

    query = Fellow.query

    if not is_admin_all:
        try:
            owner_id_int = int(user_id)
            query = query.filter_by(owner_id=owner_id_int)
        except (ValueError, TypeError):
            pass

    # Search filter (q)
    search_str = str(query_params.get("q", "")).strip()
    if search_str:
        pattern = f"%{search_str}%"
        search_filter = or_(
            Fellow.name.ilike(pattern),
            Fellow.email.ilike(pattern),
            Fellow.relation.ilike(pattern),
            Fellow.notes.ilike(pattern),
        )
        query = query.filter(search_filter)

    # Total count matching filter
    total_count = query.count()

    # Pagination parameters
    try:
        page = max(1, int(query_params.get("page", 1)))
    except (ValueError, TypeError):
        page = 1

    try:
        limit = max(1, min(100, int(query_params.get("limit", 10))))
    except (ValueError, TypeError):
        limit = 10

    offset = (page - 1) * limit
    total_pages = max(1, (total_count + limit - 1) // limit) if total_count > 0 else 1

    # Sorting parameters
    sort_field_name = str(query_params.get("sort", "created_at")).strip()
    if sort_field_name not in ("name", "email", "relation", "created_at"):
        sort_field_name = "created_at"

    order_str = str(query_params.get("order", "desc")).strip().lower()
    sort_column = getattr(Fellow, sort_field_name, Fellow.created_at)

    if order_str in ("asc", "1"):
        query = query.order_by(asc(sort_column))
    else:
        query = query.order_by(desc(sort_column))

    fellows_list = query.offset(offset).limit(limit).all()

    items = []
    owner_cache = {}
    for f in fellows_list:
        serialized = serialize_fellow(f)
        owner_id = f.owner_id
        if owner_id:
            owner_key = str(owner_id)
            if owner_key not in owner_cache:
                u = db.session.get(User, owner_id)
                owner_cache[owner_key] = u.username if u else "Unknown"
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


def update_fellow(fellow_id, user_id, updates, user_role=None):
    """Update a fellow if owned by user_id or if user is Admin."""
    try:
        fellow_id_int = int(fellow_id)
    except (ValueError, TypeError):
        return False, "Fellow not found", None, 404

    fellow = db.session.get(Fellow, fellow_id_int)
    if not fellow:
        return False, "Fellow not found", None, 404

    if user_role != UserRole.ADMIN and str(fellow.owner_id) != str(user_id):
        return False, "Fellow not found", None, 404

    if updates:
        for key, value in updates.items():
            if hasattr(fellow, key) and key not in ("id", "owner_id", "created_at"):
                setattr(fellow, key, value)
        db.session.commit()

    return True, None, serialize_fellow(fellow), 200


def delete_fellow(fellow_id, user_id, user_role=None):
    """Delete a fellow if owned by user_id or if user is Admin."""
    try:
        fellow_id_int = int(fellow_id)
    except (ValueError, TypeError):
        return False, "Fellow not found", 404

    fellow = db.session.get(Fellow, fellow_id_int)
    if not fellow:
        return False, "Fellow not found", 404

    if user_role != UserRole.ADMIN and str(fellow.owner_id) != str(user_id):
        return False, "Fellow not found", 404

    db.session.delete(fellow)
    db.session.commit()
    return True, "Fellow deleted", 200


def add_fellow_attachment(fellow_id, user_id, file_obj, app_root_path, user_role=None):
    """Save an uploaded file attachment to fellow record."""
    try:
        fellow_id_int = int(fellow_id)
    except (ValueError, TypeError):
        return False, "Fellow not found", None, 404

    fellow = db.session.get(Fellow, fellow_id_int)
    if not fellow:
        return False, "Fellow not found", None, 404

    if user_role != UserRole.ADMIN and str(fellow.owner_id) != str(user_id):
        return False, "Fellow not found", None, 404

    if not file_obj or not file_obj.filename:
        return False, "No file provided", None, 400

    filename = secure_filename(file_obj.filename)
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in ALLOWED_ATTACHMENT_EXTENSIONS:
        return False, f"File extension .{ext} not allowed", None, 400

    unique_filename = f"{uuid.uuid4().hex}_{filename}"
    attach_dir = os.path.join(app_root_path, "uploads", "attachments", str(fellow_id))
    os.makedirs(attach_dir, exist_ok=True)
    file_path = os.path.join(attach_dir, unique_filename)
    file_obj.save(file_path)

    relative_url = f"/uploads/attachments/{fellow_id}/{unique_filename}"
    attachment_record = {
        "filename": filename,
        "url": relative_url,
        "uploaded_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }

    current_attachments = list(fellow.attachments or [])
    current_attachments.append(attachment_record)
    fellow.attachments = current_attachments
    flag_modified(fellow, "attachments")
    db.session.commit()

    return True, "Attachment uploaded", serialize_fellow(fellow), 200


def delete_fellow_attachment(fellow_id, user_id, filename, app_root_path, user_role=None):
    """Remove a file attachment from fellow record and delete physical file."""
    try:
        fellow_id_int = int(fellow_id)
    except (ValueError, TypeError):
        return False, "Fellow not found", 404

    fellow = db.session.get(Fellow, fellow_id_int)
    if not fellow:
        return False, "Fellow not found", 404

    if user_role != UserRole.ADMIN and str(fellow.owner_id) != str(user_id):
        return False, "Fellow not found", 404

    attachments = list(fellow.attachments or [])
    target = None
    new_attachments = []
    for att in attachments:
        if att.get("filename") == filename:
            target = att
        else:
            new_attachments.append(att)

    if not target:
        return False, "Attachment not found", 404

    fellow.attachments = new_attachments
    flag_modified(fellow, "attachments")
    db.session.commit()

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
