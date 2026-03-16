# FinanceTrackerService

A finance tracker backend service built with FastAPI and SQLAlchemy.

## Tech stack
- FastAPI
- SQLAlchemy
- SQLite (default)
- PostgreSQL-ready configuration

## Local run (without Docker)
1. Create and activate a virtual environment.
```bash
python -m venv .venv
source .venv/bin/activate
```
2. Install dependencies.
```bash
pip install -r requirements.txt
```
3. Create `.env` from `.env.shared` and adjust values.
4. Run the API.
```bash
uvicorn app.main:app --reload
```
5. Open docs at `http://127.0.0.1:8000/docs`.

## Docker Compose (SQLite persistent)

`docker-compose.yml` runs the API and stores SQLite data in a named Docker volume (`sqlite_data`). This means API image rebuilds do not delete DB data.

Run:
```bash
docker compose up --build
```

API URL:
- `http://localhost:8080`
- `http://localhost:8080/docs`

Stop:
```bash
docker compose down
```

Stop and delete SQLite volume (full reset):
```bash
docker compose down -v
```

## PostgreSQL migration path

This repo now includes `docker-compose.postgres.yml` as an override. It adds a `db` (PostgreSQL) service and points the API to Postgres.

Run API + Postgres:
```bash
docker compose -f docker-compose.yml -f docker-compose.postgres.yml up --build
```

Notes:
- SQLAlchemy URL for Postgres is `postgresql+psycopg://...`
- `requirements.txt` includes `psycopg[binary]` for the DB driver.
- Existing SQLite data does not auto-migrate. If you need data migration, add Alembic and run a one-time transfer script.

## Recommended next migration steps
1. Add Alembic for schema versioning.
2. Create an initial migration from current models.
3. Add dev/prod env files with distinct `DATABASE_URL` values.
4. Add a seed/migration script if you need to copy SQLite data into Postgres.

## Author
KevinEstebanQ
