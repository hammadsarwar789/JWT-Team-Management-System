from flask import Blueprint, request, jsonify

from middleware.auth import token_required, role_required, parse_oid
from validators.profile_validator import validate_profile_update, validate_fellow_payload
import services.profile_service as profile_service
import services.fellow_service as fellow_service
import services.dashboard_service as dashboard_service
import services.audit_service as audit_service
from services.audit_service import log_event
from models.user import UserRole

profile_bp = Blueprint("profile", __name__)


# ---------- Profile ----------

@profile_bp.route("/profile", methods=["GET"])
@token_required
def get_profile():
    user_oid = getattr(request, "user_oid", None) or parse_oid(request.user_id)
    if not user_oid:
        return jsonify({"error": "Invalid user id"}), 400

    success, msg, profile, status_code = profile_service.get_user_profile(user_oid)
    if not success:
        return jsonify({"error": msg}), status_code

    return jsonify(profile), status_code


@profile_bp.route("/profile", methods=["PUT"])
@token_required
def edit_profile():
    user_oid = getattr(request, "user_oid", None) or parse_oid(request.user_id)
    if not user_oid:
        return jsonify({"error": "Invalid user id"}), 400

    data = request.get_json(silent=True)
    is_valid, error_msg, updates = validate_profile_update(data)
    if not is_valid:
        return jsonify({"error": error_msg}), 400

    success, msg, profile, status_code = profile_service.update_user_profile(user_oid, updates)
    if not success:
        return jsonify({"error": msg}), status_code

    return jsonify(profile), status_code


@profile_bp.route("/profile/picture", methods=["POST"])
@token_required
def upload_picture():
    user_oid = getattr(request, "user_oid", None) or parse_oid(request.user_id)
    if not user_oid:
        return jsonify({"error": "Invalid user id"}), 400

    if "picture" not in request.files and "file" not in request.files:
        return jsonify({"error": "No picture or file part in request"}), 400

    file_obj = request.files.get("picture") or request.files.get("file")
    from flask import current_app
    success, msg, profile, status_code = profile_service.upload_profile_picture(
        user_oid, file_obj, current_app.root_path
    )
    if not success:
        return jsonify({"error": msg}), status_code

    return jsonify({"message": msg, "user": profile}), status_code



# ---------- Admin Role Management ----------

from middleware.auth import role_required
from models.user import UserRole


@profile_bp.route("/admin/users/<user_id>/role", methods=["PUT"])
@token_required
@role_required(UserRole.ADMIN)
def change_user_role(user_id):
    target_oid = parse_oid(user_id)
    if not target_oid:
        return jsonify({"error": "Invalid user id"}), 400

    data = request.get_json(silent=True) or {}
    new_role = data.get("role")
    if not new_role:
        return jsonify({"error": "role is required"}), 400

    success, msg, user_data, status_code = profile_service.update_user_role(target_oid, new_role)
    if not success:
        return jsonify({"error": msg}), status_code

    log_event(request.user_id, "USER_ROLE_UPDATED", {"target_user_id": user_id, "new_role": new_role}, request.remote_addr)
    return jsonify({"message": msg, "user": user_data}), status_code


from services.cache_service import cache_endpoint, cache_delete_pattern


@profile_bp.route("/admin/audit-logs", methods=["GET"])
@token_required
@role_required(UserRole.ADMIN)
@cache_endpoint(ttl=300, key_prefix="audit_logs")
def get_audit_logs():
    result = audit_service.get_audit_logs(request.args)
    return jsonify(result), 200




# ---------- Dashboard Analytics ----------

import services.dashboard_service as dashboard_service


@profile_bp.route("/dashboard/stats", methods=["GET"])
@token_required
@cache_endpoint(ttl=300, key_prefix="dashboard")
def get_dashboard():
    user_oid = getattr(request, "user_oid", None) or parse_oid(request.user_id)
    if not user_oid:
        return jsonify({"error": "Invalid user id"}), 400

    success, msg, stats, status_code = dashboard_service.get_dashboard_stats(user_oid)
    if not success:
        return jsonify({"error": msg}), status_code

    return jsonify(stats), status_code


# ---------- Fellows (people the signed-in user has added) ----------

@profile_bp.route("/fellows", methods=["POST"])
@token_required
def add_fellow():
    user_oid = getattr(request, "user_oid", None) or parse_oid(request.user_id)
    if not user_oid:
        return jsonify({"error": "Invalid user id"}), 400

    data = request.get_json(silent=True)
    is_valid, error_msg, cleaned_data = validate_fellow_payload(data)
    if not is_valid:
        return jsonify({"error": error_msg}), 400

    fellow = fellow_service.create_fellow(user_oid, cleaned_data)
    cache_delete_pattern(f"cache:*:{request.user_id}:*")
    return jsonify(fellow), 201


@profile_bp.route("/fellows", methods=["GET"])
@token_required
@cache_endpoint(ttl=300, key_prefix="fellows")
def list_fellows():
    user_oid = getattr(request, "user_oid", None) or parse_oid(request.user_id)
    if not user_oid:
        return jsonify({"error": "Invalid user id"}), 400

    user_role = getattr(request, "user_role", None)
    result = fellow_service.get_user_fellows(user_oid, request.args, user_role=user_role)
    return jsonify(result), 200


