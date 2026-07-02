# DeliverIQ — Interview Prep & Concept Guide

> A self-study reference for everything built so far. Each topic has: **the concept (why)**,
> the **interview soundbite** (how to say it out loud), and the **gotcha** (what trips people up).
> If you can explain every soundbite without looking, you own the material.
>
> **Layout:** §1–2 frame the project (pitch + stack) — what an interviewer opens with.
> §3–8 are the backend concepts. §9 onward (Alembic, then Parts 2–5) go day-by-day in depth.

---

## 1. DeliverIQ — Project Talking Points

### The one-line pitch
> "A production-grade REST API that dispatches food-delivery orders to riders using priority queues, geohashing, rate limiting, and event streaming — FastAPI, Redis, Kafka, PostgreSQL, Docker."

### The differentiator: fairness-banded dispatch
Instead of naive nearest-rider, among riders within a distance band Δ of the nearest, assign the one with the **fewest orders today**.

- **"How is it different from Swiggy/Zomato?"** → "Theirs optimizes pure ETA. Mine adds a bounded fairness constraint — greedy-nearest reframed as a constrained assignment problem."
- **"What problem does it solve?"** → "Naive nearest-rider starves some riders and overloads others. Banding spreads earnings while Δ guarantees delivery SLA isn't sacrificed."
- **"Social impact?"** → "Fairer earnings for gig riders — an honest angle, no fabrication."
- **"Why a band, not a weighted score?"** → "A blended `α·dist + β·fairness` can silently send a far rider (cold food). The band makes the SLA guarantee explicit and tunable."

### DSA core (steer interviews here)
- **Priority queue** dispatch — O(log n) ordering.
- **Geohash** rider matching — O(1) grid-cell lookup vs O(n) scan.
- **Fairness band** — constrained assignment, a min-heap on a composite key.
- **State machine** — a directed graph of legal order transitions.
- These are the same nearest-neighbour shape as the FAISS work in SemanticCache.

### Honest framing
"It's a pattern-aware portfolio project where I went deep on the engineering and trade-offs — not production experience. I can speak to every design decision and what I'd change at scale."

---

## 2. Tech Stack — Why These, and the Alternatives

> Interviewers ask "why did you choose X?" to check whether you **decided** or just
> copied a tutorial. The strong answer always names the **trade-off** and a credible
> alternative. Honest framing: part of the reason is fit, part is that these are the
> industry-standard tools my target companies (Uber, Razorpay, PhonePe) actually use.

### Python
- **Why:** fast to build, huge ecosystem, spans backend *and* AI/ML (matters for SemanticCache). The bottleneck here is I/O (DB, network), not CPU, so raw language speed isn't the constraint.
- **Alternatives:** **Go** (compiled, great concurrency — Uber uses it; faster but more verbose, weaker ML ecosystem). **Java/Spring** (enterprise-standard, mature, heavy boilerplate). **Node.js** (also great at I/O; Python won for the AI side).
- **Soundbite:** "I/O-bound service, so developer speed beat raw speed. Go would be faster but I wanted Python's ecosystem and the ML overlap with my second project."

### FastAPI (web framework)
- **Why:** async-first, validation built in via Pydantic, **auto-generated OpenAPI/Swagger docs**. Minimal boilerplate, type-hint driven.
- **Alternatives:** **Flask** (simpler but you bolt on validation/docs/async). **Django + DRF** (batteries-included, but heavy, less async-native — overkill for a focused API).
- **Soundbite:** "FastAPI gives me async, validation, and live docs out of the box. Flask is lighter but I'd rebuild those; Django is heavier than an API-first service needs."

### PostgreSQL (database)
- **Why:** ACID relational DB — orders and riders have clear relationships and I can't afford to lose an order. Rich SQL (window functions, indexes), JSON support, **PostGIS** for geospatial.
- **Alternatives:** **MySQL** (solid; Postgres wins on window functions, JSON, geospatial, stricter SQL). **MongoDB** (flexible schema, but my data is relational and needs consistency). **SQLite** (great for dev, not concurrent production load).
- **Soundbite:** "Structured, related data that needs consistency → relational + ACID. Postgres over MySQL for window functions and geospatial; over Mongo because losing an order isn't acceptable."

### SQLAlchemy (ORM)
- **Why:** most mature Python ORM, pairs cleanly with FastAPI, lets me write Python but drop to raw SQL when needed, database-agnostic.
- **Alternatives:** **Raw SQL via psycopg2** (max control, more boilerplate, injection risk if careless). **SQLModel** (newer, merges Pydantic + SQLAlchemy — less battle-tested). **Tortoise ORM** (async-native).
- **Trade-off:** ORMs add abstraction and can generate inefficient queries (N+1) — you trade some control for productivity.

### Pydantic (validation)
- **Why:** ships with FastAPI; declarative validation + serialization from type hints, structured error output.
- **Alternatives:** **marshmallow** (older, more manual), or hand-rolled. Pydantic is the modern standard.

### Redis (caching, rate limiting, rider state)
- **Why:** in-memory key-value, sub-millisecond, perfect for hot ephemeral state: rate-limit counters, rider locations, `orders_today`. TTLs, pub/sub, rich structures (sorted sets, geo, hashes).
- **Alternatives:** **Memcached** (simpler cache, no rich structures/persistence/pub-sub). **In-process memory** (doesn't work across instances — Redis is shared state).
- **Soundbite:** "Fast, shared, ephemeral state across app instances. Redis over Memcached for sorted sets and geo; over in-memory because that doesn't survive scaling horizontally."

### Kafka (event streaming) — *upcoming*
- **Why:** durable, high-throughput, replayable event log. Decouples producers from consumers — one order event fans out to notification, analytics, audit as independent consumer groups.
- **Alternatives:** **RabbitMQ** (great task queue, but Kafka wins on high-throughput streaming, replay, many independent consumers). **Redis Pub/Sub** (simple, not durable). **AWS SQS/SNS** (managed, ties you to AWS).
- **Soundbite:** "A durable, replayable log many consumers read independently — that's Kafka. RabbitMQ is a queue, not a log; Redis pub/sub isn't durable."

### Docker / Compose, Prometheus + Grafana — *upcoming*
- **Docker:** reproducible env, easy multi-service local setup, simple deploys. Alt: bare-metal/venv (not reproducible), Podman.
- **Prometheus + Grafana:** Prometheus scrapes metrics (pull), Grafana visualizes. Alt: Datadog/New Relic (paid SaaS), ELK (more for logs).

### The honest meta-answer
"Some of these (Kafka, Prometheus) are more than a small project strictly needs. I added them deliberately to learn the production patterns my target companies use, and I can defend each one's trade-off rather than just listing it."

---

## 3. REST & HTTP Basics

### Status codes — what they signal
- `200 OK` — success, here's the data.
- `201 Created` — success, a new resource was created (use for POST that creates).
- `400 Bad Request` — the request is well-formed but **illegal given current state** (e.g. an illegal order-status transition). *Your* logic raised it.
- `404 Not Found` — the resource doesn't exist.
- `422 Unprocessable Entity` — input failed **validation** (wrong type, missing field, constraint broken). FastAPI raises this automatically.
- `429 Too Many Requests` — rate limit exceeded (the token bucket).
- `503 Service Unavailable` — health check degraded (a dependency is down). *Upcoming, Day 38.*

**Soundbite:** "Status codes are the contract — a client decides success vs failure from the code, not the body. A missing resource is `404`, not a `200` with an error inside."

### 400 vs 422 — the distinction (learned at the state machine)
Both are "client's request didn't work," but they mean different things:
- **422** = *malformed* — the input doesn't match the declared shape. FastAPI/Pydantic raises it **automatically** at the boundary (`status="banana"` against an Enum).
- **400** = *well-formed but illegal* — the input is a valid shape, but doesn't make sense against current state (a legal-looking status that's an illegal *transition*). **You** raise it at runtime.

