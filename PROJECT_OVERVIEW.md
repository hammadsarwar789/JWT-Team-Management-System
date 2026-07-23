# Project Architecture & Developer Guide: JWT Auth App

Welcome! This document provides a comprehensive technical overview of the **JWT Auth App** codebase. It is designed to give AI agents and software engineers complete context regarding the application architecture, data models, API contracts, database patterns, caching strategies, task queues, and testing framework.

---

## 1. High-Level Architecture Overview

The application is a production-ready, highly scalable web API and single-page web app built with **Flask**, **PostgreSQL** (Flask-SQLAlchemy), **Redis**, **Pydantic v2**, **Celery**, and **PyJWT**.

```
jwt_auth_app/
├── app.py                 # Flask App Factory (registers blueprints, global error handlers)
├── run.py                 # Application entry point (loads .env, starts server)
├── config.py              # Environment configuration (SECRET_KEY, DATABASE_URL, REDIS_URL, JWT settings)
├── extensions.py          # Flask-SQLAlchemy db object & ResilientRedis client
├── auth/                  # Authentication module
│   ├── routes.py          # Signup, Signin, Refresh, Logout & Password reset endpoints
│   └── utils.py           # JWT token generation with jti, decoding, @token_required decorator
├── profiles/              # User profile, Fellows, Dashboard & Admin module
│   └── routes.py          # Profile GET/PUT, Fellows CRUD, Analytics & Role management
├── models/                # SQLAlchemy ORM Models
│   ├── user.py            # User model (roles: Admin, Manager, User)
│   ├── fellow.py          # Fellow model (owner_id ForeignKey to users.id)
│   └── audit_log.py       # AuditLog model for security tracking
├── validators/            # Data Sanitization & Schema Validation Layer
│   ├── schemas.py         # Pydantic v2 payload models (SignupSchema, SigninSchema, etc.)
│   ├── auth_validator.py  # Signup & Signin validation wrappers
│   ├── profile_validator.py # Profile update & Fellow validation wrappers
│   └── file_validator.py  # Image & file attachment validators
├── services/              # Modularized Business Logic Layer
│   ├── auth_service.py    # Registration, login & token refresh logic
│   ├── profile_service.py # Profile updates, avatar uploads, role updates
│   ├── fellow_service.py  # Fellows CRUD, search, pagination, file attachments
│   ├── token_blacklist_service.py # Redis-backed JWT revocation & jti blacklisting
│   ├── cache_service.py   # Redis query/endpoint caching & invalidation
│   ├── password_reset_service.py # Password reset & email verification logic
│   ├── audit_service.py   # Audit log recording & retrieval
│   └── dashboard_service.py # User analytics & profile completeness metrics
├── tasks/                 # Asynchronous Task Queue Layer (Celery)
│   ├── celery_app.py      # Celery app factory bound to Flask context & Redis broker
│   └── email_tasks.py     # Async email background tasks (password reset, email verification)
├── templates/             # HTML templates (base.html, signin.html, signup.html, profile.html)
├── static/                # Static assets (style.css)
├── tests/                 # Automated Test Suite (35 Passing Pytest Unit & Integration Tests)
│   ├── conftest.py        # Pytest fixtures & isolated SQLite database setup
│   ├── test_auth.py       # Authentication unit tests
│   ├── test_cookies_and_logout.py # HTTP-only cookies, /logout & token revocation tests
│   ├── test_pydantic_validators.py # Pydantic schema validation tests
│   ├── test_celery_tasks.py # Async Celery email dispatch tests
│   ├── test_caching.py    # Redis query caching & invalidation tests
│   └── test_profile.py    # Profile & Fellows unit tests
└── requirements.txt       # Python dependencies (Flask, SQLAlchemy, Redis, Pydantic, Celery, etc.)
```

---

## 2. Key Architecture Patterns & Security Model

### Application Factory (`app.py`)
The app uses Flask's standard `create_app()` factory function. Blueprints (`auth_bp`, `profile_bp`), database initialization (`init_db(app)`), security headers, and global exception handlers (`SQLAlchemyError`) are registered inside `create_app()`.

### Relational Database Layer (`Flask-SQLAlchemy`)
- All database entities (`User`, `Fellow`, `AuditLog`) are defined as SQL ORM models inheriting from `extensions.db.Model`.
- Database connections and tables are managed via `Flask-SQLAlchemy`.
- Foreign key constraints ensure data integrity (`Fellow.owner_id` -> `User.id` with `ondelete="CASCADE"`).
- Case-insensitive email querying using `func.lower(User.email)` for secure registration, login, and password resets.

### Advanced Authentication & Security
1. **HTTP-Only Cookies:** Refresh tokens are issued and stored securely via `Set-Cookie: refresh_token=...; HttpOnly; SameSite=Lax` headers.
2. **Redis Token Revocation (Blacklisting):** Each issued JWT contains a unique `jti` UUID claim. Calling `POST /api/v1/auth/logout` revokes the token `jti` in Redis and clears the refresh cookie.
3. **Pydantic v2 Payload Validation:** Request bodies are sanitized and validated against strict Pydantic v2 models in `validators/schemas.py`.

