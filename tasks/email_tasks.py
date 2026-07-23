import logging
from tasks.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="send_password_reset_email")
def send_password_reset_email(email: str, reset_token: str):
    """
    Asynchronous Celery task to send password reset email.
    In development/testing, logs the dispatched token.
    """
    logger.info(f"[Celery Worker] Sending password reset email to {email}. Reset Token: {reset_token}")
    print(f"--> [EMAIL TASK] Password reset token for {email}: {reset_token}")
    return {"status": "sent", "email": email, "token": reset_token}


@celery_app.task(name="send_verification_email")
def send_verification_email(email: str, verification_token: str):
    """
    Asynchronous Celery task to send account verification email.
    """
    logger.info(f"[Celery Worker] Sending verification email to {email}. Verification Token: {verification_token}")
    print(f"--> [EMAIL TASK] Verification token for {email}: {verification_token}")
    return {"status": "sent", "email": email, "token": verification_token}
