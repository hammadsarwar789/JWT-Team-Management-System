import csv
import json
import io
import datetime
from extensions import fellows_collection
from models.fellow import serialize_fellow
from models.user import UserRole


def export_user_fellows(user_oid, format_type="csv", user_role=None):
    """Export user's fellows as a CSV string or JSON list."""
    if user_role == UserRole.ADMIN:
        cursor = fellows_collection.find({})
    else:
        cursor = fellows_collection.find({"owner_id": user_oid})

    items = [serialize_fellow(f) for f in cursor]

    if format_type.lower() == "json":
        return json.dumps(items, indent=2), "application/json", "fellows_export.json"

    # CSV Export
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["id", "name", "email", "relation", "notes", "created_at"])

    for item in items:
        writer.writerow([
            item.get("id", ""),
            item.get("name", ""),
            item.get("email", ""),
            item.get("relation", ""),
            item.get("notes", ""),
            item.get("created_at", ""),
        ])

    return output.getvalue(), "text/csv", "fellows_export.csv"


def import_user_fellows(user_oid, file_stream, filename):
    """Import contacts from CSV or JSON file stream into user's fellows."""
    content = file_stream.read()
    if isinstance(content, bytes):
        content = content.decode("utf-8", errors="ignore")

    imported_count = 0
    now = datetime.datetime.now(datetime.timezone.utc)

    if filename.lower().endswith(".json"):
        try:
            data = json.loads(content)
            if not isinstance(data, list):
                return False, "JSON file must contain a list of objects", 0
            for record in data:
                if isinstance(record, dict) and record.get("name"):
                    doc = {
                        "owner_id": user_oid,
                        "name": str(record["name"]).strip(),
                        "email": str(record.get("email", "")).strip(),
                        "relation": str(record.get("relation", "")).strip(),
                        "notes": str(record.get("notes", "")).strip(),
                        "created_at": now,
                    }
                    fellows_collection.insert_one(doc)
                    imported_count += 1
            return True, f"Successfully imported {imported_count} contacts", imported_count
        except Exception as exc:
            return False, f"Invalid JSON format: {exc}", 0

    # Assume CSV
    try:
        csv_reader = csv.DictReader(io.StringIO(content))
        for row in csv_reader:
            name = (row.get("name") or row.get("Name") or "").strip()
            if name:
                doc = {
                    "owner_id": user_oid,
                    "name": name,
                    "email": (row.get("email") or row.get("Email") or "").strip(),
                    "relation": (row.get("relation") or row.get("Relation") or "").strip(),
                    "notes": (row.get("notes") or row.get("Notes") or "").strip(),
                    "created_at": now,
                }
                fellows_collection.insert_one(doc)
                imported_count += 1
        return True, f"Successfully imported {imported_count} contacts", imported_count
    except Exception as exc:
        return False, f"Invalid CSV format: {exc}", 0
