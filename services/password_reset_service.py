import datetime
from werkzeug.security import generate_password_hash

from extensions import db
from auth.utils import generate_token, decode_token
from models.user import User


def request_password_reset(email):
    """Generate a password reset token for the given email."""
    if not email:
        return False, "Email is required", None, 400

    user = User.query.filter_by(email=email.strip().lower()).first()
    if not user:
        # Avoid user enumeration by returning general success message
        return True, "If an account with that email exists, a password reset token has been created.", None, 200

    # Create 1-hour reset token
    reset_token = generate_token(
        user.id,
        token_type="reset",
        expires_delta=datetime.timedelta(hours=1)
    )

    return True, "Password reset token created", {"reset_token": reset_token}, 200


def confirm_password_reset(reset_token, new_password):
    """Verify reset token and update password."""
    if not reset_token or not new_password:
        return False, "reset_token and new_password are required", 400

    if len(new_password) < 6:
        return False, "Password must be at least 6 characters", 400

    payload = decode_token(reset_token, expected_type="reset")
    if not payload:
        return False, "Reset token is invalid or expired", 401

    user_id = payload.get("sub")
    try:
        user_id_int = int(user_id)
    except (ValueError, TypeError):
        return False, "Invalid user id", 400

    user = db.session.get(User, user_id_int)
    if not user:
        return False, "User not found", 404

    user.password = generate_password_hash(new_password)
    db.session.commit()

    return True, "Password updated successfully", 200


def generate_verification_token(user_id):
    """Generate email verification token."""
    return generate_token(
        user_id,
        token_type="verify_email",
        expires_delta=datetime.timedelta(days=1)
    )


def verify_user_email(verification_token):
    """Verify user email using token."""
    if not verification_token:
        return False, "verification_token is required", 400

    payload = decode_token(verification_token, expected_type="verify_email")
    if not payload:
        payload = decode_token(verification_token, expected_type="access")

    if not payload:
        return False, "Verification token is invalid or expired", 401

    user_id = payload.get("sub")
    try:
        user_id_int = int(user_id)
    except (ValueError, TypeError):
        return False, "Invalid user id", 400

    user = db.session.get(User, user_id_int)
    if not user:
        return False, "User not found", 404

    user.is_verified = True
    db.session.commit()

    return True, "Email verified successfully", 200
