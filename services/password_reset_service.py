import datetime
from werkzeug.security import generate_password_hash

from extensions import db
from auth.utils import generate_token, decode_token
from models.user import User


from sqlalchemy import func


def request_password_reset(email):
    """Generate a password reset token for the given email and save it to DB."""
    if not email:
        return False, "Email is required", None, 400

    clean_email = email.strip().lower()
    user = User.query.filter(func.lower(User.email) == clean_email).first()
    if not user:
        # Avoid user enumeration by returning general success message
        return True, "If an account with that email exists, a password reset token has been created.", None, 200


    expires_delta = datetime.timedelta(hours=1)
    reset_token = generate_token(
        user.id,
        token_type="reset",
        expires_delta=expires_delta
    )

    user.reset_token = reset_token
    user.reset_token_expires_at = datetime.datetime.now(datetime.timezone.utc) + expires_delta
    db.session.commit()

    # Dispatch Celery background task
    try:
        from tasks.email_tasks import send_password_reset_email
        send_password_reset_email.delay(user.email, reset_token)
    except Exception:
        pass

    return True, "Password reset token created", {"reset_token": reset_token}, 200


def confirm_password_reset(reset_token, new_password):
    """Verify reset token, update password, and clear reset token from DB."""
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
    user.reset_token = None
    user.reset_token_expires_at = None
    db.session.commit()

    return True, "Password updated successfully", 200


def generate_verification_token(user_id):
    """Generate email verification token and save to DB."""
    token = generate_token(
        user_id,
        token_type="verify_email",
        expires_delta=datetime.timedelta(days=1)
    )

    try:
        user_id_int = int(user_id)
        user = db.session.get(User, user_id_int)
        if user:
            user.verification_token = token
            db.session.commit()
            try:
                from tasks.email_tasks import send_verification_email
                send_verification_email.delay(user.email, token)
            except Exception:
                pass
    except (ValueError, TypeError):
        pass

    return token


def verify_user_email(verification_token):
    """Verify user email using token and clear verification token from DB."""
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
    user.verification_token = None
    db.session.commit()

    return True, "Email verified successfully", 200

