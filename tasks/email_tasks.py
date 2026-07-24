import logging
import smtplib
from email.message import EmailMessage
from tasks.celery_app import celery_app
from config import Config

logger = logging.getLogger(__name__)


def _send_smtp_email(to_email: str, subject: str, body_text: str, body_html: str = None) -> bool:
    """Helper function to send email via SMTP if credentials are configured."""
    username = (Config.MAIL_USERNAME or "").strip()
    password = (Config.MAIL_PASSWORD or "").replace(" ", "").strip()

    if not username or not password:
        logger.info("[SMTP] MAIL_USERNAME or MAIL_PASSWORD not configured. Skipping SMTP send.")
        return False

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = username
    msg["To"] = to_email
    msg.set_content(body_text)

    if body_html:
        msg.add_alternative(body_html, subtype="html")

    try:
        with smtplib.SMTP(Config.MAIL_SERVER, Config.MAIL_PORT, timeout=10) as server:
            if Config.MAIL_USE_TLS:
                server.starttls()
            server.login(username, password)
            server.send_message(msg)
        logger.info(f"[SMTP] Successfully sent email to {to_email}")
        return True
    except Exception as e:
        logger.error(f"[SMTP ERROR] Failed to send email to {to_email}: {str(e)}")
        return False


@celery_app.task(name="send_password_reset_email")
def send_password_reset_email(email: str, reset_token: str):
    """
    Asynchronous Celery task to send password reset email.
    """
    reset_link = f"{Config.APP_BASE_URL}/reset-password?token={reset_token}"
    subject = "Reset Your Password"
    text_content = f"Please click the link to reset your password: {reset_link}\n\nReset Token: {reset_token}"
    html_content = f"""
    <html>
      <body style="font-family: Arial, sans-serif; color: #333; line-height: 1.6;">
        <div style="max-width: 500px; margin: 0 auto; padding: 20px; border: 1px solid #e0e0e0; border-radius: 8px;">
          <h2 style="color: #2563eb;">Password Reset Request</h2>
          <p>We received a request to reset your password. Click the button below to set a new password:</p>
          <p style="text-align: center; margin: 25px 0;">
            <a href="{reset_link}" style="background-color: #2563eb; color: #ffffff; padding: 12px 24px; text-decoration: none; border-radius: 6px; font-weight: bold; display: inline-block;">Reset Password</a>
          </p>
          <p style="font-size: 0.85rem; color: #666;">Or copy and paste this link in your browser:<br><a href="{reset_link}">{reset_link}</a></p>
          <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
          <p style="font-size: 0.8rem; color: #999;">If you did not request a password reset, you can safely ignore this email.</p>
        </div>
      </body>
    </html>
    """

    logger.info(f"[Celery Worker] Sending password reset email to {email}. Link: {reset_link}")
    print(f"--> [EMAIL TASK] Password reset link for {email}: {reset_link}")

    sent = _send_smtp_email(email, subject, text_content, html_content)
    return {"status": "sent", "smtp_sent": sent, "email": email, "token": reset_token, "link": reset_link}


@celery_app.task(name="send_verification_email")
def send_verification_email(email: str, verification_token: str):
    """
    Asynchronous Celery task to send account verification email.
    """
    verification_link = f"{Config.APP_BASE_URL}/verify-email?token={verification_token}"
    subject = "Verify Your Gmail Address"
    text_content = f"Welcome! Please verify your email address by clicking the link: {verification_link}\n\nVerification Token: {verification_token}"
    html_content = f"""
    <html>
      <body style="font-family: Arial, sans-serif; color: #333; line-height: 1.6;">
        <div style="max-width: 500px; margin: 0 auto; padding: 20px; border: 1px solid #e0e0e0; border-radius: 8px;">
          <h2 style="color: #10b981;">Verify Your Email Address</h2>
          <p>Thank you for registering! Please verify your email address to activate your account and log in.</p>
          <p style="text-align: center; margin: 25px 0;">
            <a href="{verification_link}" style="background-color: #10b981; color: #ffffff; padding: 12px 24px; text-decoration: none; border-radius: 6px; font-weight: bold; display: inline-block;">Verify Email Address</a>
          </p>
          <p style="font-size: 0.85rem; color: #666;">Or copy and paste this link in your browser:<br><a href="{verification_link}">{verification_link}</a></p>
          <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
          <p style="font-size: 0.8rem; color: #999;">If you did not create an account, no further action is required.</p>
        </div>
      </body>
    </html>
    """

    logger.info(f"[Celery Worker] Sending verification email to {email}. Link: {verification_link}")
    print(f"--> [EMAIL TASK] Verification link for {email}: {verification_link}")

    sent = _send_smtp_email(email, subject, text_content, html_content)
    return {"status": "sent", "smtp_sent": sent, "email": email, "token": verification_token, "link": verification_link}


