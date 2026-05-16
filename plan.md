# FinanceTrackerService — Project Plan

Goal: transform this into a fullstack, deployable portfolio project that signals production-awareness to interviewers.

Collaboration model: you implement each phase yourself; use Claude for code review, targeted snippets, and guidance when stuck.

---

## Current state assessment

**Already solid:**
- Microservice separation (auth-service + Transactions) is real and correct
- JWT + refresh token + session revocation is non-trivial — most portfolio projects skip this
- Docker Compose setup is clean
- FastAPI patterns (deps, schemas, crud, models) are correctly structured

**Needs fixing before anything else:**
- No tests
- No migrations — `create_all` at startup is a dev-only pattern, a red flag to interviewers
- Config loaded with raw `dotenv_values` instead of typed Pydantic Settings
- `Transactions` service makes an HTTP call to `auth-service` on every authenticated request — latency problem and the wrong JWT pattern
- `Transactions/models/user.py` is a copy of auth-service's model and shouldn't exist
- No logging, no request IDs, no structured error responses
- `get_user_transactions` has a hardcoded `limit=10` with no pagination

---

## Phase 1 — Foundation

> These fixes transform "student project" into "production-aware". Do these before adding any new features.

| Task | Why it matters |
|---|---|
| **Alembic migrations** | Every real project uses this. `create_all` at startup is a red flag. |
| **Pydantic Settings v2** | Typed, validated config — interviewers know the difference from raw dotenv. |
| **Fix the JWT pattern** | Embed `user_id` and `is_active` as JWT claims. Transactions decodes the token locally — zero HTTP call to auth-service needed per request. The duplicated user model goes away. |
| **Structured logging** | `loguru` or `structlog` with request ID middleware. One log line should tell the full story of a request. |
| **Standardize error responses** | Every error returns a consistent shape: `{"detail": "...", "code": "..."}`. |
| **Pagination** | `get_user_transactions` needs `limit` + `offset` (or cursor) query params — never hardcode a limit. |

---

## Phase 2 — Testing

> The biggest interview differentiator. Most portfolio projects have zero tests.

- `pytest` + `httpx` `AsyncClient` for route-level tests
- Fixtures that spin up an isolated test database (SQLite in-memory or a separate Postgres schema)
- Unit tests: `core/security.py`, all `crud/` functions
- Integration tests: full request/response cycles for every endpoint
- `pytest-cov` with 80%+ coverage target
- Coverage badge in README

---

## Phase 3 — Caching & Resilience

- **Redis** added to Docker Compose — cache user lookups with a short TTL (60s)
- **Rate limiting** with `slowapi` on auth endpoints (login, register) — 5 req/min is a standard starting point
- Optional: circuit breaker pattern on any remaining inter-service HTTP calls

---

## Phase 4 — CI/CD

> The "wow" factor for a solo project. Most candidates don't have this.

- **GitHub Actions pipeline** triggered on every push:
  1. `ruff` lint
  2. `mypy` type check
  3. `pytest` with coverage
  4. Build Docker image
- **Push image to GitHub Container Registry (GHCR)** — free, no setup required
- **Deploy to Railway or Render** — live HTTPS URL from GHCR with minimal DevOps overhead. This is the URL that goes on your resume.

---

## Phase 5 — Frontend

> Study Next.js App Router basics before starting. Spend a weekend with the docs before asking for help implementing.

- Next.js 14+ with App Router, TypeScript, Tailwind CSS
- Auth flow: login/register pages, access token in memory, refresh token in `httpOnly` cookie
- Transaction list view + create transaction form
- Dashboard with summary charts (Recharts — easiest, looks great)

---

## Phase 6 — Observability (stretch)

> Adds 30 minutes of work but looks impressive in a live demo.

- Prometheus `/metrics` endpoint on each service (`prometheus-fastapi-instrumentator`)
- Grafana added to Docker Compose to visualize metrics
- Structured log correlation using request IDs across services

---

## Final technology stack

| Layer | Technology |
|---|---|
| Backend | FastAPI, SQLAlchemy 2, Pydantic v2 |
| Database | PostgreSQL + Alembic |
| Cache | Redis |
| Auth | JWT (python-jose) + bcrypt |
| Testing | pytest, httpx, pytest-cov |
| Lint / types | ruff, mypy |
| CI/CD | GitHub Actions → GHCR → Railway |
| Frontend | Next.js 14, TypeScript, Tailwind CSS, Recharts |
| Observability | structlog, Prometheus, Grafana |

---

## Starting point: Phase 1, Task 1 — Alembic

Set up Alembic inside `auth-service/` to manage the `users` and `auth_sessions` tables. The tricky part is wiring it to `DATABASE_URL` from your `.env`. Once you have a first attempt, bring it for review.