**Soundbite:** "422 is the type system rejecting a malformed request automatically; 400 is my own runtime check rejecting a well-formed but state-illegal one. Same family — different cause, different layer. 'Type it if you can, raise it if you must.'"

### HTTP verbs — and choosing them by *semantics*, not habit
- **GET** — read, **safe** (no side effects) and **idempotent**. Must never mutate.
- **POST** — create a resource, *or* trigger a **side-effecting action** (`/orders/dispatch`, `/riders/match` — they mutate state / increment counters). Not idempotent.
- **PATCH** — **partial** update of an existing resource (rider location, order status — change a few fields).
- **PUT** — **full** replace of a resource (send the whole object). Idempotent.
- **DELETE** — remove a resource. Idempotent.

**Soundbite:** "Verb follows semantics. `/match` and `/dispatch` are POST even though they don't 'create' anything — they have side effects (incrementing a counter, flipping status), and side effects can't sit behind a GET, which must stay safe and idempotent. Location and status updates are PATCH because they're partial edits, not full replacements."

**Gotcha:** putting a mutation behind a GET is the classic violation — a crawler or a retry could silently fire it. Safe/idempotent is a *contract*, not a suggestion.

### Path vs Query parameters
- **Path param** (`/orders/3`) → identity. *Which* resource. Required.
- **Query param** (`/orders?status=PENDING`) → filter/options. Usually optional.

**Soundbite:** "Path = identity, query = filter. FastAPI decides by name: if the param name appears in the route path inside `{}`, it's a path param; otherwise it's a query param."

**Gotcha:** an optional filter like `status` should be a query param, not `/orders/{status}` — putting it in the path makes it required and reads as identity.

### The error envelope
`422` responses look like: `{"detail":[{"type","loc","msg","input"}]}`.
`loc` tells you *where* it failed — `["body","value"]`, `["query","status"]`, `["path","order_id"]`.

---

## 4. Validation (FastAPI + Pydantic)

### The core principle
FastAPI validates against **the exact type you declare — no more.**
- `str` accepts *any* string → loose gate, almost nothing rejected.
- `int`, `Enum`, or a Pydantic model with constraints → tight gate.

**Soundbite:** "Validation isn't magic — it enforces the declared contract. A loose type is a loose gate. I tighten inputs by typing them specifically: `int`, an `Enum`, or `Field(gt=0)`."

### Declarative validation vs runtime checks — "type it if you can, raise it if you must"
- **Type it (declarative):** "Is the input the right *shape*?" — knowable from input alone → use a type/Enum/Pydantic. Auto `422` at the boundary.
- **Raise it (`HTTPException`):** "Input is valid, but does it make sense against the *data/state*?" — only knowable at runtime → check and raise.

**Example:** `status` ∈ {PENDING, DELIVERED} → *static known set* → **Enum** (422 on bad). `order_id=3` exists? → *dynamic, depends on DB* → **runtime check + 404**. A status *transition* being legal → *depends on current state* → **runtime check + 400**.

**Soundbite:** "Static, known-at-code-time sets become types. Data-dependent truths — does this row exist, is this transition legal — must be runtime checks that raise. Both look like `x not in collection`, but one the type system can express and the other it can't."

### Pydantic models
- **Request model** (`OrderCreate`) = input contract — what you accept.
- **Response model** (`OrderResponse`) = output contract — what you expose.
- `response_model` **filters output**: any field not declared is stripped — internal fields can't leak. (Security boundary, not just docs.)
- `Field(gt=0, description=...)` adds constraints + Swagger docs.
- Pydantic **coerces when it can** (`"250"` → `250.0`), **rejects when it can't** (`"abc"` → 422).

**Gotcha:** to return a SQLAlchemy object through a response model, the schema needs `model_config = ConfigDict(from_attributes=True)` (Pydantic v2; was `orm_mode = True` in v1).

### Two kinds of "model" — don't confuse them
| | Pydantic model | SQLAlchemy model |
|---|---|---|
| Lives in | `app/schemas/` | `app/models/` |
| Job | shape of API data (validate JSON) | shape of a DB table |
| Guards | the API door | the storage shelf |

Having both for orders is **correct**, not redundant — different layers.

### One enum, one home (learned at the state machine)
`OrderStatus` is shared by schemas, models, dispatch, *and* the state machine. Define it **once** in `app/core/enums.py` and import everywhere. Two definitions silently drift — and two enum classes compare unequal even when their values match (`schemas.OrderStatus.PENDING != core.OrderStatus.PENDING`).

**Gotcha:** a `# type: ignore` on an *import* is a smell — it's usually silencing a real `ModuleNotFoundError` (the file you're importing from doesn't exist yet). Comments that suppress errors hide the bug you need to see.

---

## 5. Databases & Persistence

### In-memory vs on-disk
A Python dict lives in the process's **RAM** → killed on restart (counter resets, data gone). PostgreSQL writes to **disk** → survives restarts, crashes, redeploys.

**Soundbite:** "In-memory state dies with the process. A database persists to disk, so it's the durable source of truth even as the app restarts or scales to multiple instances."

### Client / server model
The database is a **separate server process** (port `5432`). Your app, `psql`, and DBeaver are all **clients** talking to it. (Same for Redis on `6379` — which is why Redis state shows in `redis-cli`, never in DBeaver.)

**Soundbite:** "Postgres runs as its own server; my app is just one client over a socket. That separation is what gives persistence, concurrency, and one shared source of truth."

### Primary key / auto-increment
`id` is a `SERIAL` (auto-incrementing sequence) — the DB generates it, and the counter **persists** (next insert is 4, not 1, after a restart). Sequences never reset on DELETE; gaps are intentional so old references never silently re-point.

---

## 6. SQLAlchemy / ORM

### What an ORM is
Object-Relational Mapper = a **translator**. You write Python classes; it generates SQL.
- `engine` — the connection manager to the DB (lazy; connects when needed).
- `Session` — one conversation/transaction with the DB.
- `Base` — the registry; every model inheriting from it is tracked.

**Soundbite:** "SQLAlchemy maps a Python class to a table. I write objects, it writes the SQL. `engine` is the connection, a `session` is one transaction, `Base` is the registry of all my tables."

