# 📘 Complete Project Study Notes: JWT Auth & Team Management System

Welcome! This guide provides an easy-to-understand breakdown of the entire **JWT Auth Team Management System** codebase.

---

## 🚀 1. Executive Summary

This application is a **production-ready RESTful Web API and Web Application** built using **Flask**, **PostgreSQL**, **Redis**, **Pydantic v2**, and **Celery**. 

It allows users to:
1. **Create Accounts & Sign In** securely using hashed passwords, **HTTP-Only Cookies**, and **JWT Tokens** (Access & Refresh tokens).
2. **Revoke Active Sessions & Logout** securely using Redis-backed token blacklisting (`jti`).
3. **Validate Request Payloads** using strict **Pydantic v2** schemas (`validators/schemas.py`).
4. **Manage User Profiles** (upload profile pictures with cache busters and fallbacks, update bio, role permissions).
5. **Manage Fellows (Team Contacts)** (Add, Edit, Delete, Search, Sort, Paginate, Upload file attachments, and Export/Import CSV/JSON data).
6. **Accelerate Endpoints** via Redis query response caching (`X-Cache: HIT` / `X-Cache: MISS`).
7. **Dispatch Background Tasks** asynchronously via **Celery & Redis Broker** for password reset emails and email verification.
8. **Track Security Events** via automated **Audit Logging**.
9. **Enforce Role-Based Access Control (RBAC)** supporting **Admin**, **Manager**, and **User** roles.

---

## 🛠️ 2. Technology Stack

| Layer | Technology Used | Description |
|---|---|---|
| **Backend Framework** | **Python 3 + Flask** | Modular Flask app using the Application Factory pattern and Blueprints. |
| **Database** | **PostgreSQL** | Relational database managed via **Flask-SQLAlchemy ORM**. |
| **Caching & Revocation** | **Redis** | In-memory store for JWT token blacklisting (`jti`) and endpoint response caching with resilient mock fallback. |
| **Validation Layer** | **Pydantic v2** | Strict data sanitization, email formatting, and type-safe payload validation (`validators/schemas.py`). |
| **Task Queue** | **Celery + Redis** | Offloads asynchronous tasks (sending emails, heavy reports) using Celery workers. |
| **Authentication** | **PyJWT + Cookies** | Dual-token mechanism: short-lived **Access Tokens** + **HTTP-Only Refresh Cookies**. |
| **Password Hashing** | **Werkzeug Security** | Secure password hashing using `scrypt` / `pbkdf2`. |
| **Testing Suite** | **Pytest + SQLite** | 35 automated tests (100% passing) using an in-memory SQLite database for instant verification. |
| **File Management** | **Werkzeug Uploads** | Secure avatar & attachment uploads saved under `uploads/` with unique UUID names. |

---

## 📂 3. Folder Structure & Component Breakdown

```
jwt_auth_app/
├── app.py                 # 🏭 App Factory (Registers Blueprints, DB & Error Handlers)
├── run.py                 # 🚀 App Entry Point (Loads .env and starts Flask server)
├── config.py              # ⚙️ Configuration (DATABASE_URL, REDIS_URL, SECRET_KEY, JWT Expiries)
├── extensions.py          # 🔌 Database Instance & ResilientRedis client
│
├── models/                # 🗄️ Database Tables (SQL ORM)
│   ├── user.py            # User table schema & UserRole constants (Admin, Manager, User)
│   ├── fellow.py          # Fellow (Contacts) table schema (linked to User via owner_id)
│   └── audit_log.py       # AuditLog table schema for tracking system events
│
├── validators/            # 🔍 Input Payload Validation & Pydantic Schemas
│   ├── schemas.py         # Pydantic v2 schemas (SignupSchema, SigninSchema, FellowSchema, etc.)
│   ├── auth_validator.py  # Signup & signin payload checks using Pydantic
│   ├── profile_validator.py # Profile & fellow payload checks using Pydantic
│   └── file_validator.py  # Avatar image type and size validation
│
├── services/              # 🧠 Business Logic Layer (Clean separation from routes)
│   ├── auth_service.py              # User registration, signin, token refresh
│   ├── profile_service.py           # Profile updates, unique avatar uploads, role updates
│   ├── fellow_service.py            # Fellows CRUD, search, pagination, file attachments
│   ├── token_blacklist_service.py   # Redis-backed JWT token revocation & jti blacklisting
│   ├── cache_service.py             # Redis query/endpoint caching & invalidation (@cache_endpoint)
│   ├── password_reset_service.py    # Password reset & async email verification
│   ├── audit_service.py             # Event logging and admin audit log retrieval
│   ├── dashboard_service.py         # User metrics and profile completeness stats
│   ├── analytics_service.py         # Relationship breakdown & domain analytics
│   └── import_export_service.py     # CSV/JSON file import and export processing
│
├── tasks/                 # ⚡ Asynchronous Task Queue Layer (Celery)
│   ├── celery_app.py      # Celery instance configuration bound to Redis broker
│   └── email_tasks.py     # Celery tasks for background email dispatching
│
├── middleware/            # 🛡️ Security & Middleware Filters
│   ├── auth.py            # @token_required & @role_required decorators
│   ├── logger.py          # Structured app file logging (logs/app.log)
│   └── security.py        # HTTP security headers (X-Frame-Options, XSS, HSTS)
│
├── auth/                  # 🔑 Auth Routes Blueprint (/api/v1/auth)
│   ├── routes.py          # REST endpoints for signup, signin, refresh, logout, password reset
│   └── utils.py           # JWT encoding/decoding with jti UUID generation
│
├── profiles/              # 👤 Profiles, Fellows & Admin Blueprint (/api/v1)
│   └── routes.py          # Profile, Fellows CRUD, Redis cached queries, Admin routes
│
├── templates/             # 🌐 HTML Pages (Frontend UI)
│   ├── signin.html        # Login page
│   ├── signup.html        # Registration page
│   └── profile.html       # Dashboard, Avatar preview & profile UI
│
├── static/                # 🎨 Static Assets
│   └── style.css          # CSS styles
│
└── tests/                 # 🧪 Automated Test Suite (35 Passing Pytest Unit & Integration Tests)
    ├── conftest.py        # Pytest fixtures & SQLite in-memory setup
    └── test_*.py          # Test files for auth, cookies, Pydantic, Celery, Redis caching, RBAC
```

