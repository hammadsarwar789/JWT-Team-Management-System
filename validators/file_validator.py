import os

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024  # 5MB


def validate_profile_image(file_obj):
    """Validate uploaded image file object."""
    if not file_obj or not file_obj.filename:
        return False, "No file provided", None

    filename = file_obj.filename
    ext = os.path.splitext(filename)[1].lower()

    if ext not in ALLOWED_EXTENSIONS:
        return False, f"Invalid file type '{ext}'. Allowed extensions: jpg, jpeg, png, webp", None

    # Check size if available
    file_obj.seek(0, os.SEEK_END)
    file_size = file_obj.tell()
    file_obj.seek(0)

    if file_size > MAX_FILE_SIZE_BYTES:
        return False, "File size exceeds 5MB limit", None

    return True, None, ext
