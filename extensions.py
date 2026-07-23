import time
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class MockRedisClient:
    """In-memory Redis fallback for environments without an active Redis daemon."""
    def __init__(self):
        self._data = {}
        self._sets = {}
        self._expirations = {}

    def _purge_expired(self):
        now = time.time()
        expired = [k for k, exp in self._expirations.items() if exp and exp <= now]
        for k in expired:
            self._data.pop(k, None)
            self._sets.pop(k, None)
            self._expirations.pop(k, None)

    def ping(self):
        return True

    def get(self, name):
        self._purge_expired()
        val = self._data.get(name)
        if isinstance(val, str):
            return val.encode("utf-8")
        return val

    def set(self, name, value, ex=None, px=None):
        self._purge_expired()
        if isinstance(value, bytes):
            value = value.decode("utf-8")
        self._data[name] = str(value)
        if ex:
            self._expirations[name] = time.time() + ex
        elif px:
            self._expirations[name] = time.time() + (px / 1000.0)
        else:
            self._expirations.pop(name, None)
        return True

    def delete(self, *names):
        count = 0
        for name in names:
            if name in self._data or name in self._sets:
                self._data.pop(name, None)
                self._sets.pop(name, None)
                self._expirations.pop(name, None)
                count += 1
        return count

    def sadd(self, name, *values):
        if name not in self._sets:
            self._sets[name] = set()
        added = 0
        for v in values:
            val_str = v.decode("utf-8") if isinstance(v, bytes) else str(v)
            if val_str not in self._sets[name]:
                self._sets[name].add(val_str)
                added += 1
        return added

    def sismember(self, name, value):
        self._purge_expired()
        val_str = value.decode("utf-8") if isinstance(value, bytes) else str(value)
        return val_str in self._sets.get(name, set())

    def keys(self, pattern="*"):
        self._purge_expired()
        import fnmatch
        all_keys = set(self._data.keys()).union(set(self._sets.keys()))
        matching = fnmatch.filter(all_keys, pattern)
        return [k.encode("utf-8") for k in matching]


class ResilientRedis:
    def __init__(self, app=None):
        self._client = None
        if app:
            self.init_app(app)

    def init_app(self, app):
        redis_url = app.config.get("REDIS_URL", "redis://localhost:6379/0")
        try:
            import redis
            client = redis.from_url(redis_url, socket_connect_timeout=1)
            client.ping()
            self._client = client
            app.logger.info("Connected to Redis server successfully.")
        except Exception:
            self._client = MockRedisClient()
            app.logger.info("Redis server unavailable. Fallback to in-memory MockRedisClient.")

    def __getattr__(self, name):
        if self._client is None:
            self._client = MockRedisClient()
        return getattr(self._client, name)


redis_client = ResilientRedis()


def init_db(app):
    """Initialize SQLAlchemy extension, Redis client, and create database tables."""
    db.init_app(app)
    redis_client.init_app(app)
    with app.app_context():
        db.create_all()




