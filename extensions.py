from pymongo import MongoClient
from config import Config

_client = None
_db = None


def get_client():
    global _client
    if _client is None:
        _client = MongoClient(Config.MONGO_URI)
    return _client


def get_db():
    global _db
    if _db is None:
        client = get_client()
        try:
            _db = client.get_default_database()
        except Exception:
            _db = client["jwt_auth_app"]
    return _db


def set_db(database):
    """Override database instance (useful for testing with mongomock)."""
    global _db
    _db = database


class CollectionProxy:
    """Delegates pymongo collection calls to the active db instance dynamically."""

    def __init__(self, collection_name):
        self.collection_name = collection_name

    @property
    def _collection(self):
        return get_db()[self.collection_name]

    def __getattr__(self, name):
        return getattr(self._collection, name)

    def __getitem__(self, item):
        return self._collection[item]


users_collection = CollectionProxy("users")
fellows_collection = CollectionProxy("fellows")
audit_logs_collection = CollectionProxy("audit_logs")


def init_indexes():
    """Create indexes if they don't exist yet. Call this once at app startup
    (see app.py). Kept separate from import so app can boot cleanly."""
    users_collection.create_index("email", unique=True)
    audit_logs_collection.create_index("created_at")


