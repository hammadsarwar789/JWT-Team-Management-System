import datetime
from extensions import db
from models.user import User, serialize_user, UserRole
from models.fellow import Fellow


def get_dashboard_stats(user_id):
    """Compute and return dashboard statistics for the user."""
    try:
        user_id_int = int(user_id)
    except (ValueError, TypeError):
        return False, "User not found", None, 404

    user = db.session.get(User, user_id_int)
    if not user:
        return False, "User not found", None, 404

    # Total fellows count
    total_fellows = Fellow.query.filter_by(owner_id=user_id_int).count()

    # Recent fellows added in last 7 days
    seven_days_ago = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=7)
    recent_fellows = Fellow.query.filter(
        Fellow.owner_id == user_id_int,
        Fellow.created_at >= seven_days_ago
    ).count()

    # Profile completeness score
    fields_checked = [user.username, user.email, user.full_name, user.bio, user.profile_picture]
    completed_fields = sum(1 for field in fields_checked if field)
    completeness_pct = int((completed_fields / len(fields_checked)) * 100)

    stats = {
        "user": serialize_user(user),
        "total_fellows": total_fellows,
        "recent_fellows_7d": recent_fellows,
        "profile_completeness_pct": completeness_pct,
        "is_verified": bool(user.is_verified),
        "role": user.role or UserRole.USER,
    }

    return True, None, stats, 200
