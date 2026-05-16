# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Architecture

Two independent FastAPI microservices share a single PostgreSQL database (`finance_tracker`) in Docker Compose:

- **`auth-service/`** (port 8081) — user registration, JWT access tokens, hashed refresh tokens, session management.
- **`Transactions/`** (port 8080) — transaction CRUD, requires a valid JWT issued by auth-service.

Each service follows the same internal layout:
- `main.py` — FastAPI app instantiation and all route definitions.
- `models/` — SQLAlchemy ORM table definitions.
- `schemas/` — Pydantic v2 request/response models.
- `crud/` — database query logic (called from routes).
- `api/deps.py` — FastAPI dependencies (`get_db`, `get_current_user`, `dev_access`).
- `core/config.py` — loads env vars; `core/security.py` — JWT and password helpers.
- `db/session.py` — SQLAlchemy engine + `SessionLocal`; `db/base.py` — declarative `Base`.
- `init_db.py` — called at startup to run `Base.metadata.create_all()`.

### Auth flow

1. Client POSTs credentials to `auth-service /auth/login` → receives an access token (short-lived JWT) and a refresh token (random URL-safe bytes).
2. The refresh token is stored as a SHA-256 + pepper hash in `auth_sessions`.
3. Transactions service decodes the JWT locally using the shared `SECRET_KEY`, then calls `auth-service GET /users/email/{email}` (via `httpx`) to retrieve the full user record. The env var `AUTH_SERVICE_URL` controls this URL (default: `http://auth-service:8081`).
4. Login invalidates all prior active sessions for the user before creating a new one.

## Configuration

Config is merged in this priority order (highest wins): OS env → `.env` (local secrets, gitignored) → `.env.shared` (committed base values).

Both services load config from the repo root (`../.env` and `../.env.shared` relative to each service directory). Key variables:

| Variable | Purpose |
|---|---|
| `DATABASE_URL` | SQLAlchemy URL; defaults to SQLite locally, set to `postgresql+psycopg://...` for Postgres |
| `SECRET_KEY` | Used for JWT signing and refresh token pepper — must match across both services |
| `ALGORITHM` | JWT algorithm (default `HS256`) |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | JWT TTL (default `30`) |
| `REFRESH_TOKEN_EXPIRE_DAYS` | Refresh session TTL (default `7`) |
| `AUTH_SERVICE_URL` | Transactions → auth-service base URL |
| `DEVELOPMENT` | Set to `True` to enable dev mode |

## Running the services

### Docker Compose (recommended)

```bash
# Start all services (PostgreSQL + both APIs)
docker compose up --build

# Full reset (deletes DB volume)
docker compose down -v
```

### Local dev (per service)

```bash
cd auth-service   # or Transactions
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8081   # 8080 for Transactions
```

Interactive docs are at `/docs` on each service's port.

## Database

Tables are created automatically at startup via `init_db()` — there is no migration tool (Alembic is the recommended next step). To reset the DB locally, drop the Docker volume (`docker compose down -v`) or delete the SQLite file.

The `Transactions` service stores `user_id` as a plain integer with no FK constraint to `users`; the relationship is enforced at the application layer via the auth-service HTTP call in `get_current_user`.
