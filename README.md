# JWT Auth App (Flask + MongoDB)

Sign up, sign in, edit your profile, and add "fellows" (other people linked
to your account) — with JWT-based authentication.

## 1. Install MongoDB (if you don't have it)

- **WSL/Linux:** `sudo apt install -y mongodb` or use a free
  [MongoDB Atlas](https://www.mongodb.com/atlas) cluster and paste its
  connection string into `.env`.
- Make sure `mongod` is running locally, or that your Atlas URI is reachable.

## 2. Set up the project

```bash
cd jwt_auth_app
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# edit .env: set SECRET_KEY to a long random string, and MONGO_URI if needed
```

## 3. Run it

```bash
python run.py
```

Visit `http://localhost:5000` in your browser. You'll land on the sign-in
page; use "Sign up" to create an account first.

## 4. API reference (for testing with curl/Postman)

| Method | Endpoint             | Auth required | Body                                   |
|--------|-----------------------|:---:|-----------------------------------------|
| POST   | /api/auth/signup      | No  | `username, email, password`             |
| POST   | /api/auth/signin      | No  | `email, password`                       |
| GET    | /api/profile          | Yes | —                                       |
| PUT    | /api/profile          | Yes | any of `username, full_name, bio`       |
| POST   | /api/fellows          | Yes | `name, email?, relation?, notes?`       |
| GET    | /api/fellows          | Yes | —                                       |
| PUT    | /api/fellows/<id>     | Yes | any of `name, email, relation, notes`   |
| DELETE | /api/fellows/<id>     | Yes | —                                       |

"Auth required" means sending header: `Authorization: Bearer <token>`
(the token comes back from signup/signin).

Example:

```bash
curl -X POST http://localhost:5000/api/auth/signup \
  -H "Content-Type: application/json" \
  -d '{"username":"hammad","email":"hammad@example.com","password":"secret123"}'

curl http://localhost:5000/api/profile \
  -H "Authorization: Bearer <token from signup response>"
```

## Project structure

```
jwt_auth_app/
├── app.py              # Flask app factory, registers blueprints + page routes
├── run.py               # entry point (loads .env, starts the server)
├── config.py            # SECRET_KEY, MONGO_URI, token expiry
├── extensions.py        # MongoDB client + collections
├── auth/
│   ├── routes.py         # POST /api/auth/signup, /api/auth/signin
│   └── utils.py          # generate_token, decode_token, @token_required
├── profiles/
│   └── routes.py         # profile GET/PUT, fellows CRUD
├── templates/            # signin.html, signup.html, profile.html
└── static/style.css
```

## Security notes before deploying this for real

- Never commit `.env` or a real `SECRET_KEY` to version control.
- This demo stores the JWT in `localStorage`, which is simplest for
  learning but vulnerable to XSS. For production, prefer an httpOnly
  cookie.
- Add rate limiting to `/signin` to slow down brute-force guessing.
- Consider short-lived access tokens + a refresh token if you want
  users to stay signed in for a long time without one long-lived token.
