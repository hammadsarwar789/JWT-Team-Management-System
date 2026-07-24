from flask import Blueprint, request, jsonify, make_response, current_app

from validators.auth_validator import validate_signup_payload, validate_signin_payload
from services.auth_service import register_user, authenticate_user, refresh_access_token
from services.password_reset_service import (
    request_password_reset,
    confirm_password_reset,
    request_verification_email,
    verify_user_email,
)
from services.audit_service import log_event
from services.token_blacklist_service import blacklist_token
from middleware.auth import token_required


auth_bp = Blueprint("auth", __name__)


def _set_refresh_cookie(response, refresh_token):
    """Set HTTP-only refresh_token cookie on Flask response object."""
    if not refresh_token:
        return response
    cookie_secure = current_app.config.get("JWT_COOKIE_SECURE", False)
    cookie_httponly = current_app.config.get("JWT_COOKIE_HTTPONLY", True)
    cookie_samesite = current_app.config.get("JWT_COOKIE_SAMESITE", "Lax")
    response.set_cookie(
        "refresh_token",
        value=refresh_token,
        httponly=cookie_httponly,
        secure=cookie_secure,
        samesite=cookie_samesite,
        max_age=7 * 24 * 3600,  # 7 days
        path="/",
    )
    return response


@auth_bp.route("/signup", methods=["POST"])
def signup():
    data = request.get_json(silent=True)
    is_valid, error_msg, cleaned_data = validate_signup_payload(data)
    if not is_valid:
        return jsonify({"error": error_msg}), 400

    success, msg, tokens, status_code = register_user(cleaned_data)
    if not success:
        log_event(None, "SIGNUP_FAILED", {"email": cleaned_data.get("email"), "reason": msg}, request.remote_addr)
        return jsonify({"error": msg}), status_code

    log_event(cleaned_data["email"], "USER_REGISTERED", {"username": cleaned_data["username"]}, request.remote_addr)

    response_data = {"message": msg}
    refresh_token = None
    if isinstance(tokens, dict):
        response_data.update(tokens)
        if "access_token" in tokens and "token" not in response_data:
            response_data["token"] = tokens["access_token"]
        refresh_token = tokens.get("refresh_token")
    else:
        response_data["token"] = tokens

    resp = make_response(jsonify(response_data), status_code)
    if refresh_token:
        _set_refresh_cookie(resp, refresh_token)
    return resp


@auth_bp.route("/signin", methods=["POST"])
def signin():
    data = request.get_json(silent=True)
    is_valid, error_msg, credentials = validate_signin_payload(data)
    if not is_valid:
        return jsonify({"error": error_msg}), 401

    success, msg, tokens, status_code = authenticate_user(
        credentials["email"], credentials["password"]
    )
    if not success:
        log_event(None, "SIGNIN_FAILED", {"email": credentials["email"]}, request.remote_addr)
        return jsonify({"error": msg}), status_code

    log_event(credentials["email"], "USER_SIGNIN", {"email": credentials["email"]}, request.remote_addr)

    response_data = {"message": msg}
    refresh_token = None
    if isinstance(tokens, dict):
        response_data.update(tokens)
        if "access_token" in tokens and "token" not in response_data:
            response_data["token"] = tokens["access_token"]
        refresh_token = tokens.get("refresh_token")
    else:
        response_data["token"] = tokens

    resp = make_response(jsonify(response_data), status_code)
    if refresh_token:
        _set_refresh_cookie(resp, refresh_token)
    return resp


@auth_bp.route("/refresh", methods=["POST"])
def refresh():
    data = request.get_json(silent=True) or {}
    token_str = (
        request.cookies.get("refresh_token")
        or data.get("refresh_token")
        or request.headers.get("X-Refresh-Token")
    )

    success, msg, tokens, status_code = refresh_access_token(token_str)
    if not success:
        return jsonify({"error": msg}), status_code

    response_data = {"message": msg}
    response_data.update(tokens)

    resp = make_response(jsonify(response_data), status_code)
    refresh_token = tokens.get("refresh_token")
    if refresh_token:
        _set_refresh_cookie(resp, refresh_token)
    return resp


@auth_bp.route("/logout", methods=["POST"])
@token_required
def logout():
    jti = getattr(request, "token_jti", None)
    if jti:
        blacklist_token(jti, expires_in_seconds=86400)

    user_email = getattr(request, "current_user", None)
    email_str = user_email.email if user_email else None
    log_event(email_str, "USER_LOGOUT", {}, request.remote_addr)

    resp = make_response(jsonify({"message": "Successfully logged out"}), 200)
    resp.delete_cookie("refresh_token", path="/")
    return resp


@auth_bp.route("/forgot-password", methods=["POST"])
def forgot_password():
    data = request.get_json(silent=True) or {}
    email = data.get("email")

    success, msg, result_data, status_code = request_password_reset(email)
    if not success:
        return jsonify({"error": msg}), status_code

    log_event(email, "PASSWORD_RESET_REQUESTED", {"email": email}, request.remote_addr)

    res_body = {"message": msg}
    if result_data:
        res_body.update(result_data)

    return jsonify(res_body), status_code


@auth_bp.route("/reset-password", methods=["POST"])
def reset_password():
    data = request.get_json(silent=True) or {}
    reset_token = data.get("reset_token")
    new_password = data.get("new_password")

    success, msg, status_code = confirm_password_reset(reset_token, new_password)
    if not success:
        return jsonify({"error": msg}), status_code

    log_event(None, "PASSWORD_RESET_COMPLETED", {}, request.remote_addr)
    return jsonify({"message": msg}), status_code


@auth_bp.route("/request-verification-email", methods=["POST"])
@token_required
def request_verification_email_route():
    success, msg, result_data, status_code = request_verification_email(request.user_id)
    if not success:
        return jsonify({"error": msg}), status_code

    user_email = getattr(request.current_user, "email", None)
    log_event(user_email, "VERIFICATION_EMAIL_REQUESTED", {}, request.remote_addr)

    res_body = {"message": msg}
    if result_data:
        res_body.update(result_data)

    return jsonify(res_body), status_code


@auth_bp.route("/verify-email", methods=["POST"])
def verify_email():
    data = request.get_json(silent=True) or {}
    verification_token = data.get("verification_token")

    success, msg, status_code = verify_user_email(verification_token)
    if not success:
        return jsonify({"error": msg}), status_code

    log_event(None, "EMAIL_VERIFIED", {}, request.remote_addr)
    return jsonify({"message": msg}), status_code





