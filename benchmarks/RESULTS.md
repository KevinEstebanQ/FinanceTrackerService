# Performance Benchmark Results

Each row is one locust run. Raw CSV + HTML reports live in `results/<date>_<label>/`.

## Checkpoints

| # | Label | Trigger | Expected improvement |
|---|-------|---------|----------------------|
| 1 | `baseline` | Before Phase 1 (current state) | — |
| 2 | `after-jwt-fix` | After embedding user claims in JWT + async SQLAlchemy | ↓ latency on authenticated Transactions endpoints — eliminates per-request HTTP call to auth-service |
| 3 | `after-async-bcrypt` | After offloading bcrypt to thread pool | Event loop unblocked during hashing — higher concurrency ceiling |
| 4 | `after-redis` | After adding Redis user-lookup cache (Phase 3) | ↓ latency on repeated requests for the same user |
| 5 | `after-observability` | After Prometheus + structured logging (Phase 6) | Confirm no regression; use Grafana dashboards as living proof |

---

## Results

### GET /transactions/user (most representative — authenticated, inter-service dependency)

| Date | Label | Users | RPS | p50 (ms) | p95 (ms) | p99 (ms) | Fail % | Notes |
|------|-------|-------|-----|----------|----------|----------|--------|-------|
| 2026-05-16 | baseline | 50 | 79.2 | 70 | 180 | 240 | 0% | Pre Phase-1; per-request HTTP call to auth-service on every GET |
| 2026-05-20 | after-jwt-fix | 150 | 103.1 | 73 | 300 | 450 | 0% | JWT claims embedded; async SQLAlchemy; 3× concurrency vs baseline |
| 2026-05-20 | after-async-bcrypt | 300 | 163.3 | 180 | 3100 | 5100 | 0% | bcrypt in thread pool; 6× concurrency vs baseline; previously 84% fail rate at 300u |
| 2026-05-20 | after-workers | 300 | 348.7 | 110 | 330 | 470 | 0% | 4 Uvicorn workers (`UVICORN_WORKERS=4`); p95 dropped 89% (3.1s → 330ms); 555 total req/s aggregated |
| 2026-05-20 | after-redis | 300 | 347.4 | 100 | 320 | 440 | 0% | Redis on auth `get_current_user`; transactions flat (no txn cache yet); auth `/me` p50 dropped 96% (1100ms → 41ms) |

### POST /transactions

| Date | Label | Users | RPS | p50 (ms) | p95 (ms) | p99 (ms) | Fail % | Notes |
|------|-------|-------|-----|----------|----------|----------|--------|-------|
| 2026-05-16 | baseline | 50 | 30.6 | 87 | 210 | 260 | 0% | Pre Phase-1 |
| 2026-05-20 | after-jwt-fix | 150 | 41.2 | 90 | 340 | 530 | 0% | 3× concurrency vs baseline |
| 2026-05-20 | after-async-bcrypt | 300 | 65.5 | 220 | 2900 | 4900 | 0% | 6× concurrency vs baseline |
| 2026-05-20 | after-workers | 300 | 137.7 | 150 | 390 | 510 | 0% | 4 workers; p95 dropped 87% (2.9s → 390ms) |
| 2026-05-20 | after-redis | 300 | 140.2 | 140 | 370 | 490 | 0% | Marginal improvement — no transaction-level caching yet |

### POST /auth/login

| Date | Label | Users | RPS | p50 (ms) | p95 (ms) | p99 (ms) | Fail % | Notes |
|------|-------|-------|-----|----------|----------|----------|--------|-------|
| 2026-05-16 | baseline | 50 | 28.3 | 360 | 530 | 640 | 0% | High latency expected — bcrypt hashing on every login |
| 2026-05-20 | after-redis | 300 | 31.0 | 4400 | 8600 | 11000 | 0% | Bcrypt-dominated; Redis doesn't help login — expected |

### POST /auth/refresh

| Date | Label | Users | RPS | p50 (ms) | p95 (ms) | p99 (ms) | Fail % | Notes |
|------|-------|-------|-----|----------|----------|----------|--------|-------|
| 2026-05-16 | baseline | 50 | 13.6 | 55 | 170 | 290 | 0% | Fast — DB lookup only, no bcrypt |
| 2026-05-20 | after-redis | 300 | 14.4 | 3000 | 6600 | 10000 | 0% | High latency at 300u — refresh queries auth_sessions, not cached |

### GET /me (auth-service)

