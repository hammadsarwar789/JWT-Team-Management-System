import datetime
from sqlalchemy import desc
from extensions import db
from models.audit_log import AuditLog
from models.user import User


def log_event(user_id, action, details=None, ip_address=None):
    """Record a system audit event in SQL database."""
    username = "Anonymous / System"

    if user_id:
        try:
            user_id_int = int(user_id)
            user_obj = db.session.get(User, user_id_int)
            if user_obj:
                username = user_obj.username
        except (ValueError, TypeError):
            pass

    log_entry = AuditLog(
        user_id=str(user_id) if user_id else None,
        username=username,
        action=action,
        details=details or {},
        ip_address=ip_address,
        created_at=datetime.datetime.now(datetime.timezone.utc),
    )

    db.session.add(log_entry)
    db.session.commit()
    return log_entry.to_dict()


def get_audit_logs(query_params=None):
    """Retrieve audit logs with optional filtering and pagination (Admin only)."""
    query_params = query_params or {}
    query = AuditLog.query

    action_filter = str(query_params.get("action", "")).strip()
    if action_filter:
        query = query.filter(AuditLog.action.ilike(f"%{action_filter}%"))

    try:
        page = max(1, int(query_params.get("page", 1)))
    except (ValueError, TypeError):
        page = 1

    try:
        limit = max(1, min(100, int(query_params.get("limit", 20))))
    except (ValueError, TypeError):
        limit = 20

    offset = (page - 1) * limit
    total_count = query.count()
    total_pages = max(1, (total_count + limit - 1) // limit) if total_count > 0 else 1

    logs_list = query.order_by(desc(AuditLog.created_at)).offset(offset).limit(limit).all()
    items = [log.to_dict() for log in logs_list]

    return {
        "items": items,
        "total": total_count,
        "page": page,
        "limit": limit,
        "pages": total_pages,
    }