### create_all + THE classic trap
`Base.metadata.create_all(bind=engine)` creates all registered tables that don't exist yet.

**Gotcha:** a model only registers on `Base` when its file is **imported**. If you don't `import` the model before `create_all`, the table silently isn't created. (`from app.models.order import Order` is doing work just by running.) *(In this project Alembic owns the schema — see §9 — but the import-trap principle recurs in `env.py`.)*

### Column options
- `primary_key=True` → unique row id, DB auto-generates it.
- `index=True` → B-tree index → O(log n) lookups (vs O(n) scan).
- `nullable=False` → required at the DB level (second layer beyond Pydantic).
- `default=...` → auto-filled if not provided. **Wrap a callable in `lambda`** (`default=lambda: datetime.now(UTC)`) so it's evaluated **per insert**, not once at import.

### CRUD operations
- **Create:** `db.add(obj)` → `db.commit()` (runs the INSERT) → `db.refresh(obj)` (reloads DB-generated fields like `id`, `created_at`).
- **Read one:** `db.query(Order).filter(Order.id == x).first()` → row or `None`.
- **Read many:** `db.query(Order).all()` (optionally `.filter(...)` first).

**Gotcha:** without `db.refresh()`, `obj.id` is still `None` right after commit — which breaks anything downstream that needs the id (e.g. indexing a new rider into Redis: commit → refresh → `add_rider`).

### Dependency Injection (`Depends(get_db)`)
`db: Session = Depends(get_db)` → FastAPI runs `get_db` before the endpoint, hands in a fresh session, closes it after (the `try/finally`). Every request gets its own short-lived, auto-closed session.

**Soundbite:** "Each request gets its own DB session via dependency injection — opened before the handler, closed after, automatically. No leaked connections."

### The type-checker squiggle (SQLAlchemy + Pylance)
`new_rider.id` / `.current_lat` show red underlines because SQLAlchemy types columns as `Column[...]` at the class level while returning real values at runtime. **Harmless** — runtime works. The clean fix is SQLAlchemy 2.0's `Mapped[int]` / `mapped_column(...)` annotations (deferred to the Day 43 quality sweep).

---

## 7. Project Structure

```
app/
├── core/        # database.py, redis_client.py, enums.py (one OrderStatus), config.py
├── models/      # SQLAlchemy models (DB tables)
├── schemas/     # Pydantic models (API in/out)
├── routers/     # APIRouter modules (grouped endpoints)
├── services/    # business logic / algorithms (dispatch, geohash, order_state)
├── middleware/  # runs on every request (rate limiter)
└── main.py      # FastAPI app + include_router
```

**Separation of concerns:** routers = *what endpoints exist*; schemas = *what shape data has*; services = *how the logic works*; models = *what the DB stores*; core = glue (connections, shared enums). **`core` = infrastructure glue, `services` = business logic** — that's why `dispatch.py` belongs in `services/`, not `core/`.

**APIRouter:** `APIRouter(prefix="/orders", tags=["orders"])` groups related routes in their own file; `app.include_router(...)` plugs them in. Keeps `main.py` thin.

---

## 8. Quick-Fire Self-Test (Pre-Alembic concepts)

1. When do you return `200` / `201` / `400` / `404` / `422` / `429`?
2. 400 vs 422 — what's the difference, and which one does FastAPI raise for you?
3. Why are `/dispatch` and `/match` POST and not GET? Why is location-update PATCH not PUT?
4. Path param vs query param — how does FastAPI decide which is which?
5. Why does `status="banana"` give `422` with an Enum but `200 []` with a plain `str`?
6. "Type it if you can, raise it if you must" — explain with `status` vs `order_id` vs a status *transition*.
7. What does `response_model` do to fields you return but didn't declare?
8. Pydantic model vs SQLAlchemy model — what's the difference?
9. Why must `OrderStatus` live in one file, and what's the `# type: ignore`-on-import smell?
10. Why does in-memory data reset on restart but the DB doesn't?
11. What are `engine`, `session`, and `Base`?
12. Walk through `add` → `commit` → `refresh`. What breaks if you skip `refresh`?
13. Why wrap a `default=` callable in `lambda`?
14. What does `Depends(get_db)` give each request, and what closes the session?
15. Why do SQLAlchemy column attributes show type-checker squiggles, and are they real?

*If any answer is shaky, that's your next review target.*

---
---

## 9. Database Migrations (Alembic)

### Why migrations exist — the `create_all` flaw
`create_all` **only creates missing tables — it never alters an existing one.** Add a column to a model and `create_all` does nothing, so your code and DB drift apart and crash. Migrations are **versioned, incremental, reversible** scripts describing schema *changes* — `upgrade` to apply, `downgrade` to roll back. Think **git for your schema**. **Alembic** is the migration tool for SQLAlchemy.

**Soundbite:** "Production never uses `create_all` — it can't alter existing tables. I use Alembic migrations: versioned, reversible schema changes that keep every environment in sync."

### The workflow
1. Configure `alembic/env.py`: import `Base` **and every model**, set `target_metadata = Base.metadata`.
2. `alembic revision --autogenerate -m "..."` — diffs models vs DB, drafts a migration.
3. **Review** the generated `upgrade()` / `downgrade()`.
4. `alembic upgrade head` — applies it; creates the `alembic_version` table that records the current revision.

### Gotchas
- **The import trap:** `env.py` must import the **model classes**, not just `Base`. A model only lands in `Base.metadata` when imported. Miss it → autogenerate thinks the models have *no* tables → it generates `DROP` statements for your real tables.
- **Autogenerate is a draft, not gospel.** Always review before applying — it can miss renames and some type changes. ("How do you handle migrations?" → "Autogenerate, then review before running.")
- **`alembic_version`** holds one row — the current revision id. That's how Alembic knows where the DB stands.
- **`default=` ≠ `nullable=False`.** A model `default=` fills the value via the ORM at insert time, but the column still allows `NULL` at the DB level. For a DB-*enforced* constraint, add `nullable=False`.


# DeliverIQ — Interview Prep, Part 2 (Days 15–17)

> Companion to the main guide. Covers Redis, the token-bucket rate limiter, and
> priority-queue dispatch — the Phase 3 work. Same format: **concept (why)**,
> **soundbite (how to say it)**, **gotcha (what trips people up)**.

---

## 10. Redis — In-Memory Store

### What it is (in CP terms)
PostgreSQL is a durable `std::map` backed by a file on disk. Redis is a `std::unordered_map` living in RAM — O(1) lookups in microseconds, no durability by default. You reach for it when you read/write data thousands of times per second and don't mind losing it on restart: counters, hot caches, queues, ephemeral rider state.

**Soundbite:** "Redis is in-memory, so it's microsecond-fast but lossy on restart unless persisted. I use it for hot ephemeral state — rate-limit counters, rider locations, `orders_today` — not as a source of truth. Postgres stays the durable record; Redis is the fast layer over it."

**Gotcha:** Redis is a *separate server* (port 6379), just like Postgres. Your app is one client; `redis-cli` is another. It's not in-process memory — that's the whole point, it's *shared* across app instances.