@profile_bp.route("/fellows/<fellow_id>", methods=["PUT"])
@token_required
def edit_fellow(fellow_id):
    user_oid = getattr(request, "user_oid", None) or parse_oid(request.user_id)
    if not user_oid:
        return jsonify({"error": "Invalid user id"}), 400

    oid = parse_oid(fellow_id)
    if not oid:
        return jsonify({"error": "Invalid fellow id"}), 400

    data = request.get_json(silent=True) or {}
    updates = {k: data[k] for k in ("name", "email", "relation", "notes") if k in data}

    user_role = getattr(request, "user_role", None)
    success, msg, fellow, status_code = fellow_service.update_fellow(oid, user_oid, updates, user_role=user_role)
    if not success:
        return jsonify({"error": msg}), status_code

    cache_delete_pattern(f"cache:*:{request.user_id}:*")
    return jsonify(fellow), status_code


@profile_bp.route("/fellows/<fellow_id>", methods=["DELETE"])
@token_required
def delete_fellow(fellow_id):
    user_oid = getattr(request, "user_oid", None) or parse_oid(request.user_id)
    if not user_oid:
        return jsonify({"error": "Invalid user id"}), 400

    oid = parse_oid(fellow_id)
    if not oid:
        return jsonify({"error": "Invalid fellow id"}), 400

    user_role = getattr(request, "user_role", None)
    success, msg, status_code = fellow_service.delete_fellow(oid, user_oid, user_role=user_role)
    if not success:
        return jsonify({"error": msg}), status_code

    cache_delete_pattern(f"cache:*:{request.user_id}:*")
    return jsonify({"message": msg}), status_code



from flask import Response, current_app

import services.import_export_service as import_export_service
import services.analytics_service as analytics_service


@profile_bp.route("/fellows/export", methods=["GET"])
@token_required
def export_fellows():
    user_oid = getattr(request, "user_oid", None) or parse_oid(request.user_id)
    if not user_oid:
        return jsonify({"error": "Invalid user id"}), 400

    format_type = request.args.get("format", "csv")
    user_role = getattr(request, "user_role", None)

    content, mime_type, filename = import_export_service.export_user_fellows(
        user_oid, format_type=format_type, user_role=user_role
    )

    return Response(
        content,
        mimetype=mime_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@profile_bp.route("/fellows/import", methods=["POST"])
@token_required
def import_fellows():
    user_oid = getattr(request, "user_oid", None) or parse_oid(request.user_id)
    if not user_oid:
        return jsonify({"error": "Invalid user id"}), 400

    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file_obj = request.files["file"]
    if not file_obj or not file_obj.filename:
        return jsonify({"error": "No file selected"}), 400

    success, msg, count = import_export_service.import_user_fellows(user_oid, file_obj, file_obj.filename)
    if not success:
        return jsonify({"error": msg}), 400

    log_event(request.user_id, "FELLOWS_IMPORTED", {"count": count, "filename": file_obj.filename}, request.remote_addr)
    return jsonify({"message": msg, "count": count}), 200


@profile_bp.route("/fellows/<fellow_id>/attachments", methods=["POST"])
@token_required
def add_attachment(fellow_id):
    user_oid = getattr(request, "user_oid", None) or parse_oid(request.user_id)
    if not user_oid:
        return jsonify({"error": "Invalid user id"}), 400

    oid = parse_oid(fellow_id)
    if not oid:
        return jsonify({"error": "Invalid fellow id"}), 400

    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file_obj = request.files["file"]
    user_role = getattr(request, "user_role", None)

    success, msg, fellow, status_code = fellow_service.add_fellow_attachment(
        oid, user_oid, file_obj, current_app.root_path, user_role=user_role
    )

    if not success:
        return jsonify({"error": msg}), status_code

    log_event(request.user_id, "FELLOW_ATTACHMENT_UPLOADED", {"fellow_id": fellow_id, "filename": file_obj.filename}, request.remote_addr)
    return jsonify({"message": msg, "fellow": fellow}), status_code


@profile_bp.route("/fellows/<fellow_id>/attachments/<filename>", methods=["DELETE"])
@token_required
def delete_attachment(fellow_id, filename):
    user_oid = getattr(request, "user_oid", None) or parse_oid(request.user_id)
    if not user_oid:
        return jsonify({"error": "Invalid user id"}), 400

    oid = parse_oid(fellow_id)
    if not oid:
        return jsonify({"error": "Invalid fellow id"}), 400

    user_role = getattr(request, "user_role", None)

    success, msg, status_code = fellow_service.delete_fellow_attachment(
        oid, user_oid, filename, current_app.root_path, user_role=user_role
    )

    if not success:
        return jsonify({"error": msg}), status_code

    log_event(request.user_id, "FELLOW_ATTACHMENT_DELETED", {"fellow_id": fellow_id, "filename": filename}, request.remote_addr)
    return jsonify({"message": msg}), status_code



@profile_bp.route("/analytics/summary", methods=["GET"])
@token_required
def get_analytics():
    user_oid = getattr(request, "user_oid", None) or parse_oid(request.user_id)
    if not user_oid:
        return jsonify({"error": "Invalid user id"}), 400

    user_role = getattr(request, "user_role", None)
    summary = analytics_service.get_analytics_summary(user_oid, user_role=user_role)
    return jsonify(summary), 200




