# JWT Auth App (Flask + PostgreSQL + Redis + Pydantic v2 + Celery)

A production-ready, highly secure RESTful Web API and Web Application built with **Flask**, **PostgreSQL** (Flask-SQLAlchemy), **Redis**, **Pydantic v2**, **Celery**, and **PyJWT**.

Features user authentication, secure **HTTP-Only cookies**, instant **Redis token revocation**, **Role-Based Access Control (RBAC)**, **Pydantic payload validation**, **Redis query caching**, **asynchronous task queues**, team contact management (Fellows), file attachments, analytics, and security audit logging.

---

## 🚀 Key Features

- 🔐 **Advanced Auth & Security:** Dual-token mechanism (30-minute Access Tokens + 7-day Refresh Tokens stored in secure `HttpOnly`, `SameSite=Lax` cookies).
- 🚫 **Redis Token Blacklisting:** Active access tokens contain a unique `jti` claim and can be immediately revoked upon `/logout` via Redis.
- 🛡️ **Role-Based Access Control (RBAC):** Restrict endpoints with `@role_required` decorator supporting `Admin`, `Manager`, and `User` roles.
- 📐 **Pydantic v2 Payload Validation:** Strict data sanitization, email formatting, and type-safe payload validation (`validators/schemas.py`).
- ⚡ **Redis Endpoint Caching:** Heavy read endpoints (`GET /fellows`, `GET /dashboard/stats`, `GET /admin/audit-logs`) use `@cache_endpoint(ttl=300)` with `X-Cache: HIT` / `X-Cache: MISS` headers and automatic mutation invalidation.
- 📩 **Asynchronous Task Queue (Celery):** Background email processing (password resets, account verification) offloaded to Celery workers using Redis as broker.
- 👥 **Fellows & Attachment Management:** Full CRUD operations for team contacts, filtering, searching, sorting, pagination, and file attachment uploads.
- 📊 **Audit Logging:** System security events (`LOGIN`, `LOGOUT`, `PASSWORD_RESET`, `ROLE_UPDATE`) automatically tracked in PostgreSQL audit logs.
- 🧪 **35 Passing Unit & Integration Tests:** 100% automated test coverage using pytest with in-memory SQLite database.

---

## 1. Prerequisites Setup

1. Make sure **PostgreSQL** is running on `localhost:5432` and create database `Jwt_Login`:
   ```sql
   CREATE DATABASE "Jwt_Login";
   ```
2. Make sure **Redis** server is running on `localhost:6379` *(Note: App includes an in-memory fallback if Redis is offline)*.

---

## 2. Environment & Project Setup

```bash
# Navigate to project directory
cd jwt_auth_app

# Create and activate virtual environment
python -m venv .venv
.\.venv\Scripts\activate        # Linux/macOS: source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

Ensure your `.env` file contains:
```env
SECRET_KEY=your-random-secret-key
DATABASE_URL=postgresql://postgres:your_password@localhost:5432/Jwt_Login
REDIS_URL=redis://localhost:6379/0
```

---

## 3. Run the Application

```powershell
.\.venv\Scripts\python.exe run.py
```
*(Database tables will be automatically created on startup).*

Visit `http://localhost:5000` in your browser.

---

## 4. Run Automated Unit Tests

Run the complete 35-test pytest suite:

```powershell
.\.venv\Scripts\python.exe -m pytest
```

---

## 5. Key API Specification

All protected endpoints require `Authorization: Bearer <JWT_TOKEN>` header (or HTTP-Only refresh cookie).

| Method | Endpoint | Auth Required | Role Required | Description |
|---|---|:---:|:---:|---|
| POST | `/api/v1/auth/signup` | No | — | Register new user account (Sets HTTP-Only refresh cookie) |
| POST | `/api/v1/auth/signin` | No | — | Authenticate user (Sets HTTP-Only refresh cookie) |
| POST | `/api/v1/auth/refresh` | No | — | Refresh access token using cookie or token string |
| POST | `/api/v1/auth/logout` | Yes | — | Revoke active token `jti` in Redis and clear refresh cookie |
| POST | `/api/v1/auth/forgot-password` | No | — | Request password reset token (dispatches async Celery task) |
| POST | `/api/v1/auth/reset-password` | No | — | Confirm password reset with reset token |
| GET | `/api/v1/profile` | Yes | — | Fetch authenticated user profile |
| PUT | `/api/v1/profile` | Yes | — | Update profile fields |
| POST | `/api/v1/profile/picture` | Yes | — | Upload profile avatar (saves unique UUID filename) |
| GET | `/api/v1/fellows` | Yes | — | List fellows (Redis cached, supports `q`, `page`, `limit`, `sort`, `order`, `all`) |
| POST | `/api/v1/fellows` | Yes | — | Create fellow contact (purges user cache) |
| PUT | `/api/v1/fellows/<id>` | Yes | — | Update fellow contact (purges user cache) |
| DELETE | `/api/v1/fellows/<id>` | Yes | — | Delete fellow contact (purges user cache) |
| GET | `/api/v1/dashboard/stats` | Yes | — | Dashboard metrics (Redis cached) |
| PUT | `/api/v1/admin/users/<id>/role` | Yes | Admin | Update user role (`Admin`, `Manager`, `User`) |
| GET | `/api/v1/admin/audit-logs` | Yes | Admin | View security audit logs (Redis cached) |

---
## 📂 Project Structure

```
jwt_auth_app/
├── app.py                 # Flask App Factory (registers blueprints, db initialization)
├── run.py                 # Server entry point (loads .env, starts Flask app)
├── config.py              # Application configuration (DATABASE_URL, REDIS_URL, JWT settings)
├── extensions.py          # SQLAlchemy db instance & ResilientRedis client
├── models/                # Database ORM models (User, Fellow, AuditLog)
├── validators/            # Pydantic v2 schemas (schemas.py) & payload validators
├── services/              # Business logic (auth, profile, fellows, token_blacklist, cache, password_reset)
├── tasks/                 # Celery task queue (celery_app.py, email_tasks.py)
├── middleware/            # JWT authentication, RBAC decorators & security headers
├── auth/                  # Authentication routes & JWT utilities with jti
├── profiles/              # Profile, Fellows, Admin & Analytics routes
├── templates/             # HTML templates (signin, signup, profile UI)
├── static/                # CSS styles
└── tests/                 # 35 automated pytest unit & integration tests
```
