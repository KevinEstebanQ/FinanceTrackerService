# FinanceTrackerService

A finance tracker backend service built with **FastAPI** and a **SQL database**.

## What this repo is
FinanceTrackerService is a backend API intended to power a personal finance tracker (users + financial data), with a FastAPI service layer and a relational database behind it. The repository currently includes:
- `app/` — application source code
- `.env.shared` — shared environment defaults / examples
- `finance.db` — a local SQLite database file (useful for quick local testing)
- `requirements.txt` — Python dependencies

---

##  Tech Stack (expected)
- **FastAPI** (REST API)
- **Pydantic** (request/response validation)
- **SQLAlchemy** (ORM)
- **SQLite** by default (via `finance.db` / `DATABASE_URL`)
- Auth: password hashing + JWT-style authentication (if enabled in `app/`)

---

## Quickstart

### 1) Create a virtual environment
```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate
```

### 2) Install dependencies
```bash
pip install -r requirements.txt
```

### 3) Configure environment variables
Create a `.env` file in the project root. Use `.env.shared` as a reference.

### 4) Run the API (dev)
From the repo root:
```bash
uvicorn app.main:app --reload
```

Then open:
- Swagger UI: `http://127.0.0.1:8000/docs`

---

## Database notes

### SQLite (default)
- The repo includes `finance.db` for local development.
- If you want a clean start, you can delete `finance.db` and let your app recreate tables (depending on how `app/` is configured).

---

## API Overview
Once running, the API endpoints are documented automatically in `/docs`.
TBD

### Common commands
```bash
# Run server
uvicorn app.main:app --reload

# Freeze deps (optional)
pip freeze > requirements.txt
```

---

## Roadmap (suggested)
- [ ] Add missing endpoint
- [ ] Add Docker + docker-compose (API + DB)
- [ ] Add test suite (pytest) + CI (GitHub Actions)
- [ ] Add role-based access / refresh tokens (if needed)
- [ ] Add OpenAPI tags + examples for nicer docs

---

## Author
KevinEstebanQ
