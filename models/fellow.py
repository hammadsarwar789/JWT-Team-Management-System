import datetime
from extensions import db


class Fellow(db.Model):
    __tablename__ = "fellows"

    id = db.Column(db.Integer, primary_key=True)
    owner_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), default="")
    relation = db.Column(db.String(100), default="")
    notes = db.Column(db.Text, default="")
    attachments = db.Column(db.JSON, default=list)
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.datetime.now(datetime.timezone.utc))

    def to_dict(self):
        created_at_str = self.created_at.isoformat() if self.created_at else ""
        return {
            "id": str(self.id),
            "owner_id": str(self.owner_id) if self.owner_id else "",
            "name": self.name,
            "email": self.email or "",
            "relation": self.relation or "",
            "notes": self.notes or "",
            "created_at": created_at_str,
            "attachments": self.attachments or [],
        }


def serialize_fellow(fellow):
    """Serialize fellow document or ORM instance to dictionary."""
    if not fellow:
        return None
    if hasattr(fellow, "to_dict"):
        return fellow.to_dict()
    if isinstance(fellow, dict):
        created_at = fellow.get("created_at")
        return {
            "id": str(fellow.get("id") or fellow.get("_id", "")),
            "name": fellow.get("name", ""),
            "email": fellow.get("email", ""),
            "relation": fellow.get("relation", ""),
            "notes": fellow.get("notes", ""),
            "created_at": created_at.isoformat() if hasattr(created_at, "isoformat") else str(created_at or ""),
            "attachments": fellow.get("attachments", []),
        }
    return None
