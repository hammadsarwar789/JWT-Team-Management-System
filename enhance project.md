# Project Enhancements & Future Roadmap

## Overview

This document outlines the planned improvements for the **Team Management System**. These enhancements are intended to make the project production-ready, improve security, provide a better user experience, and demonstrate advanced backend development skills.

---

# Objectives

The current project already supports:

- User Registration
- User Login
- JWT Authentication
- User Profile
- Fellow Management

The next phase focuses on improving:

- Security
- Scalability
- Maintainability
- Performance
- User Experience

---

# Enhancement Roadmap

| Priority | Feature | Status |
|----------|----------|--------|
| High | Improve Folder Structure | Planned |
| High | User Roles & Permissions | Planned |
| High | Profile Picture Upload | Planned |
| High | Password Reset | Planned |
| High | Email Verification | Planned |
| High | Refresh Tokens | Planned |
| Medium | Search Fellows | Planned |
| Medium | Pagination | Planned |
| Medium | Sorting | Planned |
| Medium | Audit Logs | Planned |
| Medium | Dashboard | Planned |
| Medium | API Versioning | Planned |
| Medium | Logging | Planned |
| High | Automated Testing | Completed (Pytest + Mongomock) |
| Low | Nice-to-Have Features | Planned |

---

# 1. Improve Folder Structure

## Purpose
Separate business logic from routes and configuration into services, validators, models, and middleware layers.

```
jwt_auth_app/
├── app.py
├── config.py
├── extensions.py
├── auth/
│   ├── routes.py
│   ├── services.py
│   ├── validators.py
│   └── utils.py
├── profiles/
│   ├── routes.py
│   ├── services.py
│   └── validators.py
├── models/
│   ├── user.py
│   └── fellow.py
├── middleware/
│   ├── auth.py
│   └── logger.py
├── uploads/
├── tests/
├── static/
└── templates/
```

---

# 2. User Roles & Permissions (RBAC)

## Objective
Implement Role-Based Access Control (RBAC) supporting `Admin`, `Manager`, and `User` roles.

| Feature | Admin | Manager | User |
|----------|:-----:|:-------:|:----:|
| Manage Users | ✅ | ❌ | ❌ |
| Edit Own Profile | ✅ | ✅ | ✅ |
| Manage Fellows | ✅ | ✅ | Limited |
| Delete Fellows | ✅ | ✅ | ❌ |
| View Dashboard | ✅ | ✅ | ✅ |

---

# 3. Profile Picture Upload
- Support avatar image upload (`jpg`, `jpeg`, `png`, `webp`, max 5MB).
- Store files in `uploads/profile_images/` and save file path on user record.

---

# 4. Password Reset
- One-time reset tokens with expiration and email verification workflow.

---

# 5. Email Verification
- Send email verification links upon account creation before full activation.

---

# 6. Refresh Tokens
- Implement dual-token authentication: 30-minute Access Tokens + 7-day Refresh Tokens.

---

# 7. Search, 8. Pagination & 9. Sorting
- Add query parameters to `/api/fellows`: `GET /api/fellows?search=name&page=1&limit=10&sort=name&order=asc`.

---

# 10. Audit Logs
- Track user events (`LOGIN`, `LOGOUT`, `PASSWORD_CHANGE`, `PROFILE_UPDATE`, `FELLOW_ADDED`, `FELLOW_DELETED`).

---

# 11. Dashboard
- Overview dashboard displaying key statistics (Total Fellows, Account Status, Recent Activity).

---

# 12. API Versioning (`/api/v1/...`) & 13. File Logging (`logs/app.log`)

---

# 14. Automated Testing
- Completed! Pytest + Mongomock test suite in `tests/` with 15 passing unit tests.

---

# Recommended Development Order

- **Phase 1:** Folder Structure Refactoring, Services/Validators Layer, Roles & Permissions
- **Phase 2:** Refresh Tokens, Profile Images, Password Reset
- **Phase 3:** Search, Pagination, Sorting, Dashboard
- **Phase 4:** Audit Logs, API Versioning, Structured Logging