### Asynchronous Task Queue & Caching
1. **Celery + Redis Broker:** Background operations (e.g., password reset emails and email verification) are offloaded to Celery workers using `.delay()`.
2. **Redis Endpoint & Query Caching:** Heavy read endpoints (`GET /fellows`, `GET /dashboard/stats`, `GET /admin/audit-logs`) use `@cache_endpoint(ttl=300)` with `X-Cache: HIT` / `X-Cache: MISS` headers. Mutations (`POST`, `PUT`, `DELETE`) automatically purge matching user cache entries.

---

## 3. Data Schemas & SQL Models

### `users` Table
Stores user account profiles, hashed credentials, and verification state.
- `id`: Integer (Primary Key, Autoincrement)
- `username`: String(80) (Required)
- `email`: String(120) (Required, Unique, Indexed)
- `password`: String(255) (Hashed via Werkzeug scrypt/pbkdf2)
- `full_name`: String(120)
- `bio`: Text
- `role`: String(20) (`Admin`, `Manager`, `User`)
- `is_verified`: Boolean
- `reset_token`: String(255)
- `profile_picture`: String(255)
- `created_at`: DateTime (Timezone-aware UTC)

### `fellows` Table
Stores contacts linked to a user account.
- `id`: Integer (Primary Key, Autoincrement)
- `owner_id`: Integer (ForeignKey to `users.id`, Indexed)
- `name`: String(120) (Required)
- `email`: String(120)
- `relation`: String(100)
- `notes`: Text
- `attachments`: JSON (List of attachment dicts)
- `created_at`: DateTime (Timezone-aware UTC)

### `audit_logs` Table
Tracks security and administrative events.
- `id`: Integer (Primary Key, Autoincrement)
- `user_id`: String(80)
- `username`: String(120)
- `action`: String(100)
- `details`: JSON
- `ip_address`: String(45)
- `created_at`: DateTime (Timezone-aware UTC, Indexed)

---

## 4. API Specification & Endpoints

All protected endpoints require the HTTP header:
`Authorization: Bearer <JWT_TOKEN>`

| Endpoint | Method | Auth Required | Description & Request Body |
|---|---|:---:|---|
| `/api/v1/auth/signup` | POST | No | Register new user. Body: `{ username, email, password, full_name?, bio? }` (Sets HTTP-Only refresh cookie) |
| `/api/v1/auth/signin` | POST | No | Authenticate user. Body: `{ email, password }` (Sets HTTP-Only refresh cookie) |
| `/api/v1/auth/refresh` | POST | No | Refresh access token using HTTP-only cookie or `{ refresh_token }` |
| `/api/v1/auth/logout` | POST | Yes | Revoke active access token `jti` in Redis and clear refresh cookie |
| `/api/v1/auth/forgot-password` | POST | No | Dispatch password reset email task via Celery |
| `/api/v1/auth/reset-password` | POST | No | Confirm password reset using reset token |
| `/api/v1/profile` | GET | Yes | Fetch authenticated user profile |
| `/api/v1/profile` | PUT | Yes | Update user profile. Body: any of `{ username, full_name, bio }` |
| `/api/v1/fellows` | GET | Yes | List fellows (Redis cached, supports `q`, `page`, `limit`, `sort`, `order`, `all`) |
| `/api/v1/fellows` | POST | Yes | Add a fellow. Body: `{ name, email?, relation?, notes? }` (Purges user cache) |
| `/api/v1/fellows/<id>` | PUT | Yes | Update a fellow by ID (Purges user cache) |
| `/api/v1/fellows/<id>` | DELETE | Yes | Delete a fellow by ID (Purges user cache) |
| `/api/v1/admin/users/<id>/role` | PUT | Yes (Admin) | Update user role: `{ "role": "Admin" \| "Manager" \| "User" }` |
| `/api/v1/admin/audit-logs` | GET | Yes (Admin) | Retrieve audit logs (Redis cached) |

---

## 5. Security & Validation Rules

1. **Passwords:** Stored securely using Werkzeug scrypt/pbkdf2 hashing (`generate_password_hash` / `check_password_hash`). Passwords must be at least 6 characters.
2. **JWT & Revocation:** Dual-token authentication: 30-minute Access Tokens + 7-day Refresh Tokens, signed with `HS256`, backed by Redis `jti` token revocation.
3. **Data Validation:** Strict payload validation via Pydantic v2 (`validators/schemas.py`).
4. **Timezones:** All timestamp calculations use timezone-aware Python `datetime.datetime.now(datetime.timezone.utc)`.
5. **Security Headers:** Defensive HTTP headers (`X-Frame-Options: DENY`, `X-Content-Type-Options: nosniff`, `X-XSS-Protection`) automatically injected.

---

## 6. How to Run & Test

### Environment Setup (`.env`)
Ensure `.env` contains:
```env
SECRET_KEY=your-random-secret-key
DATABASE_URL=postgresql://postgres:your_password@localhost:5432/Jwt_Login
REDIS_URL=redis://localhost:6379/0
```

### Running the Server
```powershell
.\.venv\Scripts\python.exe run.py
```

### Running Automated Unit Tests
```powershell
.\.venv\Scripts\python.exe -m pytest
```
