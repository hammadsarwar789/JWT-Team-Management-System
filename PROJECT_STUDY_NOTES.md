# 📘 Complete & Exhaustive Beginner's Study Notes: JWT Auth & Team Management System

Welcome! This document is a complete, beginner-friendly walkthrough of the entire **JWT Auth Team Management System** codebase. Every class, data model, validation schema, service function, decorator, and API route is explained line-by-line and block-by-block with code snippets.

---

## 📚 Table of Contents

1. [High-Level Architecture & Tech Stack](#1-high-level-architecture--tech-stack)
2. [Core Configuration & Infrastructure](#2-core-configuration--infrastructure)
   - [2.1 `config.py` — `class Config`](#21-configpy--class-config)
   - [2.2 `extensions.py` — `class ResilientRedis` & `class MockRedisClient`](#22-extensionspy--class-resilientredis--class-mockredisclient)
   - [2.3 `app.py` — Application Factory `create_app()`](#23-apppy--application-factory-create_app)
3. [Database Models (`models/`)](#3-database-models-models)
   - [3.1 `models/user.py` — `class UserRole` & `class User`](#31-modelsuserpy--class-userrole--class-user)
   - [3.2 `models/fellow.py` — `class Fellow`](#32-modelsfellowpy--class-fellow)
   - [3.3 `models/audit_log.py` — `class AuditLog`](#33-modelsaudit_logpy--class-auditlog)
4. [Validation & Data Sanitization Layer (`validators/`)](#4-validation--data-sanitization-layer-validators)
   - [4.1 `validators/schemas.py` — Pydantic v2 Classes](#41-validatorsschemaspy--pydantic-v2-classes)
   - [4.2 Payload Validation Modules (`auth_validator.py`, `profile_validator.py`, `file_validator.py`)](#42-payload-validation-modules)
5. [Authentication, Security & Token Management](#5-authentication-security--token-management)
   - [5.1 `auth/utils.py` — JWT Generation & Verification](#51-authutilspy--jwt-generation--verification)
   - [5.2 `services/token_blacklist_service.py` — Redis Revocation](#52-servicestoken_blacklist_servicepy--redis-revocation)
   - [5.3 `middleware/auth.py` — `@token_required` & `@role_required`](#53-middlewareauthpy--token_required--role_required)
6. [Business Logic & Services Layer (`services/`)](#6-business-logic--services-layer-services)
   - [6.1 `services/auth_service.py`](#61-servicesauth_servicepy)
   - [6.2 `services/cache_service.py` — Redis Endpoint Caching](#62-servicescache_servicepy--redis-endpoint-caching)
   - [6.3 `services/profile_service.py`](#63-servicesprofile_servicepy)
   - [6.4 `services/fellow_service.py`](#64-servicesfellow_servicepy)
   - [6.5 `services/password_reset_service.py`](#65-servicespassword_reset_servicepy)
   - [6.6 `services/audit_service.py`, `dashboard_service.py`, `analytics_service.py`, `import_export_service.py`](#66-other-services)
7. [Asynchronous Background Task Queue (`tasks/`)](#7-asynchronous-background-task-queue-tasks)
   - [7.1 `tasks/celery_app.py` — Celery Configuration](#71-taskscelery_apppy--celery-configuration)
   - [7.2 `tasks/email_tasks.py` — Async Celery Email Tasks](#72-tasksemail_taskspy--async-celery-email-tasks)
8. [API Blueprints & Route Handlers](#8-api-blueprints--route-handlers)
   - [8.1 `auth/routes.py`](#81-authroutespy)
   - [8.2 `profiles/routes.py`](#82-profilesroutespy)
9. [Automated Testing Suite (`tests/`)](#9-automated-testing-suite-tests)

---

## 1. High-Level Architecture & Tech Stack

This project is a RESTful API and Web Application designed to handle user accounts, authentication, security event tracking, contact management, Redis response caching, background tasks, and role-based permissions.

```
                    +-------------------------------------------------+
                    |              Client Browser / HTTP              |
                    +-------------------------------------------------+
                                             |
                                  Authorization Header / Cookie
                                             v
                    +-------------------------------------------------+
                    |           Flask App Factory (app.py)            |
                    +-------------------------------------------------+
                                             |
        +------------------------------------+------------------------------------+
        |                                    |                                    |
        v                                    v                                    v
+---------------+                    +---------------+                    +---------------+
| Auth Blueprint|                    |Profile/Fellows|                    |   Middleware  |
| (/auth/...)   |                    | Blueprint (/) |                    |  Security/RBAC|
+---------------+                    +---------------+                    +---------------+
        |                                    |                                    |
        v                                    v                                    v
+-----------------------------------------------------------------------------------------+
|                                    Services Layer                                       |
|  (auth_service, profile_service, fellow_service, cache_service, password_reset, etc.)  |
+-----------------------------------------------------------------------------------------+
        |                                    |                                    |
        v                                    v                                    v
+---------------+                    +---------------+                    +---------------+
| PostgreSQL DB |                    | Redis Cache & |                    | Celery Async  |
| (SQLAlchemy)  |                    | Token Revocation                  | Workers       |
+---------------+                    +---------------+                    +---------------+
```

---

## 2. Core Configuration & Infrastructure

### 2.1 `config.py` — `class Config`

The `Config` class loads configuration parameters from environment variables (using `python-dotenv`) or provides default values.

```python
import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()  # Reads .env file into os.environ

class Config:
    # 1. Secret key used for signing session cookies and JWT signatures
    SECRET_KEY = os.environ.get("SECRET_KEY", "change-this-in-production")

    # 2. Database URL: Specifies PostgreSQL connection details
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL",
        "postgresql://postgres:postgres@localhost:5432/jwt_auth_app"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False  # Disables overhead event tracking

    # 3. JWT Token Lifespan settings
    JWT_EXPIRES = timedelta(hours=24)         # Default token fallback lifespan
    JWT_ACCESS_EXPIRES = timedelta(minutes=30) # Short-lived access token (30 min)
    JWT_REFRESH_EXPIRES = timedelta(days=7)    # Long-lived refresh token (7 days)

    # 4. HTTP-Only Cookie Security Settings
    JWT_COOKIE_SECURE = os.environ.get("JWT_COOKIE_SECURE", "False").lower() in ("true", "1", "t")
    JWT_COOKIE_HTTPONLY = True  # Prevents JavaScript XSS access to refresh cookie
    JWT_COOKIE_SAMESITE = "Lax" # Protects against CSRF attacks

    # 5. Email Verification Enforcement
    REQUIRE_EMAIL_VERIFICATION = os.environ.get("REQUIRE_EMAIL_VERIFICATION", "True").lower() in ("true", "1", "t")

    # 6. Redis & Celery Connection URLs
    REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
    CELERY_BROKER_URL = REDIS_URL
    CELERY_RESULT_BACKEND = REDIS_URL
    CELERY_TASK_ALWAYS_EAGER = os.environ.get("CELERY_TASK_ALWAYS_EAGER", "False").lower() in ("true", "1", "t")
```

---

### 2.2 `extensions.py` — `class ResilientRedis` & `class MockRedisClient`

To guarantee that the application runs reliably even if a local Redis server daemon is offline, `extensions.py` implements a resilient fallback client class (`ResilientRedis`) and an in-memory dictionary fallback (`MockRedisClient`).

```python
import logging
from flask_sqlalchemy import SQLAlchemy
from redis import Redis, ConnectionError, TimeoutError

# 1. Global SQLAlchemy ORM instance
db = SQLAlchemy()

logger = logging.getLogger(__name__)

class MockRedisClient:
    """In-memory dictionary fallback matching Redis API interface."""
    def __init__(self):
        self._store = {}

    def get(self, key):
        val = self._store.get(key)
        if val is None:
            return None
        return val.encode("utf-8") if isinstance(val, str) else val

    def set(self, key, value, ex=None, px=None, nx=False, xx=False):
        self._store[key] = str(value)
        return True

    def delete(self, *keys):
        count = 0
        for k in keys:
            if k in self._store:
                del self._store[k]
                count += 1
        return count

    def keys(self, pattern="*"):
        import fnmatch
        matched = fnmatch.filter(self._store.keys(), pattern)
        return [k.encode("utf-8") for k in matched]

    def ping(self):
        return True


class ResilientRedis:
    """Wrapper that attempts real Redis operations and catches ConnectionErrors to fallback gracefully."""
    def __init__(self, redis_url="redis://localhost:6379/0"):
        self.real_client = Redis.from_url(redis_url, decode_responses=False)
        self.mock_client = MockRedisClient()

    def _execute(self, method_name, *args, **kwargs):
        try:
            method = getattr(self.real_client, method_name)
            return method(*args, **kwargs)
        except (ConnectionError, TimeoutError, OSError) as err:
            # If real Redis server is unreachable, log warning and use in-memory fallback
            logger.warning(f"Redis unavailable ({err}). Using in-memory fallback client.")
            mock_method = getattr(self.mock_client, method_name)
            return mock_method(*args, **kwargs)

    def get(self, key): return self._execute("get", key)
    def set(self, key, value, ex=None, px=None, nx=False, xx=False): return self._execute("set", key, value, ex=ex, px=px, nx=nx, xx=xx)
    def delete(self, *keys): return self._execute("delete", *keys)
    def keys(self, pattern="*"): return self._execute("keys", pattern)
    def ping(self): return self._execute("ping")


# Initialize global Redis client instance
redis_client = ResilientRedis()
```

---

### 2.3 `app.py` — Application Factory `create_app()`

`app.py` uses the standard Flask **Application Factory Pattern** to instantiate and configure the application.

```python
from flask import Flask, jsonify, request
from sqlalchemy.exc import SQLAlchemyError
from config import Config
from extensions import init_db
from middleware.logger import setup_logger
from middleware.security import setup_security_headers
from auth.routes import auth_bp
from profiles.routes import profile_bp

def create_app(config_class=Config, test_config=None):
    app = Flask(__name__)
    app.config.from_object(config_class)
    if test_config:
        app.config.update(test_config)

    # Attach structured file logging & security HTTP headers
    setup_logger(app)
    setup_security_headers(app)

    # Initialize PostgreSQL ORM database tables
    init_db(app)

    # Register API Blueprints with route prefixes
    app.register_blueprint(auth_bp, url_prefix="/api/v1/auth")
    app.register_blueprint(profile_bp, url_prefix="/api/v1")

    # Legacy URL aliases for backwards compatibility
    app.register_blueprint(auth_bp, url_prefix="/api/auth", name="auth_legacy")
    app.register_blueprint(profile_bp, url_prefix="/api", name="profile_legacy")

    # Global Database Error Exception Handler
    @app.errorhandler(SQLAlchemyError)
    def handle_db_error(error):
        app.logger.error(f"Database Error: {str(error)}")
        return jsonify({"error": "Database error occurred", "details": str(error)}), 503

    return app
```

---

## 3. Database Models (`models/`)

### 3.1 `models/user.py` — `class UserRole` & `class User`

This module defines system user roles and the primary `User` ORM model stored in PostgreSQL.

```python
import datetime
from extensions import db

class UserRole:
    """Constants defining available user roles in the system."""
    ADMIN = "Admin"
    MANAGER = "Manager"
    USER = "User"
    ALL = [ADMIN, MANAGER, USER]


class User(db.Model):
    """User database model representing account credentials and profile state."""
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password = db.Column(db.String(255), nullable=False) # Hashed password string
    full_name = db.Column(db.String(120), default="")
    bio = db.Column(db.Text, default="")
    role = db.Column(db.String(20), default=UserRole.USER, nullable=False)
    is_verified = db.Column(db.Boolean, default=False, nullable=False)
    reset_token = db.Column(db.String(255), nullable=True)
    reset_token_expires_at = db.Column(db.DateTime, nullable=True)
    verification_token = db.Column(db.String(255), nullable=True)
    profile_picture = db.Column(db.String(255), default="")
    created_at = db.Column(db.DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))

    # One-to-Many Relationship: Delete user -> cascade delete all associated fellows
    fellows = db.relationship("Fellow", backref="owner", lazy=True, cascade="all, delete-orphan")


def serialize_user(user):
    """Converts User ORM instance into a JSON-serializable dictionary."""
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "full_name": user.full_name,
        "bio": user.bio,
        "role": user.role,
        "is_verified": user.is_verified,
        "profile_picture": user.profile_picture,
        "created_at": user.created_at.isoformat() if user.created_at else None,
    }
```

---

### 3.2 `models/fellow.py` — `class Fellow`

The `Fellow` model represents contacts linked to a specific user account.

```python
import datetime
from extensions import db

class Fellow(db.Model):
    """Fellow contact model linked to a User via Foreign Key."""
    __tablename__ = "fellows"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    # Foreign key referencing users.id table with ON DELETE CASCADE
    owner_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), default="")
    relation = db.Column(db.String(100), default="")
    notes = db.Column(db.Text, default="")
    attachments = db.Column(db.JSON, default=list) # JSON array of attachment file metadata
    created_at = db.Column(db.DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))


def serialize_fellow(fellow):
    """Converts Fellow ORM instance into a JSON-serializable dictionary."""
    return {
        "id": fellow.id,
        "owner_id": fellow.owner_id,
        "name": fellow.name,
        "email": fellow.email,
        "relation": fellow.relation,
        "notes": fellow.notes,
        "attachments": fellow.attachments or [],
        "created_at": fellow.created_at.isoformat() if fellow.created_at else None,
    }
```

---

### 3.3 `models/audit_log.py` — `class AuditLog`

Tracks administrative and security events (e.g., user login, role update, password reset).

```python
import datetime
from extensions import db

class AuditLog(db.Model):
    """Database model for security audit logs."""
    __tablename__ = "audit_logs"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.String(80), nullable=True)
    username = db.Column(db.String(120), nullable=True)
    action = db.Column(db.String(100), nullable=False) # e.g. "USER_LOGIN", "ROLE_UPDATED"
    details = db.Column(db.JSON, default=dict)
    ip_address = db.Column(db.String(45), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc), index=True)


def serialize_audit_log(log):
    """Converts AuditLog ORM instance into a dictionary."""
    return {
        "id": log.id,
        "user_id": log.user_id,
        "username": log.username,
        "action": log.action,
        "details": log.details or {},
        "ip_address": log.ip_address,
        "created_at": log.created_at.isoformat() if log.created_at else None,
    }
```

---

## 4. Validation & Data Sanitization Layer (`validators/`)

### 4.1 `validators/schemas.py` — Pydantic v2 Classes

Request body payloads are validated using strict **Pydantic v2** models to sanitize input, validate email formatting, check string lengths, and return clear, descriptive validation error responses.

```python
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, field_validator

class SignupSchema(BaseModel):
    """Validation schema for user registration requests."""
    username: str = Field(..., min_length=2, max_length=80)
    email: EmailStr  # Ensures email is valid (e.g. user@example.com)
    password: str = Field(..., min_length=6, max_length=128)
    full_name: Optional[str] = Field(default="", max_length=120)
    bio: Optional[str] = Field(default="", max_length=1000)
    role: Optional[str] = Field(default="User")

    @field_validator("username")

    def sanitize_username(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Username cannot be empty or whitespace only")
        return v


class SigninSchema(BaseModel):
    """Validation schema for authentication requests."""
    email: EmailStr
    password: str = Field(..., min_length=1)


class FellowSchema(BaseModel):
    """Validation schema for creating/updating contact fellows."""
    name: str = Field(..., min_length=1, max_length=120)
    email: Optional[str] = Field(default="", max_length=120)
    relation: Optional[str] = Field(default="", max_length=100)
    notes: Optional[str] = Field(default="", max_length=2000)


class ProfileUpdateSchema(BaseModel):
    """Validation schema for profile edits."""
    username: Optional[str] = Field(default=None, min_length=2, max_length=80)
    full_name: Optional[str] = Field(default=None, max_length=120)
    bio: Optional[str] = Field(default=None, max_length=1000)


class PasswordResetRequestSchema(BaseModel):
    """Validation schema for password reset requests."""
    email: EmailStr


class PasswordResetConfirmSchema(BaseModel):
    """Validation schema for confirming password reset."""
    reset_token: str = Field(..., min_length=10)
    new_password: str = Field(..., min_length=6, max_length=128)


def validate_with_pydantic(schema_cls, data: dict):
    """Helper function that executes Pydantic validation and formats error messages."""
    try:
        validated_obj = schema_cls(**data)
        return True, validated_obj.model_dump(), None
    except Exception as exc:
        # Returns formatted error string for response body
        return False, None, str(exc)
```

---

## 5. Authentication, Security & Token Management

### 5.1 `auth/utils.py` — JWT Generation & Verification

Generates and decodes JSON Web Tokens (JWT) using `PyJWT`. Each issued token includes a unique `jti` (JWT ID) UUID claim to allow token revocation.

```python
import uuid
import datetime
import jwt
from flask import current_app
from services.token_blacklist_service import is_token_blacklisted

def generate_token(user_id, token_type="access", expires_delta=None):
    """Generates a signed JWT token containing user_id (sub), type, and unique jti UUID."""
    now = datetime.datetime.now(datetime.timezone.utc)
    if expires_delta is None:
        expires_delta = datetime.timedelta(minutes=30) if token_type == "access" else datetime.timedelta(days=7)

    payload = {
        "sub": str(user_id),
        "type": token_type,
        "jti": str(uuid.uuid4()),  # Unique token ID claim
        "iat": now,
        "exp": now + expires_delta,
    }

    secret = current_app.config["SECRET_KEY"]
    return jwt.encode(payload, secret, algorithm="HS256")


def decode_token(token_str, expected_type="access"):
    """Decodes JWT token, checks expiration, expected token type, and Redis blacklisting."""
    try:
        secret = current_app.config["SECRET_KEY"]
        payload = jwt.decode(token_str, secret, algorithms=["HS256"])

        # 1. Check expected token type (access vs refresh vs verify_email)
        if payload.get("type") != expected_type:
            return None

        # 2. Check if token jti has been blacklisted in Redis (revoked)
        jti = payload.get("jti")
        if jti and is_token_blacklisted(jti):
            return None

        return payload
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return None
```

---

### 5.2 `services/token_blacklist_service.py` — Redis Revocation

Handles instant JWT revocation upon logout using Redis.

```python
from extensions import redis_client

def blacklist_token(jti: str, expires_in_seconds: int = 86400) -> bool:
    """Stores revoked token jti in Redis with expiration TTL."""
    if not jti:
        return False
    key = f"token_blacklist:{jti}"
    redis_client.set(key, "revoked", ex=expires_in_seconds)
    return True


def is_token_blacklisted(jti: str) -> bool:
    """Checks if token jti exists in Redis blacklist."""
    if not jti:
        return False
    key = f"token_blacklist:{jti}"
    return redis_client.get(key) is not None
```

---

### 5.3 `middleware/auth.py` — `@token_required` & `@role_required`

Custom Flask decorators protecting routes and enforcing Role-Based Access Control (RBAC).

```python
from functools import wraps
from flask import request, jsonify
from extensions import db
from models.user import User
from auth.utils import decode_token

def token_required(f):
    """Decorator verifying valid Bearer JWT token in Authorization header."""
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return jsonify({"error": "Missing or invalid Authorization header"}), 401

        token = auth_header.split(" ")[1]
        payload = decode_token(token, expected_type="access")
        if not payload:
            return jsonify({"error": "Token is invalid, expired, or revoked"}), 401

        user_id = payload.get("sub")
        user = db.session.get(User, int(user_id)) if user_id and user_id.isdigit() else None
        if not user:
            return jsonify({"error": "User not found"}), 401

        # Attach authenticated user to request context
        request.current_user = user
        request.user_id = user.id
        request.token_jti = payload.get("jti")
        return f(*args, **kwargs)
    return decorated


def role_required(*allowed_roles):
    """Decorator checking if authenticated user possesses one of allowed roles."""
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            user = getattr(request, "current_user", None)
            if not user or user.role not in allowed_roles:
                return jsonify({"error": "Forbidden: Insufficient permissions"}), 403
            return f(*args, **kwargs)
        return decorated
    return decorator
```

---

## 6. Business Logic & Services Layer (`services/`)

### 6.1 `services/auth_service.py`

Encapsulates core user account authentication, registration, and token refresh logic.

```python
import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import func
from flask import current_app
from extensions import db
from models.user import User, UserRole
from auth.utils import generate_token, generate_tokens_pair
from services.password_reset_service import generate_verification_token

def register_user(cleaned_data):
    """Registers a new user, hashes password, saves to PostgreSQL, and dispatches email task."""
    email = cleaned_data["email"].strip().lower()

    # Case-insensitive email check
    if User.query.filter(func.lower(User.email) == email).first():
        return False, "Email already registered", None, 409

    role = cleaned_data.get("role", UserRole.USER)
    user = User(
        username=cleaned_data["username"],
        email=email,
        password=generate_password_hash(cleaned_data["password"]),
        full_name=cleaned_data.get("full_name", ""),
        bio=cleaned_data.get("bio", ""),
        role=role,
        is_verified=False,
    )

    db.session.add(user)
    db.session.commit()

    # Dispatch Celery background verification email task
    verification_token = generate_verification_token(user.id)

    tokens = generate_tokens_pair(user.id)
    tokens["verification_token"] = verification_token
    return True, "Account created", tokens, 201


def authenticate_user(email, password):
    """Authenticates user credentials and enforces email verification check."""
    clean_email = email.strip().lower()
    user = User.query.filter(func.lower(User.email) == clean_email).first()

    if not user or not check_password_hash(user.password, password):
        return False, "Invalid email or password", None, 401

    # Block signin if email verification is required and user email is unverified
    require_verify = current_app.config.get("REQUIRE_EMAIL_VERIFICATION", True)
    is_testing = current_app.config.get("TESTING", False)
    if require_verify and not is_testing and not user.is_verified:
        return False, "Email not verified. Please verify your email before logging in.", None, 403

    tokens = generate_tokens_pair(user.id)
    return True, "Signed in", tokens, 200
```

---

### 6.2 `services/cache_service.py` — Redis Endpoint Caching

Provides query/endpoint response caching with automatic invalidation on write mutations.

```python
import json
from functools import wraps
from flask import request, jsonify, make_response
from extensions import redis_client

def cache_get(key: str):
    """Retrieves cached string data from Redis."""
    data = redis_client.get(key)
    return data.decode("utf-8") if isinstance(data, bytes) else data

def cache_set(key: str, val: str, ttl: int = 300):
    """Stores data in Redis with expiration TTL (default 5 minutes)."""
    redis_client.set(key, val, ex=ttl)

def cache_delete_pattern(pattern: str):
    """Deletes all Redis keys matching glob pattern."""
    keys = redis_client.keys(pattern)
    if keys:
        redis_client.delete(*keys)

def cache_endpoint(ttl: int = 300):
    """Decorator caching route response in Redis for specified TTL."""
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            user_id = getattr(request, "user_id", "public")
            cache_key = f"cache:{user_id}:{request.path}:{request.query_string.decode('utf-8')}"

            # Check cache hit
            cached_data = cache_get(cache_key)
            if cached_data:
                res = make_response(jsonify(json.loads(cached_data)))
                res.headers["X-Cache"] = "HIT"
                return res

            # Cache miss: execute view function
            response = f(*args, **kwargs)
            res_obj = make_response(response)
            if res_obj.status_code == 200:
                cache_set(cache_key, res_obj.get_data(as_text=True), ttl=ttl)
                res_obj.headers["X-Cache"] = "MISS"
            return res_obj
        return decorated
    return decorator
```

---

## 7. Asynchronous Background Task Queue (`tasks/`)

### 7.1 `tasks/celery_app.py` — Celery Configuration

Initializes Celery instance bound to Flask application context and Redis broker.

```python
from celery import Celery

def create_celery_app(app=None):
    """Factory creating Celery app bound to Flask context."""
    celery = Celery(
        "jwt_auth_app",
        broker="redis://localhost:6379/0",
        backend="redis://localhost:6379/0"
    )
    if app:
        celery.conf.update(app.config)
        class ContextTask(celery.Task):
            def __call__(self, *args, **kwargs):
                with app.app_context():
                    return self.run(*args, **kwargs)
        celery.Task = ContextTask
    return celery

celery_app = create_celery_app()
```

---

### 7.2 `tasks/email_tasks.py` — Async Celery Email Tasks with Gmail SMTP

Defines background email tasks dispatched asynchronously via `.delay()`. Connects to Gmail SMTP (`smtp.gmail.com:587`) using TLS when credentials are set in `.env`.

```python
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
    """Asynchronous Celery task to send password reset email link."""
    reset_link = f"{Config.APP_BASE_URL}/reset-password?token={reset_token}"
    # Constructs HTML template with action button to /reset-password
    sent = _send_smtp_email(email, "Reset Your Password", f"Reset link: {reset_link}", html_content)
    return {"status": "sent", "smtp_sent": sent, "email": email}


@celery_app.task(name="send_verification_email")
def send_verification_email(email: str, verification_token: str):
    """Asynchronous Celery task to send account verification email link."""
    verification_link = f"{Config.APP_BASE_URL}/verify-email?token={verification_token}"
    # Constructs HTML template with action button to /verify-email
    sent = _send_smtp_email(email, "Verify Your Gmail Address", f"Verify link: {verification_link}", html_content)
    return {"status": "sent", "smtp_sent": sent, "email": email}
```

---

## 8. API Blueprints, Web Pages & Route Handlers

### Web Pages
- `GET /` or `/signin` — Sign In & Forgot Password Form
- `GET /signup` — User Registration Page
- `GET /verify-email?token=<TOKEN>` — Gmail Email Verification Landing Page (`verify_email.html`)
- `GET /reset-password?token=<TOKEN>` — Gmail Password Reset Landing Page (`reset_password.html`)
- `GET /profile` — Authenticated Profile Dashboard

### Summary of REST Endpoints

| Endpoint | Method | Security | Description |
|---|---|:---:|---|
| `/api/v1/auth/signup` | POST | Public | Register new user account (dispatches async Gmail verification email) |
| `/api/v1/auth/signin` | POST | Public | Authenticate user & receive JWT tokens / HTTP-Only cookies (Requires verified email) |
| `/api/v1/auth/verify-email` | POST | Public | Verify user email address with verification token |
| `/api/v1/auth/refresh` | POST | Public | Refresh access token using cookie or token string |
| `/api/v1/auth/logout` | POST | `@token_required` | Revoke token `jti` in Redis and clear refresh cookie |
| `/api/v1/auth/forgot-password` | POST | Public | Request password reset link (dispatches async Celery task to Gmail) |
| `/api/v1/auth/reset-password` | POST | Public | Confirm password reset with reset token & new password |
| `/api/v1/profile` | GET | `@token_required` | Retrieve authenticated user profile |
| `/api/v1/profile` | PUT | `@token_required` | Update profile information |
| `/api/v1/profile/picture` | POST | `@token_required` | Upload profile avatar (saves unique UUID filename) |
| `/api/v1/fellows` | GET | `@token_required` | Fetch contacts (Redis cached, supports search & pagination) |
| `/api/v1/fellows` | POST | `@token_required` | Add a fellow (automatically purges user cache) |
| `/api/v1/fellows/<id>` | PUT | `@token_required` | Update fellow by ID (purges user cache) |
| `/api/v1/fellows/<id>` | DELETE | `@token_required` | Delete fellow by ID (purges user cache) |
| `/api/v1/admin/users/<id>/role` | PUT | `@role_required("Admin")` | Update user role (`Admin`, `Manager`, `User`) |
| `/api/v1/admin/audit-logs` | GET | `@role_required("Admin")` | Retrieve system security audit logs |

---

## 9. Automated Testing Suite (`tests/`)

The application includes 35 passing unit and integration tests executed using `pytest` and an isolated, fast in-memory SQLite database:

```powershell
# Run full automated test suite
$env:PYTHONPATH="."; .\.venv\Scripts\python.exe -m pytest
```

### Test Coverage Highlights:
- **`test_auth.py`:** User signup, duplicate registration prevention, signin credentials check.
- **`test_cookies_and_logout.py`:** HTTP-only refresh cookies, logout token revocation (`jti` blacklisting in Redis).
- **`test_pydantic_validators.py`:** Payload validation error responses for invalid emails and short passwords.
- **`test_celery_tasks.py`:** Celery background task execution for email dispatches.
- **`test_caching.py`:** Redis endpoint response caching (`X-Cache: HIT`/`MISS`) and mutation cache invalidation.
- **`test_profile.py`:** Profile CRUD operations, unique avatar uploads, contact search, pagination, and RBAC permissions.

