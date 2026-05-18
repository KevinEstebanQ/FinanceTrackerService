# Performance Benchmark Results

Each row is one locust run. Raw CSV + HTML reports live in `results/<date>_<label>/`.

## Checkpoints

| # | Label | Trigger | Expected improvement |
|---|-------|---------|----------------------|
| 1 | `baseline` | Before Phase 1 (current state) | — |
| 2 | `after-jwt-fix` | After embedding user claims in JWT (Phase 1) | ↓ latency on authenticated Transactions endpoints — eliminates per-request HTTP call to auth-service |
| 3 | `after-redis` | After adding Redis user-lookup cache (Phase 3) | ↓ latency on repeated requests for the same user |
| 4 | `after-observability` | After Prometheus + structured logging (Phase 6) | Confirm no regression; use Grafana dashboards as living proof |

---

## Results

### GET /transactions/user (most representative — authenticated, inter-service dependency)

| Date | Label | Users | RPS | p50 (ms) | p95 (ms) | p99 (ms) | Fail % | Notes |
|------|-------|-------|-----|----------|----------|----------|--------|-------|
| 2026-05-16 | baseline | 50 | 79.2 | 70 | 180 | 240 | 0% | Pre Phase-1; per-request HTTP call to auth-service on every GET |
| — | after-jwt-fix | 50 | | | | | | |
| — | after-redis | 50 | | | | | | |

### POST /transactions

| Date | Label | Users | RPS | p50 (ms) | p95 (ms) | p99 (ms) | Fail % | Notes |
|------|-------|-------|-----|----------|----------|----------|--------|-------|
| 2026-05-16 | baseline | 50 | 30.6 | 87 | 210 | 260 | 0% | Pre Phase-1 |
| — | after-jwt-fix | 50 | | | | | | |
| — | after-redis | 50 | | | | | | |

### POST /auth/login

| Date | Label | Users | RPS | p50 (ms) | p95 (ms) | p99 (ms) | Fail % | Notes |
|------|-------|-------|-----|----------|----------|----------|--------|-------|
| 2026-05-16 | baseline | 50 | 28.3 | 360 | 530 | 640 | 0% | High latency expected — bcrypt hashing on every login |
| — | after-redis | 50 | | | | | | |

### POST /auth/refresh

| Date | Label | Users | RPS | p50 (ms) | p95 (ms) | p99 (ms) | Fail % | Notes |
|------|-------|-------|-----|----------|----------|----------|--------|-------|
| 2026-05-16 | baseline | 50 | 13.6 | 55 | 170 | 290 | 0% | Fast — DB lookup only, no bcrypt |
| — | after-redis | 50 | | | | | | |

---

## Calculated Improvements

Fill these in after collecting checkpoint 1 and 2+ results.

### Phase 1 — JWT fix

```
GET /transactions/user p95 improvement:
  baseline p95:       _____ ms
  after-jwt-fix p95:  _____ ms
  reduction:          _____ ms  (~____%)

RPS improvement:
  baseline RPS:       _____
  after-jwt-fix RPS:  _____
  increase:           _____ (~____%)
```

### Phase 3 — Redis cache

```
GET /transactions/user p95 improvement:
  after-jwt-fix p95:  _____ ms
  after-redis p95:    _____ ms
  reduction:          _____ ms  (~____%)
```

---

## Resume Bullet Templates

Copy the best-fitting template once you have real numbers.

> Eliminated per-request inter-service HTTP calls by embedding user identity as JWT claims, reducing authenticated API p95 latency by **X%** (measured with Locust at 50 concurrent users).

> Implemented Redis caching for user lookups in a FastAPI microservice, improving authenticated endpoint p95 response time by **X%** and increasing throughput from X to Y req/s.

> Designed and load-tested a two-service FastAPI architecture (auth + transactions) achieving **X req/s** at p99 < **Y ms** under 50 concurrent users.

> Built an automated performance regression suite using Locust; tracked latency improvements across three architectural milestones (JWT refactor, Redis caching), producing a documented audit trail of measurable gains.
