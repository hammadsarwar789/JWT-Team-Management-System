# Project Architecture & Developer Guide: JWT Auth App

Welcome! This document provides a comprehensive technical overview of the **JWT Auth App** codebase. It is designed to give AI agents and software engineers complete context regarding the application architecture, data models, API contracts, database patterns, and testing strategies.

---

## 1. High-Level Architecture Overview

The application is a lightweight, scalable web API and single-page web app built with **Flask**, **MongoDB** (PyMongo), and **PyJWT**.

```
jwt_auth_app/
├── app.py                 # Flask App Factory (registers blueprints, global error handlers)
├── run.py                 # Application entry point (loads .env, starts server)
├── config.py              # Environment configuration (SECRET_KEY, MONGO_URI, JWT_EXPIRES)
├── extensions.py          # Database connection manager & CollectionProxy wrappers
├── auth/                  # Authentication module
│   ├── routes.py          # Signup & Signin API endpoints
│   └── utils.py           # JWT token generation, decoding, @token_required decorator
├── profiles/              # User profile & Fellows management module
│   └── routes.py          # Profile GET/PUT & Fellows CRUD endpoints
├── templates/             # HTML templates (base.html, signin.html, signup.html, profile.html)
├── static/                # Static assets (style.css)
├── tests/                 # Unit test suite (pytest + mongomock)
│   ├── conftest.py        # Pytest fixtures & in-memory MongoDB setup
│   ├── test_auth.py       # Authentication unit tests
│   ├── test_profile.py    # Profile & Fellows unit tests
│   └── test_utils.py      # JWT utility tests
└── requirements.txt       # Python dependencies
```

---

## 2. Key Architecture Patterns & Database Strategy

### Application Factory (`app.py`)
The app uses Flask's standard `create_app()` factory function. Blueprints (`auth_bp`, `profile_bp`) and global exception handlers are registered inside `create_app()`.

### Decoupled Database Layer & `CollectionProxy` (`extensions.py`)
To prevent top-level module import side-effects and allow isolated unit testing without a live MongoDB connection:
- `extensions.py` utilizes a `CollectionProxy` pattern that dynamically forwards PyMongo collection methods (`find_one`, `insert_one`, etc.) to `get_db()`.
- Database connections are initialized **lazily** upon first query request.
- Unit tests intercept the active database by calling `set_db(mongomock_database)`, enabling 100% in-memory testing.
- A global `PyMongoError` handler in `app.py` catches database connection timeouts/failures and returns clean HTTP 503 responses.

---

## 3. Data Schemas & Database Collections

### `users` Collection
Stores user account profiles and hashed credentials.
```json
{
  "_id": "ObjectId('6789abcdef0123456789abcd')",
  "username": "string (required)",
  "email": "string (required, unique index, lowercase)",
  "password": "string (hashed via werkzeug.security)",
  "full_name": "string (optional)",
  "bio": "string (optional)",
  "created_at": "datetime (timezone-aware UTC)"
}
```

### `fellows` Collection
Stores people/contacts linked to a specific user account.
```json
{
  "_id": "ObjectId('abcdef0123456789abcdef01')",
  "owner_id": "ObjectId('6789abcdef0123456789abcd')",
  "name": "string (required)",
  "email": "string (optional)",
  "relation": "string (optional)",
  "notes": "string (optional)",
  "created_at": "datetime (timezone-aware UTC)"
}
```

---

## 4. API Specification & Endpoints

All protected endpoints require the HTTP header:
`Authorization: Bearer <JWT_TOKEN>`

| Endpoint | Method | Auth Required | Description & Request Body | Response Codes |
|---|---|:---:|---|---|
| `/api/auth/signup` | POST | No | Register new user. Body: `{ username, email, password, full_name?, bio? }` | `201 Created`, `400 Bad Request`, `409 Conflict` |
| `/api/auth/signin` | POST | No | Authenticate user. Body: `{ email, password }` | `200 OK`, `401 Unauthorized` |
| `/api/profile` | GET | Yes | Fetch authenticated user profile. | `200 OK`, `401 Unauthorized`, `404 Not Found` |
| `/api/profile` | PUT | Yes | Update user profile. Body: any of `{ username, full_name, bio }` | `200 OK`, `400 Bad Request`, `401 Unauthorized` |
| `/api/fellows` | POST | Yes | Add a fellow linked to signed-in user. Body: `{ name, email?, relation?, notes? }` | `201 Created`, `400 Bad Request`, `401 Unauthorized` |
| `/api/fellows` | GET | Yes | List all fellows owned by signed-in user. | `200 OK`, `401 Unauthorized` |
| `/api/fellows/<id>` | PUT | Yes | Update a fellow by ID. Body: any of `{ name, email, relation, notes }` | `200 OK`, `400 Bad Request`, `404 Not Found` |
| `/api/fellows/<id>` | DELETE | Yes | Delete a fellow by ID. | `200 OK`, `400 Bad Request`, `404 Not Found` |

---

## 5. Security & Validation Rules

1. **Passwords:** Stored securely using Werkzeug scrypt/pbkdf2 hashing (`generate_password_hash` / `check_password_hash`). Passwords must be at least 6 characters.
2. **JWT Tokens:** Encoded/decoded using `PyJWT` with `HS256` algorithm. Expiry is set via `JWT_EXPIRES` (default: 24 hours).
3. **ObjectId Safety:** All string-to-ObjectId conversions are wrapped with `try...except InvalidId` (via `parse_oid`) to prevent HTTP 500 server crashes on malformed IDs.
4. **Timezones:** All timestamp calculations use timezone-aware Python 3.12+ `datetime.datetime.now(datetime.timezone.utc)`.

---

## 6. How to Run & Test

### Environment Setup (`.env`)
Ensure `.env` contains:
```env
SECRET_KEY=your-random-secret-key
MONGO_URI=mongodb+srv://<user>:<password>@cluster.mongodb.net/jwt_auth_app?appName=Cluster
```

### Running the Application Server
```powershell
py run.py
```
Access the UI at `http://localhost:5000/`.

### Running Automated Unit Tests
Unit tests use `pytest` and `mongomock` (in-memory MongoDB simulation):
```powershell
py -m pytest
```

---

## 7. Guidelines for AI Agents Modifying This Codebase

- **Database Access:** Always access collections via `users_collection` and `fellows_collection` imported from `extensions.py`. Do NOT instantiate `MongoClient()` directly in route handlers or module roots.
- **ObjectId Conversion:** Always use `parse_oid(id_string)` or wrap `ObjectId()` calls in `try...except InvalidId` to maintain API safety contract.
- **Timestamps:** Always use `datetime.datetime.now(datetime.timezone.utc)` for dates and JWT payloads. Do NOT use deprecated `datetime.utcnow()`.
- **Test Integrity:** Ensure all 15 unit tests pass (`py -m pytest`) after making modifications.
