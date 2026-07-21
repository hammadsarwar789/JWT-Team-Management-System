import datetime
from extensions import db


class UserRole:
    ADMIN = "Admin"
    MANAGER = "Manager"
    USER = "User"

    ALL = [ADMIN, MANAGER, USER]


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(120), default="")
    bio = db.Column(db.Text, default="")
    role = db.Column(db.String(20), default=UserRole.USER)
    is_verified = db.Column(db.Boolean, default=False)
    verification_token = db.Column(db.String(255), nullable=True)
    reset_token = db.Column(db.String(255), nullable=True)
    reset_token_expires_at = db.Column(db.DateTime(timezone=True), nullable=True)
    profile_picture = db.Column(db.String(255), default="")
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.datetime.now(datetime.timezone.utc))

    fellows = db.relationship("Fellow", backref="owner", lazy=True, cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": str(self.id),
            "username": self.username,
            "email": self.email,
            "full_name": self.full_name or "",
            "bio": self.bio or "",
            "role": self.role or UserRole.USER,
            "is_verified": bool(self.is_verified),
            "profile_picture": self.profile_picture or "",
        }


def serialize_user(user):
    """Serialize user document or ORM instance to dictionary."""
    if not user:
        return None
    if hasattr(user, "to_dict"):
        return user.to_dict()
    if isinstance(user, dict):
        return {
            "id": str(user.get("id") or user.get("_id", "")),
            "username": user.get("username", ""),
            "email": user.get("email", ""),
            "full_name": user.get("full_name", ""),
            "bio": user.get("bio", ""),
            "role": user.get("role", UserRole.USER),
            "is_verified": bool(user.get("is_verified", False)),
            "profile_picture": user.get("profile_picture", ""),
        }
    return None
