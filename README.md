# 🔐 Task Manager API — with Authentication & Ownership

![CI](https://github.com/FidelCoder7/task-manager-auth/actions/workflows/ci.yml/badge.svg)

A REST API where every task belongs to an authenticated user. Combines JWT-based
authentication (register/login/refresh/logout, bcrypt password hashing) with a
task management system, enforcing strict per-user data isolation.

This project integrates two earlier portfolio projects — an [Auth System](https://github.com/FidelCoder7/Auth-system)
and a [Task Manager REST API](https://github.com/FidelCoder7/task-api) — into a
single production-style backend.

## Features

- User registration & login with JWT access/refresh tokens
- bcrypt password hashing
- Token blacklist (logout)
- Full task CRUD: create, read, update, delete, filter, search, paginate
- **Per-user data ownership** — users can only access their own tasks
- Ownership violations return `404` (not `403`), so other users' data isn't leaked
- SQLite + SQLAlchemy ORM
- 22 pytest tests covering auth, CRUD, and ownership isolation
- GitHub Actions CI.

## Tech Stack

Python · FastAPI · JWT (python-jose) · bcrypt · SQLAlchemy · SQLite · pytest

## Quick Start

```bash
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt
cp .env.example .env         # fill in your SECRET_KEY
uvicorn app.main:app --reload
```

Visit `http://localhost:8000/docs` for interactive API docs.

## API Endpoints

| Method | Endpoint | Auth Required | Description |
|--------|----------|----------------|-------------|
| POST | `/auth/register` | No | Create account |
| POST | `/auth/login` | No | Login, get tokens |
| POST | `/auth/refresh` | No | New access token |
| POST | `/auth/logout` | No | Blacklist refresh token |
| GET | `/tasks/` | Yes | List your tasks (filter/search/paginate) |
| POST | `/tasks/` | Yes | Create a task |
| GET | `/tasks/summary` | Yes | Task counts by status |
| GET | `/tasks/{id}` | Yes | Get one task (yours only) |
| PUT | `/tasks/{id}` | Yes | Update a task (yours only) |
| DELETE | `/tasks/{id}` | Yes | Delete a task (yours only) |

## Ownership Model

Every task has a `user_id`. All `/tasks` endpoints require a JWT access token,
and every query is scoped to `current_user.id`. Attempting to access another
user's task by ID returns `404 Not Found` — identical to a non-existent task,
so no information about other users' data is leaked.

## Running Tests

```bash
pytest tests/ -v
```

## Project Structure

```
app/
├── auth/            # password hashing, JWT, get_current_user dependency
├── routers/         # auth_routes.py, tasks.py
├── models.py        # User, Task (with user_id FK), TokenBlacklist
├── schemas.py        # Pydantic request/response models
├── crud.py            # user-scoped database operations
├── database.py
├── config.py
└── main.py
tests/
├── conftest.py
├── test_auth.py
├── test_jwt.py
└── test_tasks.py
```
