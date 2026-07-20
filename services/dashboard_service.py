import datetime
from extensions import users_collection, fellows_collection
from models.user import serialize_user, UserRole


def get_dashboard_stats(user_oid):
    """Compute and return dashboard statistics for the user."""
    user = users_collection.find_one({"_id": user_oid})
    if not user:
        return False, "User not found", None, 404

    # Total fellows count
    total_fellows = fellows_collection.count_documents({"owner_id": user_oid})

    # Recent fellows added in last 7 days
    seven_days_ago = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=7)
    recent_fellows = fellows_collection.count_documents({
        "owner_id": user_oid,
        "created_at": {"$gte": seven_days_ago}
    })


    # Profile completeness score
    fields_checked = ["username", "email", "full_name", "bio", "profile_picture"]
    completed_fields = sum(1 for field in fields_checked if user.get(field))
    completeness_pct = int((completed_fields / len(fields_checked)) * 100)

    stats = {
        "user": serialize_user(user),
        "total_fellows": total_fellows,
        "recent_fellows_7d": recent_fellows,
        "profile_completeness_pct": completeness_pct,
        "is_verified": bool(user.get("is_verified", False)),
        "role": user.get("role", UserRole.USER),
    }

    return True, None, stats, 200
