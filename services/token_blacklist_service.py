import time
from extensions import redis_client

BLACK_LIST_SET_KEY = "jwt_blacklist"


def blacklist_token(jti, expires_in_seconds=86400):
    """Store revoked token ID (jti) in Redis."""
    if not jti:
        return False
    try:
        # Store individual key with expiration for auto-cleanup
        key = f"jwt_blacklist:{jti}"
        redis_client.set(key, "revoked", ex=int(expires_in_seconds))
        # Also add to set for lookup
        redis_client.sadd(BLACK_LIST_SET_KEY, jti)
        return True
    except Exception:
        return False


def is_token_blacklisted(jti):
    """Check if token ID (jti) is in Redis blacklist."""
    if not jti:
        return False
    try:
        key = f"jwt_blacklist:{jti}"
        if redis_client.get(key) is not None:
            return True
        return bool(redis_client.sismember(BLACK_LIST_SET_KEY, jti))
    except Exception:
        return False
