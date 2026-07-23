import json
from functools import wraps
from flask import request, jsonify
from extensions import redis_client


def cache_get(key: str):
    """Retrieve and deserialize cached JSON data by key."""
    try:
        data = redis_client.get(key)
        if data:
            if isinstance(data, bytes):
                data = data.decode("utf-8")
            return json.loads(data)
    except Exception:
        pass
    return None


def cache_set(key: str, data, ttl: int = 300):
    """Serialize and store data in Redis with TTL (default 300s / 5min)."""
    try:
        serialized = json.dumps(data)
        redis_client.set(key, serialized, ex=ttl)
        return True
    except Exception:
        return False


def cache_delete_pattern(pattern: str):
    """Invalidate all Redis cache keys matching pattern."""
    try:
        keys = redis_client.keys(pattern)
        if keys:
            key_strings = [k.decode("utf-8") if isinstance(k, bytes) else k for k in keys]
            redis_client.delete(*key_strings)
            return len(key_strings)
    except Exception:
        pass
    return 0


from flask import request, jsonify, make_response


def cache_endpoint(ttl: int = 300, key_prefix: str = "view"):
    """
    Decorator for Flask routes to cache GET responses in Redis.
    Uses request path, query string, and authenticated user_id as cache key.
    """
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if request.method != "GET":
                return f(*args, **kwargs)

            user_id = getattr(request, "user_id", "public")
            query_str = request.query_string.decode("utf-8")
            cache_key = f"cache:{key_prefix}:{request.path}:{user_id}:{query_str}"

            cached_data = cache_get(cache_key)
            if cached_data is not None:
                response = jsonify(cached_data)
                response.headers["X-Cache"] = "HIT"
                return response

            res = f(*args, **kwargs)
            resp = make_response(res)

            if resp.status_code == 200:
                try:
                    json_data = resp.get_json(silent=True)
                    if json_data is not None:
                        cache_set(cache_key, json_data, ttl=ttl)
                        resp.headers["X-Cache"] = "MISS"
                except Exception:
                    pass
            return resp
        return decorated
    return decorator