| Date | Label | Users | RPS | p50 (ms) | p95 (ms) | p99 (ms) | Fail % | Notes |
|------|-------|-------|-----|----------|----------|----------|--------|-------|
| 2026-05-20 | after-workers | 300 | 70.0 | 1100 | 3200 | 5100 | 0% | DB hit on every request — no cache |
| 2026-05-20 | after-redis | 300 | 73.7 | 41 | 300 | 3700 | 0% | Redis cache hit; p50 dropped 96% (1100ms → 41ms), p95 dropped 91% (3200ms → 300ms) |

---

## Calculated Improvements

Fill these in after collecting checkpoint 1 and 2+ results.

### Phase 1 — JWT fix + async SQLAlchemy

Note: after-jwt-fix ran at 150 users (3× baseline concurrency) — direct ms comparison overstates regression; the story is throughput and stability at scale.

```
GET /transactions/user RPS:
  baseline (50 users):        79.2 req/s
  after-jwt-fix (150 users): 103.1 req/s  (+30% throughput at 3× load)

GET /transactions/user p50:
  baseline:       70ms
  after-jwt-fix:  73ms   (flat despite 3× concurrency)

Failure rate:
  baseline (150 users):       crashed — SQLAlchemy pool exhaustion
  after-jwt-fix (150 users):  0%
```

### Phase 1 extended — async bcrypt

Note: ran at 300 users (6× baseline concurrency). Previously 84% failure rate at 300 users.

```
GET /transactions/user RPS:
  baseline (50 users):              79.2 req/s
  after-async-bcrypt (300 users):  163.3 req/s  (+106% throughput at 6× load)

Total aggregated RPS (all endpoints):
  baseline (50 users):              ~50 req/s estimated
  after-async-bcrypt (300 users):  261 req/s

Failure rate at 300 users:
  before any fixes:    84%
  after-async-bcrypt:  0%

p95 at 300 users: 3.1s — single Uvicorn worker ceiling.
Next lever: --workers 4 → expected ~800ms p95 at same load.
```

### Phase 1 extended — Uvicorn multi-worker (after-workers)

Note: ran at 300 users with 4 workers (`UVICORN_WORKERS=4`). Same concurrency as after-async-bcrypt.

```
GET /transactions/user RPS:
  after-async-bcrypt (1 worker):  163.3 req/s
  after-workers (4 workers):      348.7 req/s  (+113% throughput at same 300-user load)

GET /transactions/user p95:
  after-async-bcrypt:  3100ms
  after-workers:        330ms  (-89% — exceeded the ~800ms target)

POST /transactions p95:
  after-async-bcrypt:  2900ms
  after-workers:        390ms  (-87%)

Total aggregated RPS (transactions service):
  after-async-bcrypt:  261 req/s
  after-workers:       555 req/s  (+113%)

Failure rate: 0% (unchanged — workers added throughput, not stability)
```

### Phase 1 extended — Redis user cache (after-redis)

Redis caches `get_current_user` result in auth-service. Key: `user:email:{email}`, TTL 300s, stored as Redis hash. Cache populated on first authenticated request per user; subsequent requests skip the DB entirely.

```
GET /me p50 (auth-service):
  after-workers (no cache):  1100ms
  after-redis (cache hit):     41ms  (-96%)

GET /me p95 (auth-service):
  after-workers:  3200ms
  after-redis:     300ms  (-91%)

GET /transactions/user (transactions-service):
  after-workers:  348.7 req/s, p95=330ms
  after-redis:    347.4 req/s, p95=320ms  (flat — no transaction-level caching yet)

Note: login/refresh latency unchanged — bcrypt and session DB writes are not cacheable.
```

> Resume bullet: Implemented Redis hash caching for authenticated user lookups in FastAPI using a connection pool (lifespan) + per-request dependency injection pattern, reducing GET /me p50 from 1100ms to 41ms (-96%) and p95 from 3200ms to 300ms (-91%) at 300 concurrent users.

---

## Resume Bullet Templates

> Eliminated per-request inter-service HTTP calls by embedding user identity as signed JWT claims, enabling the Transactions service to authenticate requests locally with zero network round-trips.

> Migrated two FastAPI microservices from synchronous to async SQLAlchemy (create_async_engine + AsyncSession), eliminating connection pool exhaustion that previously caused 100% failure rate at 150 concurrent users.

> Offloaded bcrypt password hashing to a thread pool via asyncio.to_thread, unblocking the async event loop during CPU-bound operations and enabling clean handling of 300 concurrent users (previously 84% failure rate).

> Load-tested a two-service FastAPI architecture with Locust across three concurrency levels (50 → 150 → 300 users), achieving 163 req/s on the core authenticated endpoint at 6× baseline concurrency with 0% failure rate.

> Built a checkpoint-based performance regression suite tracking architectural improvements (JWT refactor, async DB, async bcrypt) with quantified before/after results at each milestone.
