import datetime
from extensions import db


class AuditLog(db.Model):
    __tablename__ = "audit_logs"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(80), nullable=True)
    username = db.Column(db.String(120), default="Anonymous / System")
    action = db.Column(db.String(100), nullable=False)
    details = db.Column(db.JSON, default=dict)
    ip_address = db.Column(db.String(45), nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.datetime.now(datetime.timezone.utc), index=True)

    def to_dict(self):
        created_at_str = self.created_at.isoformat() if self.created_at else ""
        return {
            "id": str(self.id),
            "user_id": self.user_id,
            "username": self.username or "System",
            "action": self.action,
            "details": self.details or {},
            "ip_address": self.ip_address,
            "created_at": created_at_str,
        }
