import datetime
from bson import ObjectId
from extensions import audit_logs_collection, users_collection


def log_event(user_id, action, details=None, ip_address=None):
    """Record a system audit event in MongoDB."""
    user_oid = None
    username = "Anonymous / System"

    if user_id:
        try:
            user_oid = ObjectId(str(user_id))
            user_doc = users_collection.find_one({"_id": user_oid})
            if user_doc:
                username = user_doc.get("username", "Unknown")
        except Exception:
            user_oid = str(user_id)

    event_doc = {
        "user_id": str(user_id) if user_id else None,
        "username": username,
        "action": action,
        "details": details or {},
        "ip_address": ip_address,
        "created_at": datetime.datetime.now(datetime.timezone.utc),
    }

    audit_logs_collection.insert_one(event_doc)
    return event_doc


def get_audit_logs(query_params=None):
    """Retrieve audit logs with optional filtering and pagination (Admin only)."""
    query_params = query_params or {}

    filter_query = {}

    action_filter = str(query_params.get("action", "")).strip()
    if action_filter:
        filter_query["action"] = {"$regex": action_filter, "$options": "i"}

    try:
        page = max(1, int(query_params.get("page", 1)))
    except (ValueError, TypeError):
        page = 1

    try:
        limit = max(1, min(100, int(query_params.get("limit", 20))))
    except (ValueError, TypeError):
        limit = 20

    skip = (page - 1) * limit
    total_count = audit_logs_collection.count_documents(filter_query)
    total_pages = max(1, (total_count + limit - 1) // limit) if total_count > 0 else 1

    cursor = audit_logs_collection.find(filter_query).sort("created_at", -1).skip(skip).limit(limit)

    items = []
    for log in cursor:
        items.append({
            "id": str(log["_id"]),
            "user_id": log.get("user_id"),
            "username": log.get("username", "System"),
            "action": log.get("action"),
            "details": log.get("details", {}),
            "ip_address": log.get("ip_address"),
            "created_at": log["created_at"].isoformat() if isinstance(log.get("created_at"), datetime.datetime) else str(log.get("created_at")),
        })

    return {
        "items": items,
        "total": total_count,
        "page": page,
        "limit": limit,
        "pages": total_pages,
    }
