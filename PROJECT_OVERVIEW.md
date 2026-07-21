# Project Architecture & Developer Guide: JWT Auth App

Welcome! This document provides a comprehensive technical overview of the **JWT Auth App** codebase. It is designed to give AI agents and software engineers complete context regarding the application architecture, data models, API contracts, database patterns, and testing strategies.

---

## 1. High-Level Architecture Overview

The application is a lightweight, scalable web API and single-page web app built with **Flask**, **PostgreSQL** (Flask-SQLAlchemy), and **PyJWT**.

```
jwt_auth_app/
├── app.py                 # Flask App Factory (registers blueprints, global error handlers)
├── run.py                 # Application entry point (loads .env, starts server)
├── config.py              # Environment configuration (SECRET_KEY, DATABASE_URL, JWT_EXPIRES)
├── extensions.py          # Flask-SQLAlchemy db object & init_db helper
├── auth/                  # Authentication module
│   ├── routes.py          # Signup, Signin, Refresh & Password reset endpoints
│   └── utils.py           # JWT token generation, decoding, @token_required decorator
├── profiles/              # User profile, Fellows, Dashboard & Admin module
│   └── routes.py          # Profile GET/PUT, Fellows CRUD, Analytics & Role management
├── models/                # SQLAlchemy ORM Models
│   ├── user.py            # User model (roles: Admin, Manager, User)
│   ├── fellow.py          # Fellow model (owner_id ForeignKey to users.id)
│   └── audit_log.py       # AuditLog model for security tracking
├── services/              # Modularized Business Logic Layer
├── templates/             # HTML templates (base.html, signin.html, signup.html, profile.html)
├── static/                # Static assets (style.css)
├── tests/                 # Unit test suite (pytest + in-memory SQLite)
│   ├── conftest.py        # Pytest fixtures & isolated SQLite database setup
│   ├── test_auth.py       # Authentication unit tests
│   ├── test_profile.py    # Profile & Fellows unit tests
│   └── ...                # Phase 2-5 enhancement tests
└── requirements.txt       # Python dependencies
```

---

## 2. Key Architecture Patterns & Database Strategy

### Application Factory (`app.py`)
The app uses Flask's standard `create_app()` factory function. Blueprints (`auth_bp`, `profile_bp`), database initialization (`init_db(app)`), security headers, and global exception handlers (`SQLAlchemyError`) are registered inside `create_app()`.

### Relational Database Layer (`Flask-SQLAlchemy`)
- All database entities (`User`, `Fellow`, `AuditLog`) are defined as SQL ORM models inheriting from `extensions.db.Model`.
- Database connections and tables are managed via `Flask-SQLAlchemy`.
- Foreign key constraints ensure data integrity (`Fellow.owner_id` -> `User.id` with `ondelete="CASCADE"`).
- Automated unit tests (`pytest`) use an in-memory SQLite database (`sqlite:///:memory:`), enabling 100% fast and isolated testing.

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
| `/api/v1/auth/signup` | POST | No | Register new user. Body: `{ username, email, password, full_name?, bio? }` |
| `/api/v1/auth/signin` | POST | No | Authenticate user. Body: `{ email, password }` |
| `/api/v1/auth/refresh` | POST | No | Refresh access token using `{ refresh_token }` |
| `/api/v1/profile` | GET | Yes | Fetch authenticated user profile |
| `/api/v1/profile` | PUT | Yes | Update user profile. Body: any of `{ username, full_name, bio }` |
| `/api/v1/fellows` | GET | Yes | List fellows (supports `q`, `page`, `limit`, `sort`, `order`, `all`) |
| `/api/v1/fellows` | POST | Yes | Add a fellow. Body: `{ name, email?, relation?, notes? }` |
| `/api/v1/fellows/<id>` | PUT | Yes | Update a fellow by ID |
| `/api/v1/fellows/<id>` | DELETE | Yes | Delete a fellow by ID |
| `/api/v1/admin/users/<id>/role` | PUT | Yes (Admin) | Update user role: `{ "role": "Admin" | "Manager" | "User" }` |
| `/api/v1/admin/audit-logs` | GET | Yes (Admin) | Retrieve audit logs |

---

## 5. Security & Validation Rules

1. **Passwords:** Stored securely using Werkzeug scrypt/pbkdf2 hashing (`generate_password_hash` / `check_password_hash`). Passwords must be at least 6 characters.
2. **JWT Tokens:** Dual-token authentication: 30-minute Access Tokens + 7-day Refresh Tokens, signed with `HS256`.
3. **Timezones:** All timestamp calculations use timezone-aware Python `datetime.datetime.now(datetime.timezone.utc)`.
4. **Security Headers:** Defensive HTTP headers (`X-Frame-Options: DENY`, `X-Content-Type-Options: nosniff`, `X-XSS-Protection`) automatically injected.

---

## 6. How to Run & Test

### Environment Setup (`.env`)
Ensure `.env` contains:
```env
SECRET_KEY=your-random-secret-key
DATABASE_URL=postgresql://postgres:your_password@localhost:5432/Jwt_Login
```

### Running the Server
```powershell
py run.py
```

### Running Automated Unit Tests
```powershell
py -m pytest
```