### The commands that matter
- `SET` / `GET` — store and read a key. O(1).
- `INCR` — atomic read-add-write in one step. **The heartbeat of a rate limiter** — 1000 concurrent requests can't corrupt the count because the operation is indivisible.
- `EXPIRE key N` / `TTL key` — set a self-destruct timer; the key deletes itself after N seconds with zero cleanup code. `TTL` returns the live countdown (`-2` = gone, `-1` = exists but no expiry).
- `HSET` / `HGETALL` / `HGET` — a **hash**: one key holding multiple field→value pairs (a tiny dict). Needed when one logical record has several fields (e.g. a rate-limit bucket's `tokens` + `last_refill`).

**Soundbite:** "INCR is atomic, which is why it's race-safe for counters. EXPIRE gives keys a TTL so they garbage-collect themselves. Hashes let me store a small multi-field record under one key."

**Gotcha:** with `decode_responses=True`, Redis returns Python `str`, not bytes (`b'3'`). But everything still comes back as a **string** — `hgetall` gives `{"tokens": "100"}`, so you must cast: `float(data["tokens"])`.

### Python client pattern
One shared client, created once in `app/core/redis_client.py`, imported everywhere — same discipline as the SQLAlchemy `engine`. You don't make a new connection per request.

---

## 11. Token-Bucket Rate Limiter ⭐

### The model
A bucket holds up to N tokens (100). Each request spends 1. The bucket **refills continuously** based on elapsed time: `tokens = min(CAP, tokens + elapsed_seconds × refill_rate)`. Empty bucket → HTTP `429 Too Many Requests`. State (current tokens + last-refill timestamp) lives in a Redis hash between requests.

**Soundbite:** "I built a token-bucket limiter backed by a Redis hash. Each client gets 100 tokens refilling at 100/min. A request costs a token; empty bucket returns 429. Recovery is computed from elapsed time on each request — lazy refill — so I don't need a background job topping up buckets."

### Why token-bucket over fixed-window
- **Allows controlled bursts.** An idle client accumulates up to bucket-size tokens, can burst that many, then is throttled to the refill rate. Matches real traffic better than a hard count.
- **No boundary-burst flaw.** A fixed-window limiter resets its whole count at the window edge, so a client can fire 2× the limit straddling the reset (5 at 0:59, 5 at 1:00 = 10 in 2 seconds). Token-bucket refills smoothly — that instant of a fresh full budget never exists.

**Soundbite:** "Token-bucket over fixed-window for two reasons: it permits bursts up to bucket size, and it avoids fixed-window's boundary-burst flaw where a client doubles the rate across the reset edge. The price is slightly more state — I track tokens plus a timestamp instead of a single counter."

### Middleware vs dependency — why this is middleware
- A **dependency** runs *before* the handler and hands a value in. It sits on the **entry path only** — it never sees the response.
- **Middleware wraps** the handler via `call_next`: code before `call_next` gates the request; `call_next` runs the route and returns the response object; code after can mutate that response.

The limiter needs **both** sides — reject over-limit requests (before) *and* attach an `X-RateLimit-Remaining` header (after). Only middleware sits on both paths. That's the deciding reason.

**Soundbite:** "It's middleware, not a dependency, because it both gates the request and decorates the response. `call_next` hands me the response object on the way out, so I can add the remaining-tokens header — a dependency never sees the response."

**Gotcha (the one I hit):** `--reload` silently does nothing if an old server still holds the port — you get `[Errno 98] Address already in use` and keep testing stale code. Always confirm `Application startup complete`. `fuser -k 8000/tcp` kills the stale process.

### What `expire(key, 120)` actually does — the subtle one
It's **memory housekeeping, not recovery.** If a client makes a request then vanishes forever, its bucket hash would otherwise sit in Redis RAM permanently — a slow leak across millions of one-time clients. The TTL garbage-collects abandoned buckets. **Recovery for active clients comes entirely from the elapsed-time refill math, not the TTL.**

**Gotcha to nail in interviews:** "If you deleted the expire line, does rate-limiting still recover?" → **Yes.** After 3 minutes idle, `elapsed × refill_rate` refills the bucket to full regardless of TTL. Deleting `expire` only causes a memory leak, not a broken limiter. (This *would* break a fixed-window limiter, where the TTL *is* the window reset — different algorithm, different role for the TTL. Knowing this distinction is the senior signal.)

### Cost & hardening
- ~3 Redis ops per request (HGETALL, HSET, EXPIRE) → sub-millisecond locally.
- **Read-then-write race:** between reading tokens and writing the new count, a concurrent request could interleave. At scale, collapse the whole check into **one atomic Lua script or pipeline** so it's a single round-trip with no race.
- **Keying:** uses `X-API-Key or client.host`, with a None-guard (`request.client` can be `None` in tests). `X-Forwarded-For` is **deferred to deployment** — behind a proxy the real IP is in that header, but it's client-spoofable, so it's only trustworthy after verifying the request came from your trusted proxy. Trusting it blindly lets anyone bypass the limiter by forging a new IP per request.

**Soundbite:** "Three Redis ops, sub-millisecond. The read-write isn't atomic, so at scale I'd move it to a single Lua call. I key on API-key-or-IP; proper X-Forwarded-For handling waits for deployment because the header is spoofable without a trusted proxy in front."

---

## 12. Priority-Queue Dispatch

### The problem
Orders pile up as PENDING. Handling them FIFO is wrong — a ₹2000 order shouldn't wait behind a just-arrived ₹150 one. You need to always pull the **highest-priority** pending order next. That's a heap.

### The heapq mechanics (the C++ bridge)
`std::priority_queue` is a max-heap (`top()` = largest). Python's `heapq` is a **min-heap with no max flag** — so push the **negated** key. Push tuples `(-value, id)`; tuples compare element-by-element like `pair`. `heappop` returns the most-negative = highest real priority. `heapq` operates on a plain list — it's not a class you instantiate.

**Soundbite:** "Dispatch picks the highest-priority PENDING order with a max-heap. Python's heapq is a min-heap, so I push negated priorities — `(-value, id)` tuples. heappush/heappop are O(log n). I assign by flipping status PENDING→ASSIGNED and committing, so the order leaves the pool."

### What "priority" is — a design decision, not a given
In a contest priority is handed to you; here you define it. For delivery, two factors compete: **order value** (revenue) and **wait time** (don't starve cheap orders). Value-only priority can starve a ₹150 order forever behind expensive ones. The fix is **aging** — blend in wait time: `priority = value + wait_minutes × WEIGHT`. The longer an order waits, the higher it climbs until it beats fresh high-value orders.

**Soundbite:** "Priority is value plus a wait-time aging term. Without aging, a cheap order starves behind a stream of expensive ones — the classic scheduling-starvation problem. Aging is the OS technique for exactly this. Naming starvation and aging is the point here."

**Gotcha:** the assign step needs `db.commit()` to persist the status flip — otherwise the change lives only in the session and the order re-appears as PENDING on the next dispatch.

### Honest complexity note (volunteer this — it's a strength)
The current version rebuilds the heap from the DB on every call and pops one element — O(n) to build, O(log n) to pop, so for a *single* pick a plain `max()` does equal work. The heap earns its keep when you pop many in sequence or keep it warm across calls. Stating this openly signals you actually analyzed it rather than cargo-culting a heap.

### The distributed scale-up (scheduled for Phase 4, not optional)
A per-process heap is **single-instance**. The moment you run multiple API replicas, two instances could pick the same order — a race. The fix: move the queue into a **Redis sorted set** — `ZADD orders:pending {id: priority}` on create, `ZREVRANGE` to peek the max, `ZREM` to claim. `ZREM` returning `1`-or-`0` is an **atomic concurrent-claim guard**: only one instance gets the `1`, so the order can't be double-dispatched. This is what earns the word "distributed" — build it in Phase 4 when multiple instances actually exist.

**Soundbite:** "Single-process today with an in-process heap. I know exactly when it breaks — at multiple API instances the heap is per-process, so two instances could claim the same order. That's when I move the queue to a Redis sorted set, where ZREM gives an atomic claim guard. I'd rather show I know the single-node/distributed boundary than reach for distributed infra before I need it."

**Gotcha:** the sorted-set version *hides* the heap behind Redis — Redis does the ordering internally. The in-process heapq is the version that actually demonstrates the DSA, which is why it's the primary implementation and the sorted set is the scale story.

---

## 13. Self-Test — Days 15–17 (answer out loud)

1. Why is Redis fast but lossy, and what do you keep in it vs Postgres?
2. Why is `INCR` race-safe where a read-then-write isn't?
3. What does `EXPIRE`/TTL give you, and what does `TTL` return for a missing key?
4. Why store the rate-limit bucket as a hash instead of two separate keys?
5. Token-bucket vs fixed-window — name the two advantages.
6. Why is the limiter middleware and not a dependency?
7. What does `expire(key,120)` actually protect against — and does deleting it break recovery?
8. Why does deleting `expire` break a *fixed-window* limiter but not a token bucket?
9. How many Redis ops per request, and how would you remove the read-write race?
10. Why is `X-Forwarded-For` deferred to deployment?
11. Why negate the key in heapq, and what do tuples compare on?
12. What is order starvation, and how does aging fix it?
13. What breaks in the heap dispatcher at multiple API instances, and what's the fix?
14. Why does the Redis sorted-set version *hide* your DSA — and why build the heap first anyway?

*Shaky on any? That's your next review target.*


# DeliverIQ — Interview Prep, Part 3 (Day 18)

> Companion to the main guide. Covers geohash rider matching and fairness-banded
> dispatch — the differentiator. Same format: **concept (why)**, **soundbite (how
> to say it)**, **gotcha (what trips people up)**.

---

## 14. Geohash Rider Matching

### The two-stage filter (keep them distinct)
Matching is **two independent filters in order**, not one step:
1. **Geohash — coarse "who's even considered."** Encode (lat, lon) into a base-32 string where nearby points share a prefix. Lookup is the home cell + its 8 neighbours — a cheap set union, not a distance calc against every rider. At precision 6 the reach is ~3.6 km total (a 3×3 grid of ~1.2 km cells).
2. **Haversine — precise "exact distance" inside that set.** Geohash cells are approximate; haversine gives the real great-circle distance to rank the survivors. Euclidean (`√(Δlat²+Δlon²)`) is wrong on a sphere — 1° of longitude shrinks toward the poles — so haversine is the correct GPS-distance formula.

**Soundbite:** "Rider matching is two filters: geohash for a coarse O(1)-ish candidate set — nearby points share a string prefix, so I check the home cell plus 8 neighbours instead of scanning every rider — then haversine for exact great-circle distance to rank that small set. Cheap filter, then precise sort on the survivors."

**Gotcha — the boundary bug (gold interview material):** an order at a cell *edge* can have its nearest rider just across the line, in a neighbouring cell with a totally different geohash string. Checking only the home cell misses them. The fix is the 8 neighbours. I hit this live — dropping neighbours made a rider 10 m away invisible.

**Gotcha — geohash range ≠ band.** `band_m` only filters riders geohash already *found*. A rider 13 km away is outside the neighbour ring, so no band size — even 50 km — can pull them in; they were never a candidate. Two filters, in sequence: geohash decides who's considered, band decides who's feasible among those.

### Why a set AND a hash per rider
- `geohash:<cell>` → **set** of rider IDs ("who's in this cell" — membership, dedupe).
- `rider:<id>:loc` → **hash** of {lat, lon, cell} ("this rider's exact attributes").

**Rule:** set = a bag of interchangeable peers; hash = one record with named fields. Same rider lives in both, playing different roles — a *member* of the cell roster, and an *owner* of a location record.

**Gotcha:** Redis returns everything as strings. `float(loc["lat"])` before distance math, `int(...)` for counters — forget the cast and the math chokes.

---

## 15. Fairness-Banded Dispatch ⭐ (The Differentiator)

### The rule
Among riders within a distance band Δ of the **nearest** candidate, assign the one with the **fewest orders today**. Tiebreak on distance.

```
d_min = nearest candidate's distance
feasible = riders within d_min + Δ
winner = min(feasible) on key (orders_today, distance)
```

### Why a hard band, not a blended score
A blended score `α·dist + β·load` can **silently send a far rider** when the load term dominates — cold food, broken SLA, and you can't tell from the formula when it'll happen. The hard band makes the SLA guarantee **explicit and tunable**: fairness operates *only inside* Δ, so a rider outside the band is never eligible no matter how idle. Δ is the single knob between competing goals — wide band = more fairness (spread earnings), narrow band = tighter SLA.

**Soundbite:** "Greedy-nearest optimizes pure distance. I add a bounded fairness constraint — among riders within a band Δ of the nearest, assign the least-loaded. It's a constrained-assignment problem: minimize rider load subject to a distance bound. A blended score could silently send a far rider when load dominates; the hard band makes the SLA guarantee non-negotiable and tunable. That's my honest answer to both 'how is this different from Swiggy' and 'what's the social impact' — fairer earnings for gig riders without delivering cold food."

### The behaviour (what you actually see)
Two phases: the system **drains the load imbalance first**, then **reverts to nearest-rider**. Idle riders absorb orders until they catch up to the busy rider's count; once all loads tie, the distance tiebreak takes over and the nearest wins. A naive nearest-only dispatcher would hammer the closest rider every call and never balance anyone.

**Heap framing:** the selection is a min-heap on the composite key `(orders_today, distance)` over the small feasible band — greedy on a composite key, O(k log k) on candidate set k, not O(n) over all riders. Same `pair`-comparison idea as a C++ tuple sort.

### Daily counter reset — no cron
`orders_today` is stored as a **date-stamped key**: `rider:<id>:orders:<YYYY-MM-DD>`. Tomorrow is a *different key* that starts at 0 automatically — the key name **is** the reset, no midnight job, no reset race. A 48 h TTL (`expire`) garbage-collects past days. The TTL **slides** — every order refreshes it to 48 h from the last write — so an active rider's key never dies mid-day, an idle rider's key expires 48 h after they stop.

**Soundbite:** "Daily counter resets via a date-stamped key with a sliding TTL — the key rotates itself at midnight because the date is in the name, and a 48-hour expiry cleans old days. No cron, no midnight reset race."

**Gotcha:** the count and the TTL are independent on the same key. `incr` accumulates the day's total; `expire` only refreshes the death-clock. The value persists and climbs within a day; the daily "reset" comes from the date in the key, not from `expire`. Lazy creation too — `incr`/`hincrby` on a missing key starts at 0 and creates it, so no explicit init; the read side guards with `or 0`.

### The endpoint
`POST /riders/match` — **POST not GET**, because matching has a side effect (it increments the winner's order count). GETs must be safe/idempotent; a mutation behind a GET violates HTTP semantics. Same reasoning as `POST /orders/dispatch`.

---

## 16. Self-Test — Day 18 (answer out loud)

1. Why two filters (geohash + haversine) instead of one? What does each do?
2. Why check the 8 neighbour cells, not just the home cell?
3. Why can't a huge `band_m` rescue a rider 13 km away?
4. Why is a rider stored in both a set and a hash — which question does each answer?
5. Why haversine over Euclidean distance?
6. Explain the band as a constrained-assignment problem in one sentence.
7. Band vs blended score (α·dist + β·load) — why the hard band?
8. Describe the two-phase behaviour (drain imbalance, then revert to nearest).
9. How does `orders_today` reset daily with no cron job?
10. Why does each order refresh the TTL, and what does that achieve?
11. Why is `/riders/match` a POST and not a GET?

*Shaky on any? That's your next review target.*


# DeliverIQ — Interview Prep, Part 4 (Rider Sync)

> Companion to the main guide. Covers the Postgres↔Redis dual-write consistency work
> layered onto Day 18. Same format: **concept (why)**, **soundbite (how to say it)**,
> **gotcha (what trips people up)**.

---

## 17. Dual-Write Consistency (Postgres ↔ Redis)

### The setup
Riders live in **two stores at once**: PostgreSQL is the durable source of truth, Redis is a hot geohash index for fast matching. Every rider write (create, move) has to update **both** in one request — a **dual write**. Miss one and the index goes stale: `select_rider` reads Redis, so a rider absent from Redis is invisible to matching, and a rider with a stale Redis cell gets matched at a location they already left.

**Soundbite:** "Riders are in two stores — Postgres as the source of truth, Redis as a hot geohash index. Each rider write updates both in one request. I keep Postgres authoritative precisely because Redis is the disposable, rebuildable layer — if they ever drift, Redis can be reconstructed from Postgres."

### The move-path trap (the real bug)
Indexing a rider does `sadd` to their cell's set. On a **move**, you must `srem` them from the *old* cell **before** `sadd`-ing the new one — otherwise they stay a phantom member of every cell they've ever been in, and match at stale locations. The old cell is recoverable because it's stored on the `rider:{id}:loc` hash.

**Soundbite:** "The subtle bug is the move path — you have to remove the rider from their old geohash cell before adding the new one, or they become a phantom member of stale cells and get matched somewhere they've left. I read the old cell off the location hash, srem it, then sadd the new one."

**Gotcha:** order matters — `srem` old, then `sadd` new. And guard `if old_cell and old_cell != new_cell` so a no-op move (same cell) doesn't needlessly churn the set.

### What if the second write fails?
The two writes aren't in one transaction (different systems). If the Postgres commit lands but the Redis write throws, they drift. Recovery is **reconciliation**: Redis is fully reconstructable from Postgres, so a periodic job re-indexes all riders from the DB. You never lose truth — only the cache goes briefly stale, and it's self-healing.

**Soundbite:** "It's a dual write across two systems, so no single transaction spans both. If the Redis write fails after the Postgres commit they drift — but Redis is rebuildable from Postgres, so a reconciliation job re-indexing riders is the recovery path. Truth is never at risk; only the cache."

### Orders don't have this problem — know the contrast
Orders live in **Postgres only**. The dispatch heap is rebuilt from Postgres each call, not stored in Redis, so there's no order-side index to keep in sync. Being able to say *why* riders need dual-write and orders don't shows you understand the pattern, not just the mechanics.

**Soundbite:** "Orders are Postgres-only — the dispatch heap is rebuilt from the DB each call, nothing cached in Redis — so there's no dual write to maintain. Riders need it because their location is indexed in Redis for fast geohash lookup. The dual-write cost only appears when you cache derived state."

### The UTC reset nuance (daily counter)
`orders_today` keys are stamped in **UTC** (`datetime.now(UTC)`), so the daily reset boundary is UTC midnight, not local. On IST (UTC+5:30) the key reads the *previous* calendar day for the first ~5.5h after local midnight. UTC is the right default — consistent across servers and DST-free — but in production you'd reset on the **business timezone** so "today" matches the rider's actual day.

**Soundbite:** "The daily counter resets on UTC midnight because the key is stamped with `datetime.now(UTC)` — consistent across instances, no DST edge cases. In production I'd switch the reset to the business timezone so it matches the rider's local day, but UTC is the correct default for correctness."

**Gotcha:** when inspecting, the key is `rider:{id}:orders:{UTC-date}` — on IST after midnight that's *yesterday's* date. And it's a **Redis** key: visible via `redis-cli`, never in DBeaver (DBeaver is Postgres only). "Why isn't X in DBeaver?" is almost always "because X is Redis state."

---

## 18. Self-Test — Rider Sync (answer out loud)

1. Why do riders need a dual write but orders don't?
2. What's the phantom-membership bug, and what's the fix (in what order)?
3. Postgres commit succeeds, Redis write fails — what's the state, and how do you recover?
4. Why is Postgres the truth and Redis the rebuildable layer, not the reverse?
5. Why does `create_rider` need `refresh` before `add_rider`?
6. Why PATCH (not PUT/POST) for the location update?
7. Why is the daily counter stamped in UTC, and what's the IST consequence?
8. Why does `orders_today` never show up in DBeaver?

*Shaky on any? That's your next review target.*

# DeliverIQ — Interview Prep, Part 5 (Day 19)

> Companion to the main guide. Covers the order state machine — enforcing a legal
> lifecycle and the error-semantics that come with it. Same format: **concept (why)**,
> **soundbite (how to say it)**, **gotcha (what trips people up)**.

---

## 19. Order State Machine

### What it is
Order status isn't a free string — it's a **directed graph** of legal transitions. Each status is a node; each allowed transition is an edge. The table is an adjacency list (`map<State, set<State>>` in C++ terms); "is this legal?" is an O(1) set-membership check. Terminal states (DELIVERED, CANCELLED) have empty neighbour sets — nothing is reachable from them.

```
PENDING ──→ ASSIGNED ──→ PICKED_UP ──→ DELIVERED
   │            │
   └──→ CANCELLED ←┘
```

**Soundbite:** "Order status is a state machine — a directed graph of legal transitions, not a settable string. The transition table is an adjacency list; validating a transition is an O(1) lookup in the current state's neighbour set. Terminal states have no outgoing edges, so a delivered order can't be un-delivered."

**Gotcha:** the validator only *validates* — it raises or stays silent, it doesn't mutate or touch the DB. The caller persists. Keeping legality-check separate from persistence means the same `transition()` is reusable from any call site (the status endpoint, dispatch, a future rider app) with each deciding how to handle a failure.

### Why strict — no ASSIGNED → PENDING (a design decision, not a default)
A rider who accepts then abandons an order does **not** bounce it back to PENDING. Re-dispatching means the customer waits through a *second* matching cycle — cold food, broken SLA. Instead: cancel + penalize the rider. The penalty lives on the **rider**, not as an order-state edge.

**Soundbite:** "I kept the machine strict — no ASSIGNED→PENDING. When a rider abandons an accepted order I cancel rather than re-pool, because re-dispatching breaks the customer's delivery-time guarantee. The rider penalty is tracked separately on the rider, not as an order transition — the order machine governs the order's lifecycle, penalties are a rider concern. Mixing two independent state spaces is a coupling mistake."

**The senior line:** *order-state and rider-penalty are independent state spaces; don't couple them.*

### The two-failure-semantics distinction ⭐ (best interview point here)
The *same* `transition()` call has *different* failure meaning at different call sites:

- **The status endpoint** — the target status comes from the **user**. An illegal transition is *expected bad input*. Catch `InvalidTransition` → return **400**.
- **Dispatch** — the transition (PENDING→ASSIGNED) is derived from your own `status == "PENDING"` filter. A failure means a **server-side bug** (a non-PENDING order got pulled). **Don't catch it** — let it raise into a **500**.

**Soundbite:** "Same `transition()` call, two different failure semantics. In the user-facing endpoint an illegal transition is expected bad input — catch it, return 400. In dispatch the transition is derived from my own query invariant, so a failure is a server bug, not user error — I let it raise into a 500 rather than mislabel my bug as the client's bad request. Error-handling follows *who caused the error*, not the function being called."

**Gotcha:** wrapping the dispatch call in `try/except → HTTPException(400)` would be *wrong* — it blames the client (400 = "you did something wrong") for what is actually a server logic error. A 500 is the honest signal: "the server hit a state it believed impossible." The dispatch `transition()` is really an **assertion** (`assert order_is_pending`) — and asserts aren't meant to be caught.

### Single gate for status changes
Before the refactor, status was mutated in two places with two rule sets: the endpoint (validated) and dispatch (raw string, unvalidated). Routing dispatch through `transition()` too means **every** status change goes through one gate. The dispatch call is provably always-legal given the PENDING filter — so it's a no-op today — but the value is the *invariant*: "there is exactly one place order status changes legally" is a property worth being able to state. Without it, "how do you guarantee valid transitions?" gets a caveat: "well, except in dispatch."

**Soundbite:** "Every status change routes through the state machine — no exceptions. The dispatch call is always-legal given the filter, so it never fires, but I added it so I can say there's a single gate for status changes. The comment marks it deliberate, not dead code — I know it's redundant today and chose the invariant anyway."

**The honest counterpoint (have it ready):** "You could argue it's dead code — a check that provably can't fail is noise, and dead defensive code implies a check that isn't really happening. Both positions are defensible; I lean toward the single-gate invariant because the cost is one commented line and the story it buys is worth more than the line costs in clarity."

### Legal-transition vs permitted-actor — orthogonal guards
The state machine answers "is this transition legal *at all*?" It does **not** answer "is *this caller* allowed to make it?" A customer marking their own order DELIVERED is a *legal edge* but the *wrong actor*. Those are two independent protections — and authorization needs authenticated identities, so it's deferred to **Day 35 (JWT)**: role + ownership (assigned rider advances their own orders, ops cancels, customer can't touch status).

**Soundbite:** "The state machine enforces which transitions are legal, not who may make them — orthogonal guards. A customer shouldn't mark their own order delivered even though it's a legal edge. After JWT, the status endpoint checks role and ownership on top of the legality check. Until then it's an unauthenticated admin tool, which I'm tracking deliberately, not by accident."

---

## 20. Self-Test — Day 19 (answer out loud)

1. Why is order status a state machine and not just a string column?
2. What's the adjacency-list / set-membership framing, and what's O(1) about it?
3. Why does `transition()` only validate and not persist?
4. Why keep ASSIGNED→PENDING illegal — what's the product reasoning?
5. Why is the rider penalty *not* an order-state edge?
6. Same `transition()` call — why does the endpoint catch it but dispatch doesn't?
7. Why would `try/except → 400` be *wrong* in dispatch?
8. The dispatch `transition()` never fires — so why add it? And the counterargument?
9. Legal-transition vs permitted-actor — what's the difference, and which is deferred to Day 35?
10. Why is 400 (not 422) the right code for an illegal-but-well-formed transition?

*Shaky on any? That's your next review target.*
---
# DeliverIQ — Interview Prep, Part 6 (Day 20)

> Rider lifecycle (BUSY↔AVAILABLE), dual-store availability enforcement, and
> the Pub/Sub fire-and-forget flaw that motivates Kafka.

---

## 21. Rider Lifecycle + Pub/Sub

### Availability enforced in Redis, recorded in Postgres
A rider's availability lives in **both** stores, each doing a different job:
`rider.status` in Postgres is the durable truth ("why" — this rider is
delivering); the rider's *presence in a geohash cell* in Redis is the
enforcement ("now" — `select_rider` can only pick riders in cells). Assigning
sets `status="BUSY"` AND `srem`s them from their cell; freeing sets
`status="AVAILABLE"` AND re-adds them.

**Soundbite:** "Availability is dual-store. Postgres `status` is the record;
Redis cell-membership is the enforcement. I don't filter BUSY riders inside
`select_rider` — I remove them from the index entirely, so a busy rider is
*structurally* unselectable. `select_rider` needed zero changes."

**Gotcha — the asymmetry:** going BUSY only needs `srem` (drop from index).
Going AVAILABLE needs full `update_rider_location` (`srem` old + `sadd` new +
update hash) because the rider may have *moved* — a delivered rider is now at
the drop, not the pickup. Removal needs no location; re-adding does.

### orders_today counts at assignment, not delivery
`orders_today` answers "who's earned the least today?" — fairness for
*spreading work*. It increments when a rider is **assigned** (in `select_rider`),
not when they deliver. A rider assigned 5 orders has had 5 earning
opportunities regardless of delivery progress; counting at delivery would let a
mid-delivery rider keep looking idle and get piled on.

**The orthogonality:** BUSY vs orders_today are independent axes.
BUSY = "can take work *now*?" (exclusion). orders_today = "earned least
*today*?" (fairness ranking). Same shape as legal-transition vs permitted-actor
(Day 19) — two guards that look related but answer different questions.

**Soundbite:** "BUSY and orders_today are orthogonal — one is current
availability, the other is daily fairness. BUSY already stops pile-on by
removing the rider from the pool, so the counter doesn't need to; it just tracks
the day's share, incremented at assignment because that's when the earning
opportunity was handed out."

### Commit before publish — no phantom events
The event announces a *durable fact*. Publishing before `db.commit()` risks a
listener reacting to an assignment that then rolls back. Order is always:
mutate → commit (truth) → publish (announce).

**Soundbite:** "I publish after commit, never before — an event should only
describe state that's already persisted, or a consumer acts on a phantom."

### Order→rider coupling = the motivation for events
The status endpoint now does *rider* side-effects (free + re-index on
DELIVERED/CANCELLED). That's legitimate coupling — the rider's freedom depends
on the order finishing — but it's also exactly what an event-driven design
*decouples*. Building it coupled first, then feeling the coupling, is why the
Pub/Sub subscriber exists: it shows where the side-effect *wants* to move.

### Pub/Sub fire-and-forget — the flaw that motivates Kafka ⭐
Redis Pub/Sub delivers a message only to subscribers **alive at publish time**.
No queue, no persistence, no replay. Stop the worker, dispatch, restart — the
event is gone with no record it existed.

**Soundbite:** "Redis Pub/Sub is fire-and-forget — if no subscriber is alive
when you publish, the message is lost, no replay. I used it first deliberately
so I'd feel that limitation firsthand, then moved order events to Kafka, which
persists to disk and lets a recovered consumer replay from its last offset."

**Gotcha:** the first frame from `SUBSCRIBE` is a `type="subscribe"`
confirmation whose `data` is the subscription *count*, not a payload. Guard with
`if msg["type"] != "message": continue` or the first `json.loads` parses an
integer and crashes.

---

## 22. Self-Test — Day 20 (answer out loud)

1. Why enforce availability by removing from the geohash cell instead of
   filtering inside `select_rider`?
2. What's the srem-vs-update_rider_location asymmetry between going BUSY and
   going AVAILABLE?
3. Why does `orders_today` increment at assignment, not delivery?
4. BUSY vs orders_today — what does each answer, and why are they orthogonal?
5. Why publish the event after commit, never before?
6. Why capture the reindex tuple before `db.commit()`?
7. What does Pub/Sub lose, and what exactly does Kafka add that fixes it?
8. What's the `type="subscribe"` frame, and why must you skip it?

*Shaky on any? That's your next review target.*
---
# DeliverIQ — Interview Prep, Part 7 (Day 21)

> Integration testing with proper isolation — a throwaway test DB, a swapped
> Redis logical DB, and per-test reset. Same format: **concept (why)**,
> **soundbite (how to say it)**, **gotcha (what trips people up)**.

---

## 23. Integration Testing & Isolation

### Unit vs integration — what these tests are
These are **integration** tests, not unit tests. Each one drives a real HTTP
request through the full stack — endpoint → service → Redis → Postgres — and
asserts on the response. A unit test would isolate one function with everything
mocked; these deliberately exercise the wiring *between* layers, because the
bugs in this project live in the seams (BUSY rider removed from the Redis index,
rider relocated on delivery), not inside any single function.

**Soundbite:** "They're integration tests — each hits a real endpoint against a
real (test) DB and Redis, so they cover the wiring between layers. The valuable
ones assert end-to-end behaviour: dispatch a busy rider's second order and get a
404, proving the Redis index mirror works through the whole HTTP path, not just
in isolation."

### Isolation — the core discipline
Tests that depend on dev-DB state aren't tests — they pass or fail based on
leftover rows. Isolation has three parts:
1. **A throwaway test database** (`deliveriq_test_db`), separate from dev.
2. **A swapped Redis logical DB** — Redis has 16 (0–15); tests use 15, dev uses 0.
3. **An autouse reset fixture** — drop+recreate all tables and `flushdb()`
   *before every test*, so each starts from an empty, identical world.

The result: tests are **repeatable** (same result every run) and
**order-independent** (no test leaks state into the next). The `id == 1`
assertion in the create test only holds because the reset wiped prior rows —
it's a free proof the isolation works.

**Soundbite:** "Each test runs against a throwaway test DB and a separate Redis
logical DB, and an autouse fixture resets both before every test. That makes
them repeatable and order-independent — a test that depends on dev-DB state
isn't really a test."

### Two override mechanisms — the senior detail ⭐
Postgres and Redis are swapped *differently*, and knowing why is the signal:
- **Postgres** is injected via `Depends(get_db)`. FastAPI exposes
  `app.dependency_overrides[get_db] = ...`, so I point the dependency at a
  session bound to the test engine. Same endpoint code, different DB.
- **Redis** is a bare module global (`redis_client`), imported directly with no
  `Depends`. There's no dependency to override — so the clean seam is an env var
  (`REDIS_DB`) read at **import time**, set in conftest *before* the app imports.

**Soundbite:** "The two stores need different override seams. Postgres goes
through `Depends(get_db)`, so I use FastAPI's `dependency_overrides`. Redis is a
module global with no dependency injection, so the seam is an env var read at
import — which is why conftest sets `REDIS_DB=15` before importing the app.
Recognizing that a global needs a different override strategy than an injected
dependency is the part most people miss."

**Gotcha:** the env var MUST be set before the first `import` that pulls in
`redis_client`, because the client is constructed once at import time. Set it
after, and the client is already bound to db 0 — your tests silently hit dev
Redis.

### TestClient — in-process, no server
`TestClient(app)` wraps the ASGI app and lets you call it like an HTTP server
with no uvicorn and no network. Requests run in-process, synchronously — fast
and deterministic. It's still the *real* routing, validation, and middleware,
just without a socket.

### The autouse fixture + yield
`@pytest.fixture(autouse=True)` runs without a test asking for it — perfect for
universal setup like the reset. The `yield` splits setup (before) from teardown
(after); code before `yield` runs pre-test, code after runs post-test. Here all
the work is pre-test (drop/create/flush), so the next test's setup is also the
previous test's cleanup.

### Coverage is a map, not a grade
86% isn't a target hit — it's a readout. The useful part is the **"Missing"
column**: it names the lines/branches no test reached (e.g. the CANCELLED
free-path, rate-limiter middleware, Kafka stubs). That tells you *what you
forgot to test*, not whether the code is good. Chasing 100% means testing
defensive branches that aren't worth it yet; ≥60% with the critical paths
covered is the real bar.

**Soundbite:** "I read coverage as a map of what's untested, not a grade. 86%
with the full dispatch lifecycle covered matters more than a higher number that
just exercises error branches. The 'Missing' column is the actionable part."

---

## 24. Self-Test — Day 21 (answer out loud)

1. Unit vs integration test — which are these, and why suit this project?
2. What three things make the tests isolated?
3. Why does `id == 1` reliably hold in the create test?
4. Postgres and Redis are overridden by different mechanisms — what and why?
5. Why must `REDIS_DB=15` be set before the app is imported?
6. What does `TestClient` give you that hitting the running server doesn't?
7. What does `autouse=True` do, and what splits setup from teardown?
8. Why is the busy-rider-404 test the most valuable one?
9. How do you read a coverage report — what's the actionable part?

*Shaky on any? That's your next review target.*