---

## 🗃️ 4. Database Schema Overview

```
+-----------------------------------+        +-----------------------------------+
|               USERS               |        |              FELLOWS              |
+-----------------------------------+        +-----------------------------------+
| id           : INT (PK, Auto)     |<------1| id           : INT (PK, Auto)     |
| username     : VARCHAR(80)        |        | owner_id     : INT (FK->users.id) |
| email        : VARCHAR(120) UK    |        | name         : VARCHAR(120)      |
| password     : VARCHAR(255)       |        | email        : VARCHAR(120)      |
| full_name    : VARCHAR(120)       |        | relation     : VARCHAR(100)      |
| bio          : TEXT               |        | notes        : TEXT               |
| role         : VARCHAR(20)        |        | attachments  : JSON               |
| is_verified  : BOOLEAN            |        | created_at   : DATETIME           |
| reset_token  : VARCHAR(255)       |        +-----------------------------------+
| created_at   : DATETIME           |
+-----------------------------------+
```

---

## 🔄 5. How Data Flows Through the App

### Example: User Signs In (`POST /api/v1/auth/signin`)

1. **Client / Browser** sends request with `{ email, password }`.
2. **`validators/auth_validator.py`** validates body against **`SigninSchema`** (Pydantic v2).
3. **`auth_service.py`** queries PostgreSQL using case-insensitive lower match: `User.query.filter(func.lower(User.email) == clean_email).first()`.
4. Password is checked using `check_password_hash(user.password, password)`.
5. **`auth/utils.py`** generates `access_token` and `refresh_token` containing a unique `jti` claim.
6. `refresh_token` is injected into a secure `Set-Cookie: refresh_token=...; HttpOnly; SameSite=Lax` header.
7. Access token and status are returned to client.

---

## 🔐 6. Role-Based Access Control (RBAC)

The system supports **3 Roles**:

| Feature | Admin | Manager | User |
|---|:---:|:---:|:---:|
| **Manage Own Profile** | ✅ | ✅ | ✅ |
| **Manage Own Fellows** | ✅ | ✅ | ✅ |
| **View System Dashboard** | ✅ | ✅ | ✅ |
| **View All System Fellows** (`?all=true`) | ✅ | ❌ | ❌ |
| **Change User Roles** (`PUT /admin/users/<id>/role`) | ✅ | ❌ | ❌ |
| **View Security Audit Logs** (`GET /admin/audit-logs`) | ✅ | ❌ | ❌ |

---

## ⚡ 7. Developer Cheat Sheet

### 1. Run the Server
```powershell
.\.venv\Scripts\python.exe run.py
```

### 2. Run Automated Tests (35 Tests)
```powershell
.\.venv\Scripts\python.exe -m pytest
```

### 3. Change a User to Admin
```powershell
.\.venv\Scripts\python.exe -c "from app import create_app; from extensions import db; from models.user import User, UserRole; app = create_app(); app.app_context().push(); u = User.query.filter_by(email='user@example.com').first(); u.role = UserRole.ADMIN; db.session.commit(); print('Role updated!')"
```
