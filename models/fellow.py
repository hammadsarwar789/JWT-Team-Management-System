def serialize_fellow(fellow):
    """Serialize MongoDB fellow document to dictionary."""
    if not fellow:
        return None
    created_at = fellow.get("created_at")
    return {
        "id": str(fellow["_id"]),
        "name": fellow["name"],
        "email": fellow.get("email", ""),
        "relation": fellow.get("relation", ""),
        "notes": fellow.get("notes", ""),
        "created_at": created_at.isoformat() if hasattr(created_at, "isoformat") else str(created_at or ""),
        "attachments": fellow.get("attachments", []),
    }

