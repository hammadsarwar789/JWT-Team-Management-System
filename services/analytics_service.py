from collections import Counter
from extensions import fellows_collection
from models.user import UserRole


def get_analytics_summary(user_oid, user_role=None):
    """Aggregate relationship breakdown, domain distributions, and creation trends."""
    if user_role == UserRole.ADMIN:
        cursor = fellows_collection.find({})
    else:
        cursor = fellows_collection.find({"owner_id": user_oid})

    relation_counter = Counter()
    domain_counter = Counter()
    month_counter = Counter()

    total_count = 0
    for fellow in cursor:
        total_count += 1
        # Relation
        rel = (fellow.get("relation") or "Unspecified").strip().capitalize()
        relation_counter[rel] += 1

        # Email domain
        email = (fellow.get("email") or "").strip()
        if "@" in email:
            domain = email.split("@")[-1].lower()
            domain_counter[domain] += 1
        else:
            domain_counter["no_email"] += 1

        # Created date month
        created_at = fellow.get("created_at")
        if created_at and hasattr(created_at, "strftime"):
            month_key = created_at.strftime("%Y-%m")
            month_counter[month_key] += 1
        else:
            month_counter["Unknown"] += 1

    return {
        "total_contacts": total_count,
        "relations": dict(relation_counter),
        "email_domains": dict(domain_counter),
        "monthly_trends": dict(month_counter),
    }
