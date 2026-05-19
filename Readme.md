# FinanceTrackerService

A personal finance backend built as a microservices system using FastAPI, PostgreSQL, and Docker. Designed as a portfolio project to demonstrate production-aware backend patterns: JWT auth with refresh token rotation, session revocation, Alembic-managed migrations, and cloud deployment on Railway.

---

## Architecture

```
┌─────────────────────┐        ┌────────────────────────┐
│    auth-service     │        │  transactions-service  │
│      :8081          │        │        :8080           │
│                     │        │                        │
│  - Registration     │◄───────│  - JWT validation      │
│  - Login / Logout   │  HTTP  │  - Create transaction  │
│  - Token refresh    │        │  - List transactions   │
│  - Session mgmt     │        │                        │
└────────┬────────────┘        └───────────┬────────────┘
         │                                 │
         └──────────────┬──────────────────┘
                        │
               ┌────────▼────────┐
               │  PostgreSQL 16  │
               │                 │
               │  users          │
               │  auth_sessions  │
               │  transactions   │
               └─────────────────┘
```

Both services share one PostgreSQL database but manage their own schema migrations independently via separate Alembic version tables (`alembic_version_auth`, `alembic_version_transactions`).

---

## Services

### auth-service — port 8081

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Service health and environment status |
| `POST` | `/users` | Register a new user |
| `POST` | `/auth/login` | OAuth2 login — returns access + refresh tokens |
| `POST` | `/auth/refresh` | Exchange refresh token for a new token pair |
| `POST` | `/auth/logout` | Revoke an active refresh session |
| `GET` | `/me` | Current authenticated user profile |
| `GET` | `/protected/ping` | Protected heartbeat (auth enforcement check) |
| `GET` | `/users/email/{email}` | Lookup user by email (inter-service use) |

### transactions-service — port 8080

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Service health and environment status |
| `GET` | `/info` | API metadata and message of the day |
| `POST` | `/transactions` | Create a new transaction (JWT-protected) |
| `GET` | `/transactions/user` | List all transactions for current user (JWT-protected) |
| `GET` | `/` | Redirect to `/docs` |

Interactive docs (Swagger UI) are available at `/docs` on each service.

---

## Security Design

- **JWT access tokens** — HS256-signed, short-lived (configurable via `ACCESS_TOKEN_EXPIRE_MINUTES`)
- **Refresh tokens** — cryptographically random (`secrets.token_urlsafe(32)`), stored as `SHA-256 + pepper` hash (never plain-text), validated with `secrets.compare_digest` to prevent timing attacks
- **Session revocation on login** — all active sessions for a user are bulk-revoked before issuing a new one, preventing concurrent session reuse
- **bcrypt** password hashing via passlib
- **IP logging** on every session creation
- **CORS middleware** configured on auth-service

---

## Local Development (Docker Compose)

**Prerequisites:** Docker and Docker Compose installed.

```bash
git clone <repo>
cd FinanceTrackerService
```

Copy the shared config and adjust values if needed:
```bash
cp .env.shared .env
```

Start all three containers (auth-service, transactions-service, PostgreSQL):
```bash
docker compose up --build
```

| Service | URL |
|---|---|
| transactions-service | http://localhost:8080 / http://localhost:8080/docs |
| auth-service | http://localhost:8081 / http://localhost:8081/docs |
| PostgreSQL | localhost:5432 |

Stop:
```bash
docker compose down
```

Full reset (drop database volume):
```bash
docker compose down -v
```

### How startup works

Each service runs `alembic upgrade head` before starting Uvicorn (via `Entrypoint.sh`). The database schema is fully migration-managed — no `create_all()` at startup.

---

## Environment Variables

Configuration is loaded from `.env.shared` (committed, used as a template by Railway) and `.env` (gitignored, local overrides). `os.environ` always takes precedence over file values.

| Variable | Description | Local default |
|---|---|---|
| `DATABASE_URL` | SQLAlchemy connection string | `postgresql+psycopg://finance_user:finance_pass@db:5432/finance_tracker` |
| `SECRET_KEY` | JWT signing key and refresh token pepper | `CHANGE-ME` |
| `ALGORITHM` | JWT algorithm | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Access token lifetime | `30` |
| `REFRESH_TOKEN_EXPIRE_DAYS` | Refresh token lifetime | `7` |
| `AUTH_SERVICE_URL` | Transactions → auth-service base URL | `http://auth-service:8081` |
| `AUTH_TOKEN_URL` | OAuth2 tokenUrl for Swagger UI | `http://localhost:8081/auth/login` |
| `DEVELOPMENT` | Enables dev mode flags | `True` |

> **Note:** `DATABASE_URL` must use the `postgresql+psycopg://` scheme (psycopg v3). Railway's Postgres plugin generates `postgresql://` — add `+psycopg` manually in the Railway dashboard.

---

## Cloud Deployment (Railway)

The project is deployed on Railway with three services:

| Railway Service | Source directory | Live URL |
|---|---|---|
| auth-service | `auth-service/` | https://graceful-caring-production-296f.up.railway.app |
| transactions-service | `Transactions/` | https://transactions-production-2dc9.up.railway.app/docs |
| PostgreSQL | Railway plugin | — |

Each service is built from its own Dockerfile. Railway injects a dynamic `PORT` — both entrypoints are configured to use it (`${PORT:-808x}`).

---

## Tech Stack

| | |
|---|---|
| Language | Python 3.12 |
| Web framework | FastAPI 0.128.0 |
| ORM | SQLAlchemy 2.0.45 |
| Migrations | Alembic 1.18.4 |
| DB driver | psycopg 3.2.12 (binary) |
| Database | PostgreSQL 16 |
| Auth / JWT | python-jose 3.5.0 |
| Password hashing | passlib 1.7.4 (bcrypt) |
| Inter-service HTTP | httpx 0.27.0 |
| Data validation | Pydantic v2 2.12.5 |
| ASGI server | Uvicorn 0.40.0 + uvloop 0.22.1 |
| Containerization | Docker + Docker Compose |
| Dependency management | pyproject.toml + uv.lock |
| Load testing | Locust 2.44.0 |

---

## Author

Kevin Esteban Quiceno — [GitHub](https://github.com/KevinEstebanQ)
