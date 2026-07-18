# DeliverIQ — Interview Prep & Concept Guide

> **Companion:** this file is the *project-specific*, day-by-day guide. For the
> full zero-to-master backend curriculum (foundations → SQL/concurrency →
> distributed systems → system-design frameworks, with diagrams), see
> [Backend_Interview_Zero_to_Master.md](Backend_Interview_Zero_to_Master.md) —
> it cross-references sections here as `IP §n`.

> A self-study reference for everything built so far. Each topic has: **the
> concept (why)**,
> the **interview soundbite** (how to say it out loud), and the **gotcha** (what
> trips people up).
> If you can explain every soundbite without looking, you own the material.
>
> **Layout:** §1–2 frame the project (pitch + stack) — what an interviewer opens
> with.
> §3–8 are the backend concepts. §9 onward (Alembic, then Parts 2–5) go
> day-by-day in depth.

---

## 1. DeliverIQ — Project Talking Points

### The one-line pitch
> "A production-grade REST API that dispatches food-delivery orders to riders
> using priority queues, geohashing, rate limiting, and event streaming —
> FastAPI, Redis, Kafka, PostgreSQL, Docker."

### The differentiator: fairness-banded dispatch
Instead of naive nearest-rider, among riders within a distance band Δ of the
nearest, assign the one with the **fewest orders today**.

- **"How is it different from Swiggy/Zomato?"** → "Theirs optimizes pure ETA.
  Mine adds a bounded fairness constraint — greedy-nearest reframed as a
  constrained assignment problem."
- **"What problem does it solve?"** → "Naive nearest-rider starves some riders
  and overloads others. Banding spreads earnings while Δ guarantees delivery SLA
  isn't sacrificed."
- **"Social impact?"** → "Fairer earnings for gig riders — an honest angle, no
  fabrication."
- **"Why a band, not a weighted score?"** → "A blended `α·dist + β·fairness` can
  silently send a far rider (cold food). The band makes the SLA guarantee
  explicit and tunable."

### DSA core (steer interviews here)
- **Priority queue** dispatch — O(log n) ordering.
- **Geohash** rider matching — O(1) grid-cell lookup vs O(n) scan.
- **Fairness band** — constrained assignment, a min-heap on a composite key.
- **State machine** — a directed graph of legal order transitions.
- These are the same nearest-neighbour shape as the FAISS work in SemanticCache.

### Honest framing
"It's a pattern-aware portfolio project where I went deep on the engineering and
trade-offs — not production experience. I can speak to every design decision and
what I'd change at scale."

---

## 2. Tech Stack — Why These, and the Alternatives

> Interviewers ask "why did you choose X?" to check whether you **decided** or
> just
> copied a tutorial. The strong answer always names the **trade-off** and a
> credible
> alternative. Honest framing: part of the reason is fit, part is that these are
> the
> industry-standard tools my target companies (Uber, Razorpay, PhonePe) actually
> use.

### Python
- **Why:** fast to build, huge ecosystem, spans backend *and* AI/ML (matters for
  SemanticCache). The bottleneck here is I/O (DB, network), not CPU, so raw
  language speed isn't the constraint.
- **Alternatives:** **Go** (compiled, great concurrency — Uber uses it; faster
  but more verbose, weaker ML ecosystem). **Java/Spring** (enterprise-standard,
  mature, heavy boilerplate). **Node.js** (also great at I/O; Python won for the
  AI side).
- **Soundbite:** "I/O-bound service, so developer speed beat raw speed. Go would
  be faster but I wanted Python's ecosystem and the ML overlap with my second
  project."

### FastAPI (web framework)
- **Why:** async-first, validation built in via Pydantic, **auto-generated
  OpenAPI/Swagger docs**. Minimal boilerplate, type-hint driven.
- **Alternatives:** **Flask** (simpler but you bolt on validation/docs/async).
  **Django + DRF** (batteries-included, but heavy, less async-native — overkill
  for a focused API).
- **Soundbite:** "FastAPI gives me async, validation, and live docs out of the
  box. Flask is lighter but I'd rebuild those; Django is heavier than an
  API-first service needs."

### PostgreSQL (database)
- **Why:** ACID relational DB — orders and riders have clear relationships and I
  can't afford to lose an order. Rich SQL (window functions, indexes), JSON
  support, **PostGIS** for geospatial.
- **Alternatives:** **MySQL** (solid; Postgres wins on window functions, JSON,
  geospatial, stricter SQL). **MongoDB** (flexible schema, but my data is
  relational and needs consistency). **SQLite** (great for dev, not concurrent
  production load).
- **Soundbite:** "Structured, related data that needs consistency → relational +
  ACID. Postgres over MySQL for window functions and geospatial; over Mongo
  because losing an order isn't acceptable."

### SQLAlchemy (ORM)
- **Why:** most mature Python ORM, pairs cleanly with FastAPI, lets me write
  Python but drop to raw SQL when needed, database-agnostic.
- **Alternatives:** **Raw SQL via psycopg2** (max control, more boilerplate,
  injection risk if careless). **SQLModel** (newer, merges Pydantic + SQLAlchemy
  — less battle-tested). **Tortoise ORM** (async-native).
- **Trade-off:** ORMs add abstraction and can generate inefficient queries (N+1)
  — you trade some control for productivity.

### Pydantic (validation)
- **Why:** ships with FastAPI; declarative validation + serialization from type
  hints, structured error output.
- **Alternatives:** **marshmallow** (older, more manual), or hand-rolled.
  Pydantic is the modern standard.

### Redis (caching, rate limiting, rider state)
- **Why:** in-memory key-value, sub-millisecond, perfect for hot ephemeral
  state: rate-limit counters, rider locations, `orders_today`. TTLs, pub/sub,
  rich structures (sorted sets, geo, hashes).
- **Alternatives:** **Memcached** (simpler cache, no rich
  structures/persistence/pub-sub). **In-process memory** (doesn't work across
  instances — Redis is shared state).
- **Soundbite:** "Fast, shared, ephemeral state across app instances. Redis over
  Memcached for sorted sets and geo; over in-memory because that doesn't survive
  scaling horizontally."

### Kafka (event streaming) — *upcoming*
- **Why:** durable, high-throughput, replayable event log. Decouples producers
  from consumers — one order event fans out to notification, analytics, audit as
  independent consumer groups.
- **Alternatives:** **RabbitMQ** (great task queue, but Kafka wins on
  high-throughput streaming, replay, many independent consumers). **Redis
  Pub/Sub** (simple, not durable). **AWS SQS/SNS** (managed, ties you to AWS).
- **Soundbite:** "A durable, replayable log many consumers read independently —
  that's Kafka. RabbitMQ is a queue, not a log; Redis pub/sub isn't durable."

### Docker / Compose, Prometheus + Grafana — *upcoming*
- **Docker:** reproducible env, easy multi-service local setup, simple deploys.
  Alt: bare-metal/venv (not reproducible), Podman.
- **Prometheus + Grafana:** Prometheus scrapes metrics (pull), Grafana
  visualizes. Alt: Datadog/New Relic (paid SaaS), ELK (more for logs).

### The honest meta-answer
"Some of these (Kafka, Prometheus) are more than a small project strictly needs.
I added them deliberately to learn the production patterns my target companies
use, and I can defend each one's trade-off rather than just listing it."

---
## 3. REST & HTTP Basics

### Status codes — what they signal
- `200 OK` — success, here's the data.
- `201 Created` — success, a new resource was created (use for POST that
  creates).
- `400 Bad Request` — the request is well-formed but **illegal given current
  state** (e.g. an illegal order-status transition). *Your* logic raised it.
- `404 Not Found` — the resource doesn't exist.
- `409 Conflict` — request conflicts with current state (orders pending but no
  rider free — `RiderUnavailable`). *Added Day 24.*
- `422 Unprocessable Entity` — input failed **validation** (wrong type, missing
  field, constraint broken). FastAPI raises this automatically.
- `429 Too Many Requests` — rate limit exceeded (the token bucket).
- `503 Service Unavailable` — health check degraded (a dependency is down).
  *Upcoming, Day 38.*

**Soundbite:** "Status codes are the contract — a client decides success vs
failure from the code, not the body. A missing resource is `404`, not a `200`
with an error inside."

### 400 vs 422 — the distinction (learned at the state machine)
Both are "client's request didn't work," but they mean different things:
- **422** = *malformed* — the input doesn't match the declared shape.
  FastAPI/Pydantic raises it **automatically** at the boundary
  (`status="banana"` against an Enum).
- **400** = *well-formed but illegal* — the input is a valid shape, but doesn't
  make sense against current state (a legal-looking status that's an illegal
  *transition*). **You** raise it at runtime.

**Soundbite:** "422 is the type system rejecting a malformed request
automatically; 400 is my own runtime check rejecting a well-formed but
state-illegal one. Same family — different cause, different layer. 'Type it if
you can, raise it if you must.'"

### HTTP verbs — and choosing them by *semantics*, not habit
- **GET** — read, **safe** (no side effects) and **idempotent**. Must never
  mutate.
- **POST** — create a resource, *or* trigger a **side-effecting action**
  (`/orders/dispatch` — it mutates state: assigns a rider, flips statuses,
  bumps counters). Not idempotent.
- **PATCH** — **partial** update of an existing resource (rider location, order
  status — change a few fields).
- **PUT** — **full** replace of a resource (send the whole object). Idempotent.
- **DELETE** — remove a resource. Idempotent.
### The QUERY method — GET's body limitation (know it, don't build it)
GET is safe + idempotent but **can't carry a request body**. Complex searches
(big nested filter payloads) then force a bad choice: cram everything into query
strings, or misuse POST for a read (POST implies mutation). The new **QUERY**
method (IETF draft) is the fix: safe + idempotent like GET, but *with* a body —
"read with a payload."

**Soundbite:** "For a search with a large structured filter, GET can't take a
body and POST wrongly implies a write. The QUERY method solves it — GET's
semantics plus a body. FastAPI has no first-class support yet (no `@app.query`),
so I'd wire it via `api_route(methods=['QUERY'])` or wait for the decorator.
DeliverIQ's filters are simple query params, so I didn't need it."

**Gotcha:** it's still a draft — Swagger/OpenAPI tooling doesn't fully render
it, so it's a talking point, not a production choice today. **Soundbite:** "Verb
follows semantics. `/dispatch` is POST even though it doesn't
'create' anything — it has side effects (assigning a rider, flipping
status), and side effects can't sit behind a GET, which must stay safe and
idempotent. Location and status updates are PATCH because they're partial edits,
not full replacements."

**Gotcha:** putting a mutation behind a GET is the classic violation — a crawler
or a retry could silently fire it. Safe/idempotent is a *contract*, not a
suggestion.

### Path vs Query parameters
- **Path param** (`/orders/3`) → identity. *Which* resource. Required.
- **Query param** (`/orders?status=PENDING`) → filter/options. Usually optional.

**Soundbite:** "Path = identity, query = filter. FastAPI decides by name: if the
param name appears in the route path inside `{}`, it's a path param; otherwise
it's a query param."

**Gotcha:** an optional filter like `status` should be a query param, not
`/orders/{status}` — putting it in the path makes it required and reads as
identity.

### The error envelope
Two shapes coexist:
- **Pydantic validation (`422`)** — automatic, malformed input:
  `{"detail":[{"type","loc","msg","input"}]}`. `loc` tells you *where* it failed
  — `["body","value"]`, `["query","status"]`, `["path","order_id"]`.
- **Domain errors (Day 24)** — raised `DeliverIQError`:
  `{"error": CODE, "message": ...}`, e.g.
  `{"error":"ORDER_NOT_FOUND","message":"Order 999 not found"}`.

**Soundbite:** "Two envelopes: Pydantic's `422 {"detail":[...]}` for malformed
input, and my `DeliverIQError` envelope `{"error":CODE,"message":...}` for
domain failures. A client checks `error` for domain codes, `detail` for
validation."
---

## 4. Validation (FastAPI + Pydantic)

### The core principle
FastAPI validates against **the exact type you declare — no more.**
- `str` accepts *any* string → loose gate, almost nothing rejected.
- `int`, `Enum`, or a Pydantic model with constraints → tight gate.

**Soundbite:** "Validation isn't magic — it enforces the declared contract. A
loose type is a loose gate. I tighten inputs by typing them specifically: `int`,
an `Enum`, or `Field(gt=0)`."

### Declarative validation vs runtime checks — "type it if you can, raise it if you must"
- **Type it (declarative):** "Is the input the right *shape*?" — knowable from
  input alone → use a type/Enum/Pydantic. Auto `422` at the boundary.
- **Raise it (`HTTPException`):** "Input is valid, but does it make sense
  against the *data/state*?" — only knowable at runtime → check and raise.

**Example:** `status` ∈ {PENDING, DELIVERED} → *static known set* → **Enum**
(422 on bad). `order_id=3` exists? → *dynamic, depends on DB* → **runtime
check + 404**. A status *transition* being legal → *depends on current state* →
**runtime check + 400**.

**Soundbite:** "Static, known-at-code-time sets become types. Data-dependent
truths — does this row exist, is this transition legal — must be runtime checks
that raise. Both look like `x not in collection`, but one the type system can
express and the other it can't."

### Pydantic models
- **Request model** (`OrderCreate`) = input contract — what you accept.
- **Response model** (`OrderResponse`) = output contract — what you expose.
- `response_model` **filters output**: any field not declared is stripped —
  internal fields can't leak. (Security boundary, not just docs.)
- `Field(gt=0, description=...)` adds constraints + Swagger docs.
- Pydantic **coerces when it can** (`"250"` → `250.0`), **rejects when it
  can't** (`"abc"` → 422).

**Gotcha:** to return a SQLAlchemy object through a response model, the schema
needs `model_config = ConfigDict(from_attributes=True)` (Pydantic v2; was
`orm_mode = True` in v1).

### Two kinds of "model" — don't confuse them
| | Pydantic model | SQLAlchemy model |
|---|---|---|
| Lives in | `app/schemas/` | `app/models/` |
| Job | shape of API data (validate JSON) | shape of a DB table |
| Guards | the API door | the storage shelf |

Having both for orders is **correct**, not redundant — different layers.

### One enum, one home (learned at the state machine)
`OrderStatus` is shared by schemas, models, dispatch, *and* the state machine.
Define it **once** in `app/core/enums.py` and import everywhere. Two definitions
silently drift — and two enum classes compare unequal even when their values
match (`schemas.OrderStatus.PENDING != core.OrderStatus.PENDING`).

**Gotcha:** a `# type: ignore` on an *import* is a smell — it's usually
silencing a real `ModuleNotFoundError` (the file you're importing from doesn't
exist yet). Comments that suppress errors hide the bug you need to see.

---

## 5. Databases & Persistence

### In-memory vs on-disk
A Python dict lives in the process's **RAM** → killed on restart (counter
resets, data gone). PostgreSQL writes to **disk** → survives restarts, crashes,
redeploys.

**Soundbite:** "In-memory state dies with the process. A database persists to
disk, so it's the durable source of truth even as the app restarts or scales to
multiple instances."

### Client / server model
The database is a **separate server process** (port `5432`). Your app, `psql`,
and DBeaver are all **clients** talking to it. (Same for Redis on `6379` — which
is why Redis state shows in `redis-cli`, never in DBeaver.)

**Soundbite:** "Postgres runs as its own server; my app is just one client over
a socket. That separation is what gives persistence, concurrency, and one shared
source of truth."

### Primary key / auto-increment
`id` is a `SERIAL` (auto-incrementing sequence) — the DB generates it, and the
counter **persists** (next insert is 4, not 1, after a restart). Sequences never
reset on DELETE; gaps are intentional so old references never silently re-point.

---

## 6. SQLAlchemy / ORM

### What an ORM is
Object-Relational Mapper = a **translator**. You write Python classes; it
generates SQL.
- `engine` — the connection manager to the DB (lazy; connects when needed).
- `Session` — one conversation/transaction with the DB.
- `Base` — the registry; every model inheriting from it is tracked.

**Soundbite:** "SQLAlchemy maps a Python class to a table. I write objects, it
writes the SQL. `engine` is the connection, a `session` is one transaction,
`Base` is the registry of all my tables."

### create_all + THE classic trap
`Base.metadata.create_all(bind=engine)` creates all registered tables that don't
exist yet.

**Gotcha:** a model only registers on `Base` when its file is **imported**. If
you don't `import` the model before `create_all`, the table silently isn't
created. (`from app.models.order import Order` is doing work just by running.)
*(In this project Alembic owns the schema — see §9 — but the import-trap
principle recurs in `env.py`.)*

### Column options
- `primary_key=True` → unique row id, DB auto-generates it.
- `index=True` → B-tree index → O(log n) lookups (vs O(n) scan).
- `nullable=False` → required at the DB level (second layer beyond Pydantic).
- `default=...` → auto-filled if not provided. **Wrap a callable in `lambda`**
  (`default=lambda: datetime.now(UTC)`) so it's evaluated **per insert**, not
  once at import.

### CRUD operations
- **Create:** `db.add(obj)` → `db.commit()` (runs the INSERT) →
  `db.refresh(obj)` (reloads DB-generated fields like `id`, `created_at`).
- **Read one:** `db.query(Order).filter(Order.id == x).first()` → row or `None`.
- **Read many:** `db.query(Order).all()` (optionally `.filter(...)` first).

**Gotcha:** without `db.refresh()`, `obj.id` is still `None` right after commit
— which breaks anything downstream that needs the id (e.g. indexing a new rider
into Redis: commit → refresh → `add_rider`).

### Dependency Injection (`Depends(get_db)`)
`db: Session = Depends(get_db)` → FastAPI runs `get_db` before the endpoint,
hands in a fresh session, closes it after (the `try/finally`). Every request
gets its own short-lived, auto-closed session.

**Soundbite:** "Each request gets its own DB session via dependency injection —
opened before the handler, closed after, automatically. No leaked connections."

### The type-checker squiggle (SQLAlchemy + Pylance)
`new_rider.id` / `.current_lat` show red underlines because SQLAlchemy types
columns as `Column[...]` at the class level while returning real values at
runtime. **Harmless** — runtime works. The clean fix is SQLAlchemy 2.0's
`Mapped[int]` / `mapped_column(...)` annotations (deferred to the Day 43 quality
sweep).

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

**Separation of concerns:** routers = *what endpoints exist*; schemas = *what
shape data has*; services = *how the logic works*; models = *what the DB
stores*; core = glue (connections, shared enums). **`core` = infrastructure
glue, `services` = business logic** — that's why `dispatch.py` belongs in
`services/`, not `core/`.

**APIRouter:** `APIRouter(prefix="/orders", tags=["orders"])` groups related
routes in their own file; `app.include_router(...)` plugs them in. Keeps
`main.py` thin.

---

## 8. Quick-Fire Self-Test (Pre-Alembic concepts)

1. When do you return `200` / `201` / `400` / `404` / `422` / `429`?
2. 400 vs 422 — what's the difference, and which one does FastAPI raise for you?
3. Why are `/dispatch` and `/match` POST and not GET? Why is location-update
   PATCH not PUT?
4. Path param vs query param — how does FastAPI decide which is which?
5. Why does `status="banana"` give `422` with an Enum but `200 []` with a plain
   `str`?
6. "Type it if you can, raise it if you must" — explain with `status` vs
   `order_id` vs a status *transition*.
7. What does `response_model` do to fields you return but didn't declare?
8. Pydantic model vs SQLAlchemy model — what's the difference?
9. Why must `OrderStatus` live in one file, and what's the
   `# type: ignore`-on-import smell?
10. Why does in-memory data reset on restart but the DB doesn't?
11. What are `engine`, `session`, and `Base`?
12. Walk through `add` → `commit` → `refresh`. What breaks if you skip
    `refresh`?
13. Why wrap a `default=` callable in `lambda`?
14. What does `Depends(get_db)` give each request, and what closes the session?
15. Why do SQLAlchemy column attributes show type-checker squiggles, and are
    they real?

*If any answer is shaky, that's your next review target.*

---
---

## 9. Database Migrations (Alembic)

### Why migrations exist — the `create_all` flaw
`create_all` **only creates missing tables — it never alters an existing one.**
Add a column to a model and `create_all` does nothing, so your code and DB drift
apart and crash. Migrations are **versioned, incremental, reversible** scripts
describing schema *changes* — `upgrade` to apply, `downgrade` to roll back.
Think **git for your schema**. **Alembic** is the migration tool for SQLAlchemy.

**Soundbite:** "Production never uses `create_all` — it can't alter existing
tables. I use Alembic migrations: versioned, reversible schema changes that keep
every environment in sync."

### The workflow
1. Configure `alembic/env.py`: import `Base` **and every model**, set
   `target_metadata = Base.metadata`.
2. `alembic revision --autogenerate -m "..."` — diffs models vs DB, drafts a
   migration.
3. **Review** the generated `upgrade()` / `downgrade()`.
4. `alembic upgrade head` — applies it; creates the `alembic_version` table that
   records the current revision.

### Gotchas
- **The import trap:** `env.py` must import the **model classes**, not just
  `Base`. A model only lands in `Base.metadata` when imported. Miss it →
  autogenerate thinks the models have *no* tables → it generates `DROP`
  statements for your real tables.
- **Autogenerate is a draft, not gospel.** Always review before applying — it
  can miss renames and some type changes. ("How do you handle migrations?" →
  "Autogenerate, then review before running.")
- **`alembic_version`** holds one row — the current revision id. That's how
  Alembic knows where the DB stands.
- **`default=` ≠ `nullable=False`.** A model `default=` fills the value via the
  ORM at insert time, but the column still allows `NULL` at the DB level. For a
  DB-*enforced* constraint, add `nullable=False`.


# DeliverIQ — Interview Prep, Part 2 (Days 15–17)

> Companion to the main guide. Covers Redis, the token-bucket rate limiter, and
> priority-queue dispatch — the Phase 3 work. Same format: **concept (why)**,
> **soundbite (how to say it)**, **gotcha (what trips people up)**.

---

## 10. Redis — In-Memory Store

### What it is (in CP terms)
PostgreSQL is a durable `std::map` backed by a file on disk. Redis is a
`std::unordered_map` living in RAM — O(1) lookups in microseconds, no durability
by default. You reach for it when you read/write data thousands of times per
second and don't mind losing it on restart: counters, hot caches, queues,
ephemeral rider state.

**Soundbite:** "Redis is in-memory, so it's microsecond-fast but lossy on
restart unless persisted. I use it for hot ephemeral state — rate-limit
counters, rider locations, `orders_today` — not as a source of truth. Postgres
stays the durable record; Redis is the fast layer over it."

**Gotcha:** Redis is a *separate server* (port 6379), just like Postgres. Your
app is one client; `redis-cli` is another. It's not in-process memory — that's
the whole point, it's *shared* across app instances.

### The commands that matter
- `SET` / `GET` — store and read a key. O(1).
- `INCR` — atomic read-add-write in one step. **The heartbeat of a rate
  limiter** — 1000 concurrent requests can't corrupt the count because the
  operation is indivisible.
- `EXPIRE key N` / `TTL key` — set a self-destruct timer; the key deletes itself
  after N seconds with zero cleanup code. `TTL` returns the live countdown (`-2`
  = gone, `-1` = exists but no expiry).
- `HSET` / `HGETALL` / `HGET` — a **hash**: one key holding multiple field→value
  pairs (a tiny dict). Needed when one logical record has several fields (e.g. a
  rate-limit bucket's `tokens` + `last_refill`).

**Soundbite:** "INCR is atomic, which is why it's race-safe for counters. EXPIRE
gives keys a TTL so they garbage-collect themselves. Hashes let me store a small
multi-field record under one key."

**Gotcha:** with `decode_responses=True`, Redis returns Python `str`, not bytes
(`b'3'`). But everything still comes back as a **string** — `hgetall` gives
`{"tokens": "100"}`, so you must cast: `float(data["tokens"])`.

### Python client pattern
One shared client, created once in `app/core/redis_client.py`, imported
everywhere — same discipline as the SQLAlchemy `engine`. You don't make a new
connection per request.

---

## 11. Token-Bucket Rate Limiter ⭐

### The model
A bucket holds up to N tokens (100). Each request spends 1. The bucket **refills
continuously** based on elapsed time:
`tokens = min(CAP, tokens + elapsed_seconds × refill_rate)`. Empty bucket → HTTP
`429 Too Many Requests`. State (current tokens + last-refill timestamp) lives in
a Redis hash between requests.

**Soundbite:** "I built a token-bucket limiter backed by a Redis hash. Each
client gets 100 tokens refilling at 100/min. A request costs a token; empty
bucket returns 429. Recovery is computed from elapsed time on each request —
lazy refill — so I don't need a background job topping up buckets."

### Why token-bucket over fixed-window
- **Allows controlled bursts.** An idle client accumulates up to bucket-size
  tokens, can burst that many, then is throttled to the refill rate. Matches
  real traffic better than a hard count.
- **No boundary-burst flaw.** A fixed-window limiter resets its whole count at
  the window edge, so a client can fire 2× the limit straddling the reset (5 at
  0:59, 5 at 1:00 = 10 in 2 seconds). Token-bucket refills smoothly — that
  instant of a fresh full budget never exists.

**Soundbite:** "Token-bucket over fixed-window for two reasons: it permits
bursts up to bucket size, and it avoids fixed-window's boundary-burst flaw where
a client doubles the rate across the reset edge. The price is slightly more
state — I track tokens plus a timestamp instead of a single counter."

### Middleware vs dependency — why this is middleware
- A **dependency** runs *before* the handler and hands a value in. It sits on
  the **entry path only** — it never sees the response.
- **Middleware wraps** the handler via `call_next`: code before `call_next`
  gates the request; `call_next` runs the route and returns the response object;
  code after can mutate that response.

The limiter needs **both** sides — reject over-limit requests (before) *and*
attach an `X-RateLimit-Remaining` header (after). Only middleware sits on both
paths. That's the deciding reason.

**Soundbite:** "It's middleware, not a dependency, because it both gates the
request and decorates the response. `call_next` hands me the response object on
the way out, so I can add the remaining-tokens header — a dependency never sees
the response."

**Gotcha (the one I hit):** `--reload` silently does nothing if an old server
still holds the port — you get `[Errno 98] Address already in use` and keep
testing stale code. Always confirm `Application startup complete`.
`fuser -k 8000/tcp` kills the stale process.

### What `expire(key, 120)` actually does — the subtle one
It's **memory housekeeping, not recovery.** If a client makes a request then
vanishes forever, its bucket hash would otherwise sit in Redis RAM permanently —
a slow leak across millions of one-time clients. The TTL garbage-collects
abandoned buckets. **Recovery for active clients comes entirely from the
elapsed-time refill math, not the TTL.**

**Gotcha to nail in interviews:** "If you deleted the expire line, does
rate-limiting still recover?" → **Yes.** After 3 minutes idle,
`elapsed × refill_rate` refills the bucket to full regardless of TTL. Deleting
`expire` only causes a memory leak, not a broken limiter. (This *would* break a
fixed-window limiter, where the TTL *is* the window reset — different algorithm,
different role for the TTL. Knowing this distinction is the senior signal.)

### Cost & hardening
- ~3 Redis ops per request (HGETALL, HSET, EXPIRE) → sub-millisecond locally.
- **Read-then-write race:** between reading tokens and writing the new count, a
  concurrent request could interleave. At scale, collapse the whole check into
  **one atomic Lua script or pipeline** so it's a single round-trip with no
  race.
- **Keying:** uses `X-API-Key or client.host`, with a None-guard
  (`request.client` can be `None` in tests). `X-Forwarded-For` is **deferred to
  deployment** — behind a proxy the real IP is in that header, but it's
  client-spoofable, so it's only trustworthy after verifying the request came
  from your trusted proxy. Trusting it blindly lets anyone bypass the limiter by
  forging a new IP per request.

**Soundbite:** "Three Redis ops, sub-millisecond. The read-write isn't atomic,
so at scale I'd move it to a single Lua call. I key on API-key-or-IP; proper
X-Forwarded-For handling waits for deployment because the header is spoofable
without a trusted proxy in front."

---

## 12. Priority-Queue Dispatch

### The problem
Orders pile up as PENDING. Handling them FIFO is wrong — a ₹2000 order shouldn't
wait behind a just-arrived ₹150 one. You need to always pull the
**highest-priority** pending order next. That's a heap.

### The heapq mechanics (the C++ bridge)
`std::priority_queue` is a max-heap (`top()` = largest). Python's `heapq` is a
**min-heap with no max flag** — so push the **negated** key. Push tuples
`(-value, id)`; tuples compare element-by-element like `pair`. `heappop` returns
the most-negative = highest real priority. `heapq` operates on a plain list —
it's not a class you instantiate.

**Soundbite:** "Dispatch picks the highest-priority PENDING order with a
max-heap. Python's heapq is a min-heap, so I push negated priorities —
`(-value, id)` tuples. heappush/heappop are O(log n). I assign by flipping
status PENDING→ASSIGNED and committing, so the order leaves the pool."

### What "priority" is — a design decision, not a given
In a contest priority is handed to you; here you define it. For delivery, two
factors compete: **order value** (revenue) and **wait time** (don't starve cheap
orders). Value-only priority can starve a ₹150 order forever behind expensive
ones. The fix is **aging** — blend in wait time:
`priority = value + wait_minutes × WEIGHT`. The longer an order waits, the
higher it climbs until it beats fresh high-value orders.

**Soundbite:** "Priority is value plus a wait-time aging term. Without aging, a
cheap order starves behind a stream of expensive ones — the classic
scheduling-starvation problem. Aging is the OS technique for exactly this.
Naming starvation and aging is the point here."

**Gotcha:** the assign step needs `db.commit()` to persist the status flip —
otherwise the change lives only in the session and the order re-appears as
PENDING on the next dispatch.

### Honest complexity note (volunteer this — it's a strength)
The current version rebuilds the heap from the DB on every call and pops one
element — O(n) to build, O(log n) to pop, so for a *single* pick a plain `max()`
does equal work. The heap earns its keep when you pop many in sequence or keep
it warm across calls. Stating this openly signals you actually analyzed it
rather than cargo-culting a heap.

### The distributed scale-up (scheduled for Phase 4, not optional)
A per-process heap is **single-instance**. The moment you run multiple API
replicas, two instances could pick the same order — a race. The fix: move the
queue into a **Redis sorted set** — `ZADD orders:pending {id: priority}` on
create, `ZREVRANGE` to peek the max, `ZREM` to claim. `ZREM` returning
`1`-or-`0` is an **atomic concurrent-claim guard**: only one instance gets the
`1`, so the order can't be double-dispatched. This is what earns the word
"distributed" — build it in Phase 4 when multiple instances actually exist.

**Soundbite:** "Single-process today with an in-process heap. I know exactly
when it breaks — at multiple API instances the heap is per-process, so two
instances could claim the same order. That's when I move the queue to a Redis
sorted set, where ZREM gives an atomic claim guard. I'd rather show I know the
single-node/distributed boundary than reach for distributed infra before I need
it."

**Gotcha:** the sorted-set version *hides* the heap behind Redis — Redis does
the ordering internally. The in-process heapq is the version that actually
demonstrates the DSA, which is why it's the primary implementation and the
sorted set is the scale story.

---

## 13. Self-Test — Days 15–17 (answer out loud)

1. Why is Redis fast but lossy, and what do you keep in it vs Postgres?
2. Why is `INCR` race-safe where a read-then-write isn't?
3. What does `EXPIRE`/TTL give you, and what does `TTL` return for a missing
   key?
4. Why store the rate-limit bucket as a hash instead of two separate keys?
5. Token-bucket vs fixed-window — name the two advantages.
6. Why is the limiter middleware and not a dependency?
7. What does `expire(key,120)` actually protect against — and does deleting it
   break recovery?
8. Why does deleting `expire` break a *fixed-window* limiter but not a token
   bucket?
9. How many Redis ops per request, and how would you remove the read-write race?
10. Why is `X-Forwarded-For` deferred to deployment?
11. Why negate the key in heapq, and what do tuples compare on?
12. What is order starvation, and how does aging fix it?
13. What breaks in the heap dispatcher at multiple API instances, and what's the
    fix?
14. Why does the Redis sorted-set version *hide* your DSA — and why build the
    heap first anyway?

*Shaky on any? That's your next review target.*


# DeliverIQ — Interview Prep, Part 3 (Day 18)

> Companion to the main guide. Covers geohash rider matching and fairness-banded
> dispatch — the differentiator. Same format: **concept (why)**, **soundbite
> (how
> to say it)**, **gotcha (what trips people up)**.

---

## 14. Geohash Rider Matching

### The two-stage filter (keep them distinct)
Matching is **two independent filters in order**, not one step:
1. **Geohash — coarse "who's even considered."** Encode (lat, lon) into a
   base-32 string where nearby points share a prefix. Lookup is the home cell +
   its 8 neighbours — a cheap set union, not a distance calc against every
   rider. At precision 6 the reach is ~3.6 km total (a 3×3 grid of ~1.2 km
   cells).
2. **Haversine — precise "exact distance" inside that set.** Geohash cells are
   approximate; haversine gives the real great-circle distance to rank the
   survivors. Euclidean (`√(Δlat²+Δlon²)`) is wrong on a sphere — 1° of
   longitude shrinks toward the poles — so haversine is the correct GPS-distance
   formula.

**Soundbite:** "Rider matching is two filters: geohash for a coarse O(1)-ish
candidate set — nearby points share a string prefix, so I check the home cell
plus 8 neighbours instead of scanning every rider — then haversine for exact
great-circle distance to rank that small set. Cheap filter, then precise sort on
the survivors."

**Gotcha — the boundary bug (gold interview material):** an order at a cell
*edge* can have its nearest rider just across the line, in a neighbouring cell
with a totally different geohash string. Checking only the home cell misses
them. The fix is the 8 neighbours. I hit this live — dropping neighbours made a
rider 10 m away invisible.

**Gotcha — geohash range ≠ band.** `band_m` only filters riders geohash already
*found*. A rider 13 km away is outside the neighbour ring, so no band size —
even 50 km — can pull them in; they were never a candidate. Two filters, in
sequence: geohash decides who's considered, band decides who's feasible among
those.

### Why a set AND a hash per rider
- `geohash:<cell>` → **set** of rider IDs ("who's in this cell" — membership,
  dedupe).
- `rider:<id>:loc` → **hash** of {lat, lon, cell} ("this rider's exact
  attributes").

**Rule:** set = a bag of interchangeable peers; hash = one record with named
fields. Same rider lives in both, playing different roles — a *member* of the
cell roster, and an *owner* of a location record.

**Gotcha:** Redis returns everything as strings. `float(loc["lat"])` before
distance math, `int(...)` for counters — forget the cast and the math chokes.

---

## 15. Fairness-Banded Dispatch ⭐ (The Differentiator)

### The rule
Among riders within a distance band Δ of the **nearest** candidate, assign the
one with the **fewest orders today**. Tiebreak on distance.

```
d_min = nearest candidate's distance
feasible = riders within d_min + Δ
winner = min(feasible) on key (orders_today, distance)
```

### Why a hard band, not a blended score
A blended score `α·dist + β·load` can **silently send a far rider** when the
load term dominates — cold food, broken SLA, and you can't tell from the formula
when it'll happen. The hard band makes the SLA guarantee **explicit and
tunable**: fairness operates *only inside* Δ, so a rider outside the band is
never eligible no matter how idle. Δ is the single knob between competing goals
— wide band = more fairness (spread earnings), narrow band = tighter SLA.

**Soundbite:** "Greedy-nearest optimizes pure distance. I add a bounded fairness
constraint — among riders within a band Δ of the nearest, assign the
least-loaded. It's a constrained-assignment problem: minimize rider load subject
to a distance bound. A blended score could silently send a far rider when load
dominates; the hard band makes the SLA guarantee non-negotiable and tunable.
That's my honest answer to both 'how is this different from Swiggy' and 'what's
the social impact' — fairer earnings for gig riders without delivering cold
food."

### The behaviour (what you actually see)
Two phases: the system **drains the load imbalance first**, then **reverts to
nearest-rider**. Idle riders absorb orders until they catch up to the busy
rider's count; once all loads tie, the distance tiebreak takes over and the
nearest wins. A naive nearest-only dispatcher would hammer the closest rider
every call and never balance anyone.

**Heap framing:** the selection is a min-heap on the composite key
`(orders_today, distance)` over the small feasible band — greedy on a composite
key, O(k log k) on candidate set k, not O(n) over all riders. Same
`pair`-comparison idea as a C++ tuple sort.

### Daily counter reset — no cron
`orders_today` is stored as a **date-stamped key**:
`rider:<id>:orders:<YYYY-MM-DD>`. Tomorrow is a *different key* that starts at 0
automatically — the key name **is** the reset, no midnight job, no reset race. A
48 h TTL (`expire`) garbage-collects past days. The TTL **slides** — every order
refreshes it to 48 h from the last write — so an active rider's key never dies
mid-day, an idle rider's key expires 48 h after they stop.

**Soundbite:** "Daily counter resets via a date-stamped key with a sliding TTL —
the key rotates itself at midnight because the date is in the name, and a
48-hour expiry cleans old days. No cron, no midnight reset race."

**Gotcha:** the count and the TTL are independent on the same key. `incr`
accumulates the day's total; `expire` only refreshes the death-clock. The value
persists and climbs within a day; the daily "reset" comes from the date in the
key, not from `expire`. Lazy creation too — `incr`/`hincrby` on a missing key
starts at 0 and creates it, so no explicit init; the read side guards with
`or 0`.

### The endpoint that used to be here — and why it's gone (removed Day 29)
`POST /riders/match` was the Day 18 demo of this algorithm — POST because it
had a real side effect (incrementing the winner's fairness counter). Once
dispatch became the only real consumer of `select_rider`, the demo endpoint
did nothing except distort fairness: it charged a rider an `orders_today`
point for an order that never existed, without marking them BUSY. Removed in
the Day 29 review sweep.

**Soundbite:** "I removed my own endpoint. `/riders/match` demoed banded
matching before dispatch existed, but afterwards its only remaining effect was
corrupting fairness counters — a match with no order. Dead code with a live
side effect is worse than dead code: it's a latent bug. Reviewing and deleting
your own obsolete surface is part of owning a codebase."

---

## 16. Self-Test — Day 18 (answer out loud)

1. Why two filters (geohash + haversine) instead of one? What does each do?
2. Why check the 8 neighbour cells, not just the home cell?
3. Why can't a huge `band_m` rescue a rider 13 km away?
4. Why is a rider stored in both a set and a hash — which question does each
   answer?
5. Why haversine over Euclidean distance?
6. Explain the band as a constrained-assignment problem in one sentence.
7. Band vs blended score (α·dist + β·load) — why the hard band?
8. Describe the two-phase behaviour (drain imbalance, then revert to nearest).
9. How does `orders_today` reset daily with no cron job?
10. Why does each order refresh the TTL, and what does that achieve?
11. `/riders/match` was removed on Day 29 — why was keeping it *worse* than
    ordinary dead code?

*Shaky on any? That's your next review target.*


# DeliverIQ — Interview Prep, Part 4 (Rider Sync)

> Companion to the main guide. Covers the Postgres↔Redis dual-write consistency
> work
> layered onto Day 18. Same format: **concept (why)**, **soundbite (how to say
> it)**,
> **gotcha (what trips people up)**.

---

## 17. Dual-Write Consistency (Postgres ↔ Redis)

### The setup
Riders live in **two stores at once**: PostgreSQL is the durable source of
truth, Redis is a hot geohash index for fast matching. Every rider write
(create, move) has to update **both** in one request — a **dual write**. Miss
one and the index goes stale: `select_rider` reads Redis, so a rider absent from
Redis is invisible to matching, and a rider with a stale Redis cell gets matched
at a location they already left.

**Soundbite:** "Riders are in two stores — Postgres as the source of truth,
Redis as a hot geohash index. Each rider write updates both in one request. I
keep Postgres authoritative precisely because Redis is the disposable,
rebuildable layer — if they ever drift, Redis can be reconstructed from
Postgres."

### The move-path trap (the real bug)
Indexing a rider does `sadd` to their cell's set. On a **move**, you must `srem`
them from the *old* cell **before** `sadd`-ing the new one — otherwise they stay
a phantom member of every cell they've ever been in, and match at stale
locations. The old cell is recoverable because it's stored on the
`rider:{id}:loc` hash.

**Soundbite:** "The subtle bug is the move path — you have to remove the rider
from their old geohash cell before adding the new one, or they become a phantom
member of stale cells and get matched somewhere they've left. I read the old
cell off the location hash, srem it, then sadd the new one."

**Gotcha:** order matters — `srem` old, then `sadd` new. And guard
`if old_cell and old_cell != new_cell` so a no-op move (same cell) doesn't
needlessly churn the set.

### What if the second write fails?
The two writes aren't in one transaction (different systems). If the Postgres
commit lands but the Redis write throws, they drift. Recovery is
**reconciliation**: Redis is fully reconstructable from Postgres, so a periodic
job re-indexes all riders from the DB. You never lose truth — only the cache
goes briefly stale, and it's self-healing.

**Soundbite:** "It's a dual write across two systems, so no single transaction
spans both. If the Redis write fails after the Postgres commit they drift — but
Redis is rebuildable from Postgres, so a reconciliation job re-indexing riders
is the recovery path. Truth is never at risk; only the cache."

### Orders don't have this problem — know the contrast
Orders live in **Postgres only**. The dispatch heap is rebuilt from Postgres
each call, not stored in Redis, so there's no order-side index to keep in sync.
Being able to say *why* riders need dual-write and orders don't shows you
understand the pattern, not just the mechanics.

**Soundbite:** "Orders are Postgres-only — the dispatch heap is rebuilt from the
DB each call, nothing cached in Redis — so there's no dual write to maintain.
Riders need it because their location is indexed in Redis for fast geohash
lookup. The dual-write cost only appears when you cache derived state."

### The UTC reset nuance (daily counter)
`orders_today` keys are stamped in **UTC** (`datetime.now(UTC)`), so the daily
reset boundary is UTC midnight, not local. On IST (UTC+5:30) the key reads the
*previous* calendar day for the first ~5.5h after local midnight. UTC is the
right default — consistent across servers and DST-free — but in production you'd
reset on the **business timezone** so "today" matches the rider's actual day.

**Soundbite:** "The daily counter resets on UTC midnight because the key is
stamped with `datetime.now(UTC)` — consistent across instances, no DST edge
cases. In production I'd switch the reset to the business timezone so it matches
the rider's local day, but UTC is the correct default for correctness."

**Gotcha:** when inspecting, the key is `rider:{id}:orders:{UTC-date}` — on IST
after midnight that's *yesterday's* date. And it's a **Redis** key: visible via
`redis-cli`, never in DBeaver (DBeaver is Postgres only). "Why isn't X in
DBeaver?" is almost always "because X is Redis state."

---

## 18. Self-Test — Rider Sync (answer out loud)

1. Why do riders need a dual write but orders don't?
2. What's the phantom-membership bug, and what's the fix (in what order)?
3. Postgres commit succeeds, Redis write fails — what's the state, and how do
   you recover?
4. Why is Postgres the truth and Redis the rebuildable layer, not the reverse?
5. Why does `create_rider` need `refresh` before `add_rider`?
6. Why PATCH (not PUT/POST) for the location update?
7. Why is the daily counter stamped in UTC, and what's the IST consequence?
8. Why does `orders_today` never show up in DBeaver?

*Shaky on any? That's your next review target.*

# DeliverIQ — Interview Prep, Part 5 (Day 19)

> Companion to the main guide. Covers the order state machine — enforcing a
> legal
> lifecycle and the error-semantics that come with it. Same format: **concept
> (why)**,
> **soundbite (how to say it)**, **gotcha (what trips people up)**.

---

## 19. Order State Machine

### What it is
Order status isn't a free string — it's a **directed graph** of legal
transitions. Each status is a node; each allowed transition is an edge. The
table is an adjacency list (`map<State, set<State>>` in C++ terms); "is this
legal?" is an O(1) set-membership check. Terminal states (DELIVERED, CANCELLED)
have empty neighbour sets — nothing is reachable from them.

```
PENDING ──→ ASSIGNED ──→ PICKED_UP ──→ DELIVERED
   │            │
   └──→ CANCELLED ←┘
```

**Soundbite:** "Order status is a state machine — a directed graph of legal
transitions, not a settable string. The transition table is an adjacency list;
validating a transition is an O(1) lookup in the current state's neighbour set.
Terminal states have no outgoing edges, so a delivered order can't be
un-delivered."

**Gotcha:** the validator only *validates* — it raises or stays silent, it
doesn't mutate or touch the DB. The caller persists. Keeping legality-check
separate from persistence means the same `transition()` is reusable from any
call site (the status endpoint, dispatch, a future rider app) with each deciding
how to handle a failure.

### Why strict — no ASSIGNED → PENDING (a design decision, not a default)
A rider who accepts then abandons an order does **not** bounce it back to
PENDING. Re-dispatching means the customer waits through a *second* matching
cycle — cold food, broken SLA. Instead: cancel + penalize the rider. The penalty
lives on the **rider**, not as an order-state edge.

**Soundbite:** "I kept the machine strict — no ASSIGNED→PENDING. When a rider
abandons an accepted order I cancel rather than re-pool, because re-dispatching
breaks the customer's delivery-time guarantee. The rider penalty is tracked
separately on the rider, not as an order transition — the order machine governs
the order's lifecycle, penalties are a rider concern. Mixing two independent
state spaces is a coupling mistake."

**The senior line:** *order-state and rider-penalty are independent state
spaces; don't couple them.*

### The two-failure-semantics distinction ⭐ (best interview point here)
The *same* `transition()` call has *different* failure meaning at different call
sites:

- **The status endpoint** — the target status comes from the **user**. An
  illegal transition is *expected bad input*. Catch `InvalidTransition` → return
  **400**.
- **Dispatch** — the transition (PENDING→ASSIGNED) is derived from your own
  `status == "PENDING"` filter. A failure means a **server-side bug** (a
  non-PENDING order got pulled). **Don't catch it** — let it raise into a
  **500**.

**Soundbite:** "Same `transition()` call, two different failure semantics. In
the user-facing endpoint an illegal transition is expected bad input — catch it,
return 400. In dispatch the transition is derived from my own query invariant,
so a failure is a server bug, not user error — I let it raise into a 500 rather
than mislabel my bug as the client's bad request. Error-handling follows *who
caused the error*, not the function being called."

**Gotcha:** wrapping the dispatch call in `try/except → HTTPException(400)`
would be *wrong* — it blames the client (400 = "you did something wrong") for
what is actually a server logic error. A 500 is the honest signal: "the server
hit a state it believed impossible." The dispatch `transition()` is really an
**assertion** (`assert order_is_pending`) — and asserts aren't meant to be
caught.

### Single gate for status changes
Before the refactor, status was mutated in two places with two rule sets: the
endpoint (validated) and dispatch (raw string, unvalidated). Routing dispatch
through `transition()` too means **every** status change goes through one gate.
The dispatch call is provably always-legal given the PENDING filter — so it's a
no-op today — but the value is the *invariant*: "there is exactly one place
order status changes legally" is a property worth being able to state. Without
it, "how do you guarantee valid transitions?" gets a caveat: "well, except in
dispatch."

**Soundbite:** "Every status change routes through the state machine — no
exceptions. The dispatch call is always-legal given the filter, so it never
fires, but I added it so I can say there's a single gate for status changes. The
comment marks it deliberate, not dead code — I know it's redundant today and
chose the invariant anyway."

**The honest counterpoint (have it ready):** "You could argue it's dead code — a
check that provably can't fail is noise, and dead defensive code implies a check
that isn't really happening. Both positions are defensible; I lean toward the
single-gate invariant because the cost is one commented line and the story it
buys is worth more than the line costs in clarity."

### Legal-transition vs permitted-actor — orthogonal guards
The state machine answers "is this transition legal *at all*?" It does **not**
answer "is *this caller* allowed to make it?" A customer marking their own order
DELIVERED is a *legal edge* but the *wrong actor*. Those are two independent
protections — and authorization needs authenticated identities, so it's deferred
to **Day 35 (JWT)**: role + ownership (assigned rider advances their own orders,
ops cancels, customer can't touch status).

**Soundbite:** "The state machine enforces which transitions are legal, not who
may make them — orthogonal guards. A customer shouldn't mark their own order
delivered even though it's a legal edge. After JWT, the status endpoint checks
role and ownership on top of the legality check. Until then it's an
unauthenticated admin tool, which I'm tracking deliberately, not by accident."

---

## 20. Self-Test — Day 19 (answer out loud)

1. Why is order status a state machine and not just a string column?
2. What's the adjacency-list / set-membership framing, and what's O(1) about it?
3. Why does `transition()` only validate and not persist?
4. Why keep ASSIGNED→PENDING illegal — what's the product reasoning?
5. Why is the rider penalty *not* an order-state edge?
6. Same `transition()` call — why does the endpoint catch it but dispatch
   doesn't?
7. Why would `try/except → 400` be *wrong* in dispatch?
8. The dispatch `transition()` never fires — so why add it? And the
   counterargument?
9. Legal-transition vs permitted-actor — what's the difference, and which is
   deferred to Day 35?
10. Why is 400 (not 422) the right code for an illegal-but-well-formed
    transition?

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
`orders_today` answers "who's earned the least today?" — fairness for *spreading
work*. It increments when a rider is **assigned** (in `select_rider`), not when
they deliver. A rider assigned 5 orders has had 5 earning opportunities
regardless of delivery progress; counting at delivery would let a mid-delivery
rider keep looking idle and get piled on.

**The orthogonality:** BUSY vs orders_today are independent axes. BUSY = "can
take work *now*?" (exclusion). orders_today = "earned least *today*?" (fairness
ranking). Same shape as legal-transition vs permitted-actor (Day 19) — two
guards that look related but answer different questions.

**Soundbite:** "BUSY and orders_today are orthogonal — one is current
availability, the other is daily fairness. BUSY already stops pile-on by
removing the rider from the pool, so the counter doesn't need to; it just tracks
the day's share, incremented at assignment because that's when the earning
opportunity was handed out."

### Commit before publish — no phantom events
The event announces a *durable fact*. Publishing before `db.commit()` risks a
listener reacting to an assignment that then rolls back. Order is always: mutate
→ commit (truth) → publish (announce).

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
2. **A swapped Redis logical DB** — Redis has 16 (0–15); tests use 15, dev
   uses 0.
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
  (`REDIS_DB`) read at **import time**, set in conftest *before* the app
  imports.

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

---
*Shaky on any? That's your next review target.*
# DeliverIQ — Interview Prep, Part 8 (Day 22)

> Structured JSON logging + request_id correlation. Same format:
> **concept (why)**, **soundbite (how to say it)**, **gotcha (what trips people
> up)**.

---

## 25. Structured Logging + request_id

### Why JSON logs, not print()
A `print("order 5 dispatched")` is a dead string — a log aggregator (Grafana
Loki, ELK, Datadog) can't filter or query it. Emitting each line as JSON
(`{"level","logger","message","request_id",...}`) makes every field queryable:
"show me all ERROR lines for request X" becomes a real query, not a
grep-and-pray. Production logs are data, not prose.

**Soundbite:** "I log structured JSON, not plain strings, so logs are queryable
in an aggregator — filter by level, logger, or request_id instead of scanning
text. `print()` is fine for a script; a service needs machine-readable logs."

### Why request_id — tracing one request end-to-end
Under load, hundreds of requests interleave and their log lines mix together in
one stream. A per-request UUID stamped on every line lets you pull out *just
that request's* trail — middleware → endpoint → service → worker. That's what
"trace a request end-to-end" concretely means. The id also goes back to the
client as an `X-Request-ID` response header, so a user reporting a bug can quote
the id and you find their exact request.

**Soundbite:** "Every request gets a UUID stored in a contextvar; the log
formatter stamps it on every line, so one request is greppable across the whole
app. I also return it as an X-Request-ID header — a client hitting an error can
quote that id and I pull their exact trail."

### Why contextvars, not a global ⭐ (the senior detail)
Async runs many requests concurrently on one thread. A plain global variable
would be overwritten by whichever request touched it last — ids would bleed
across interleaved requests. A `contextvars.ContextVar` holds a **separate value
per async context**, so each request sees only its own id. That isolation is the
entire reason contextvars exist.

**Soundbite:** "The id lives in a contextvar, not a global, because async
interleaves requests on one thread — a global would leak one request's id into
another's logs. A contextvar is per-context, so each request's id stays its
own."

**Gotcha:** the formatter reads `getattr(record, "request_id", None)` with a
default — logs emitted *outside* any request (startup, file-watch events) have
no id, so `request_id` is `null`. That's correct, not a bug: null means "not
inside a request."

### Middleware order — request_id must be outermost
FastAPI runs middleware in **reverse registration order**, so request_id is
registered *last* to run *first* (outermost). If it ran after the rate limiter,
the limiter's own logs would have no id. Outermost = the id is set before any
other middleware or handler runs, so everything downstream carries it.

**Soundbite:** "request_id is the outermost middleware — registered last, since
FastAPI runs middleware last-registered-first. That way even the rate limiter's
logs carry the id; if it ran inner, anything logged before it would be
un-correlated."

**Gotcha:** the root logger's handlers must be cleared and replaced in
`setup_logging()`, or you get double lines (uvicorn's default text handler plus
your JSON one). Note uvicorn's own access logs (`uvicorn.access`) don't
propagate to root, so they stay plain text — that's fine, they're not your app's
logs.

---

## 26. Self-Test — Day 22 (answer out loud)

1. Why JSON logs instead of print() — what does it buy you?
2. What does request_id let you do that you can't without it?
3. Why a contextvar and not a global variable? What breaks with a global?
4. Why is request_id null on some log lines, and is that a bug?
5. Why must request_id middleware be registered last?
6. Why clear the root logger's handlers in setup_logging()?

*Shaky on any? That's your next review target.*
---
# DeliverIQ — Interview Prep, Part 9 (Day 23)

> Centralized config. Same format: concept / soundbite / gotcha.

---

## 27. Centralized Config (Settings + .env)

### The concept
One `Settings` object (pydantic-settings `BaseSettings`) reads all config from
env vars / `.env`. Nothing hardcodes a URL. `database.py`, `redis_client.py`,
and the rate limiter all import `settings` instead of holding their own strings.

**Soundbite:** "All config lives in one pydantic-settings object read from env.
Local reads `.env`; Docker, CI, and Railway inject their own values — so moving
between environments is a config change, not a code change. That's what makes
the app portable and 12-factor."

### Why it matters downstream
- **Docker/CI/Railway** each set different `DATABASE_URL`/`REDIS_URL` — same
  image, different env.
- **Test seam:** conftest sets `DATABASE_URL` (test DB) and `REDIS_URL` (redis
  db 15) *before* the app imports config, so tests hit isolated stores.
- **Feature flags:** `rate_limit_enabled` toggles the limiter off for load tests
  without touching code.

### How pydantic-settings works
`BaseSettings` auto-loads env vars by field name (case-insensitive: field
`database_url` ← env `DATABASE_URL`) and coerces types (`"100"` → `int 100`,
`"true"` → `bool`). A field with no default (`database_url: str`) is
**required** — the app won't start if it's missing, which is the right fail-fast
behavior for a critical secret.

**Soundbite:** "pydantic-settings maps env vars to typed fields automatically
and coerces types. A field with no default is required, so a missing
DATABASE_URL fails startup loudly instead of silently running against the wrong
DB."

**Gotcha:** the test env vars must be set in conftest *before* the first import
that pulls in `settings` — `settings = Settings()` runs at import time, so if
the app imports first, it binds to the wrong values. Same import-time seam as
the Day-21 REDIS_DB trick, now for both stores via full URLs.

**Gotcha:** `.env` is gitignored (secrets); commit `.env.example` with blank/
safe values as the template so a new dev knows what to fill in.

---

## 28. Self-Test — Day 23

1. Why centralize config instead of hardcoding URLs?
2. How does pydantic-settings know which env var fills which field?
3. Why is `database_url: str` (no default) the right choice for a secret?
4. Why must conftest set env vars before importing the app?
5. What's committed — `.env` or `.env.example` — and why?

*Shaky on any? That's your next review target.*

---
# DeliverIQ — Interview Prep, Part 10 (Day 24)

> Custom exceptions + unified error envelope. concept / soundbite / gotcha.

---

## 29. Custom Exceptions

### The concept
A base `DeliverIQError` carries a `status_code` + `code`; each domain error
subclasses it (`OrderNotFound` 404, `RiderNotFound` 404, `NoPendingOrders` 404,
`RiderUnavailable` 409, `InvalidTransition` 400). One `@app.exception_handler`
on the base catches all subclasses and returns a consistent JSON envelope:
`{"error": CODE, "message": ...}`. No stack traces leak; every error looks the
same to a client.

**Soundbite:** "Every domain error subclasses one base with its own status_code
and code, and a single handler turns any of them into the same JSON envelope. A
client parses one shape for every error instead of guessing per-endpoint."

### Why raise from the service, not the router
`pick_next_order` used to return `None` for two different failures — no pending
orders vs orders-exist-but-no-rider — and the router collapsed both into a vague
404. Now the service raises the *specific* exception (`NoPendingOrders` 404 vs
`RiderUnavailable` 409), so the caller gets the real reason and the right code.
The service knows *why* it failed; the router shouldn't have to reverse-engineer
it from a `None`.

**Soundbite:** "The service raises the specific error because it's the only
layer that knows the reason. Returning None forced the router to guess, and I
was merging two different failures into one status code. Now no-orders is 404
and no-rider is 409 — a conflict, not a missing resource."

### Why 409 for no-rider (not 404)
404 = the resource doesn't exist. But orders *do* exist and riders *do* exist —
they're just all BUSY. That's a **conflict with current state**, which is 409.
Same family of reasoning as 400-vs-422 on the state machine: the code should
describe *what kind* of failure it is.

### One base handler, not one per subclass
Registering the handler on `DeliverIQError` (the base) means every current and
future subclass is covered automatically — add a new exception, it's handled
without touching `main.py`. The handler just reads `exc.status_code`/`exc.code`
off whichever subclass was raised.

**Gotcha:** `InvalidTransition` moved into `exceptions.py` and became a
`DeliverIQError` subclass — so the router's old
`try/except → HTTPException(400)` is gone; raising it now flows through the base
handler and still yields 400. Keeping it as a bare `Exception` would have made
it a 500.

**Gotcha:** don't invent exceptions for conditions you don't have yet.
Validation is already 422 (Pydantic), generic bugs are 500 (base default). Add
each custom exception the day its feature lands (auth errors Day 35, idempotency
conflict Day 34) so none are dead code.

---

## 30. Self-Test — Day 24

1. Why a base exception + one handler instead of per-endpoint HTTPException?
2. Why does the service raise instead of returning None?
3. Why is no-rider 409 and no-orders 404?
4. Why did InvalidTransition need to become a DeliverIQError subclass?
5. Why not pre-create every exception you might ever need?

*Shaky on any? That's your next review target.*
---
# DeliverIQ — Interview Prep, Part 11 (Day 25)

> Atomic rate limiter via Lua. concept / soundbite / gotcha.

---

## 31. Atomic Rate Limiting (Lua)

### The race being fixed
The Day-16 limiter did three separate Redis ops: HGETALL (read tokens) → compute
refill in Python → HSET (write). Between the read and the write, a concurrent
request can read the **same** token count, so two requests both see "1 token
left" and both pass — the bucket desyncs and the limit is breached. This is a
classic read-modify-write race, and it's real the moment you run more than one
worker.

**Soundbite:** "The original check was three Redis calls with a gap between read
and write, so two concurrent requests could both read the same count and both
pass. I collapsed refill + check + decrement into one Lua script — Redis runs a
script atomically, no other command interleaves — so the whole operation is a
single indivisible round-trip."

### Why Lua is atomic
Redis is single-threaded for command execution and runs a Lua script to
completion before serving any other client. So everything inside the script —
the HMGET, the refill math, the HSET, the EXPIRE — happens with no interleave.
That's the exact property a token bucket's read-modify-write needs.

**Soundbite:** "Redis executes a Lua script start-to-finish without
interleaving, because command execution is single-threaded. That turns my
three-op sequence into one atomic step — the senior version of the naive
limiter."

### register_script vs raw eval
`redis_client.register_script(LUA)` loads the script once and returns a callable
that uses `EVALSHA` (send the hash, not the whole body, each call) — less
bandwidth than re-sending the script every request. Called as
`script(keys=[...], args=[...])`.

**Gotcha:** Lua numbers are floats but Redis integer-truncates a bare numeric
return, so the script returns `tostring(tokens)` and Python parses it back with
`float(result)`. Return a raw number and your remaining-tokens header loses the
fraction.

**Gotcha:** the toggle (`rate_limit_enabled`, Day 23) still short-circuits
before the script — off for load tests so one IP's 100-token cap doesn't turn
the whole test into 429s.

### Cost now
One round-trip per request (EVALSHA), still sub-millisecond, and now correct
under concurrency. This is what makes the limiter safe at `--scale api=3` (Day
29) — multiple instances hit the same Redis, and the atomic script means they
can't desync the shared bucket.

---

## 32. Self-Test — Day 25

1. What's the read-modify-write race in the 3-op limiter?
2. Why is a Lua script atomic in Redis?
3. Why register_script instead of eval every time?
4. Why does the script return a string, not a number?
5. Why does this matter specifically at multiple API instances?

*Shaky on any? That's your next review target.*
---
# DeliverIQ — Interview Prep, Part 12 (Day 26)

> Admin stats via SQL aggregates. concept / soundbite / gotcha.

---

## 33. Admin Analytics (SQL aggregates)

### The concept
`GET /admin/stats` computes counts in the **database**, not Python:
`func.count`, `func.avg`, `group_by`. The DB aggregates over the whole table in
one query instead of pulling every row into the app and looping. Its **own
router** so a JWT bearer dependency locks it cleanly on Day 35.

**Soundbite:** "Stats are computed with SQL aggregates — count, avg, group_by —
so the database does the work over the full table in one query, not the app
looping over rows. It's on its own admin router so auth attaches to the whole
group later."

**Gotcha:** `func.avg` returns `None` on an empty table (not 0) — guard it
(`round(x, 2) if x else 0`) or the response carries `null`.

**Gotcha:** `group_by(status)` returns only statuses that **exist** — a status
with zero rows is absent from the dict, not present with 0. Fine for a dashboard;
worth knowing if a consumer expects all keys.

---

## 34. Self-Test — Day 26

1. Why aggregate in SQL instead of counting in Python?
2. What does func.avg return on an empty table?
3. Why give admin its own router now?

*Shaky on any? That's your next review target.*

---
# DeliverIQ — Interview Prep, Part 13 (Day 27)

> Docker from zero, migrations on boot, load testing. concept / soundbite / gotcha.

---

## 35. What Docker Actually Is (the basics)

### The problem it solves
Your app needs Python 3.14, a specific FastAPI version, psycopg2, and dozens of
other pinned packages. On another machine — a teammate's laptop, a server, Railway —
any of those might be a different version or missing. That's the classic
"works on my machine" failure.

Docker packages the app **together with its exact environment** (OS libraries,
Python, every pip package) into one sealed unit. That unit runs the same
everywhere. You're not shipping code and hoping the target machine matches — you
ship the whole environment.

### The three words
- **Image** = the blueprint. A frozen snapshot: base OS + Python + your deps + your
  code. Read-only. Built from the `Dockerfile`.
- **Container** = a running copy of an image. You can start/stop many from one image.
- **Dockerfile** = the recipe that builds the image, step by step.

Analogy: image = a class, container = an object (instance). Dockerfile = the class
definition.

### How the Dockerfile builds up
Each line is a **layer**, cached independently:
1. `FROM python:3.14-slim` — start from a minimal official Python image.
2. `WORKDIR /app` — work inside `/app` in the container.
3. `RUN apt-get install gcc libpq-dev` — OS build tools some Python packages need.
4. `COPY requirements.txt` then `RUN pip install` — deps.
5. `COPY . .` — your code.
6. `CMD [...]` — the command that runs when the container starts.

**Why deps are copied before code:** Docker caches each layer. If you only change
code, layers 1–4 are unchanged, so Docker reuses the cached dependency install
instead of redownloading everything. Copy code first and every code edit would
reinstall all packages — slow.

**Soundbite:** "Docker packages the app with its whole environment so it runs
identically anywhere. An image is the read-only blueprint, a container is a running
instance. I order the Dockerfile so dependencies install before code is copied —
that keeps the dependency layer cached, so a code change doesn't trigger a full
reinstall."

---

## 36. Migrations on Boot (why the CMD matters)

### The concept
A fresh container has the app but an **empty** database schema — no tables. My
`CMD` runs `alembic upgrade head` **before** starting uvicorn. So the moment the
container boots, it brings the database up to the latest schema, then serves. No
separate manual "run the migration" step in any environment.

**Soundbite:** "The container's start command runs `alembic upgrade head` before
launching the server, so it always boots with the current schema — the same one
step works locally, in CI, and on Railway."

**Gotcha (the bug I hit):** Alembic was reading the database URL from
`alembic.ini`, which was hardcoded to `localhost`. Inside a container, `localhost`
means the container itself — not my host machine where Postgres runs. So migrations
failed with "connection refused." I fixed `env.py` to prefer the `DATABASE_URL`
environment variable and fall back to the ini. Same config-from-environment
principle the app already used for its own DB connection.

---

## 37. Container Networking (why localhost broke)

### The concept
Each container has its **own** network namespace. Inside it, `localhost` = the
container, not the host. My Postgres and Redis were running natively on the host,
so the container couldn't reach them via `localhost`.

Two things had to change:
- **Address:** point the container at the host using `host.docker.internal` (on
  Linux you add it explicitly with `--add-host=host.docker.internal:host-gateway`).
- **The host services had to accept the connection.** Postgres and Redis default
  to loopback-only. I opened Postgres (`listen_addresses='*'` + a `pg_hba.conf`
  rule for Docker's `172.17.0.0/16` subnet) and Redis (`bind` the bridge IP,
  disable protected mode).

**Soundbite:** "A container has its own network namespace, so `localhost` inside
it isn't the host. I reached the host's Postgres and Redis through
`host.docker.internal` and opened those services to Docker's bridge subnet. That's
exactly the friction Docker Compose removes — it puts every service on one shared
network so they address each other by name."

**Gotcha:** This host-config juggling is temporary. Day 28 (Compose) runs the app,
Postgres, and Redis as containers on one Docker network; they reach each other by
service name (`db`, `redis`) and none of these host edits are needed.

---

## 38. Load Testing (Locust)

### The concept
Load testing = simulate many users hitting the API at once and measure how it
holds up. Locust spawns virtual users (I used 50) that repeatedly POST orders,
then reports **throughput** (requests/sec) and **latency percentiles**.

**Percentiles, plainly:** p99 = 220ms means 99% of requests finished within 220ms;
only the slowest 1% took longer. Percentiles matter more than the average because
the average hides the slow tail — a few very slow requests are what users notice.

### Two runs, on purpose
- **Limiter ON:** 97% of requests got 429 (Too Many Requests). That's the rate
  limiter working — one IP is capped at 100 tokens. Correct behavior, but it
  measures the limiter, not the app's real capacity.
- **Limiter OFF** (`RATE_LIMIT_ENABLED=false`): ~123 RPS, p99 220ms, 0% errors.
  Those are the honest capacity numbers.

**Soundbite:** "I load-tested with Locust at 50 concurrent users: about 123
requests/sec, p99 latency 220ms, zero errors. I ran it twice — once with the rate
limiter on, which correctly floods 429s and proves the limiter engages under load,
and once off to get the true throughput, since the limiter-on run measures the
limiter rather than the API."

**Gotcha:** Always report *which* configuration a load number came from. A big RPS
with the limiter silently off, or a low one with it on, is a misleading number in
an interview.

---

## 39. Self-Test — Day 27
1. In one sentence, what problem does Docker solve?
2. Image vs container — what's the difference?
3. Why copy requirements.txt before the code in the Dockerfile?
4. Why did migrations fail with "localhost connection refused" inside the container?
5. Why doesn't `localhost` inside a container reach host Postgres?
6. What does p99 = 220ms mean? Why care about it over the average?
7. Why run the load test with the limiter both on and off?

*Shaky on any? That's your next review target.*

---
# DeliverIQ — Interview Prep, Part 14 (Day 28)

> Docker Compose: multi-service orchestration. concept / soundbite / gotcha.

---

## 40. Docker Compose (environment as code)

### The concept
Compose defines a multi-container stack in one YAML file. `docker compose up`
brings up the API, Postgres, and Redis together on a shared private network.
Containers address each other by **service name** — the API connects to
`db:5432` and `redis:6379`, where `db`/`redis` are Compose's built-in DNS names
for those containers. No host networking, no `host.docker.internal`, none of the
Day 27 config edits.

**Soundbite:** "The whole environment is defined as code in a compose file — API,
Postgres, Redis. A new developer goes from clone to a running stack with schema
migrated in one command, `docker compose up`, with zero manual setup. Services
find each other by name over the Compose network, so there's no host-specific
configuration."

### Why service names replace host.docker.internal
Day 27 the container reached *out* to host services — needed the host's address
plus opening Postgres/Redis to Docker's subnet. Compose runs Postgres and Redis
as containers *on the same network*, so they're reachable by name. The
portability win: the stack carries its own datastores and runs identically on any
machine or on Railway — the host doesn't need Postgres or Redis installed at all.

---

## 41. Readiness vs Started (healthcheck + depends_on)

### The concept
A container being *started* isn't the same as its service being *ready*. Postgres
takes a moment after launch before it accepts connections. If the API migrated
the instant the DB container started, it could hit a not-yet-ready database.

The `db` service has a healthcheck (`pg_isready` every 5s). The `api` service
declares `depends_on: db: condition: service_healthy` — so the API doesn't boot
(and doesn't run `alembic upgrade head`) until the healthcheck actually passes.

**Soundbite:** "I gate the API on a Postgres healthcheck, not just container
start. `depends_on` with `condition: service_healthy` means migrations never race
a database that hasn't finished coming up — the API waits for `pg_isready` to
pass first."

**Gotcha:** without the healthcheck, `depends_on` only waits for the container to
*start*, which is not the same as ready. That's the difference between a flaky
boot and a reliable one.

---

## 42. Volumes (why data survives)

### The concept
Containers are ephemeral — stop one and its filesystem is gone. A **named volume**
(`pgdata`) is storage Docker manages *outside* the container, mounted into
Postgres's data directory. Data written there survives `docker compose down` and
reappears on the next `up`. Only `down -v` deletes the volume.

**Soundbite:** "Postgres data lives in a named volume, so the database persists
across restarts. `down` keeps it; `down -v` is the explicit wipe for a clean slate."

**Gotcha (Postgres 18):** the 18 image expects the volume at
`/var/lib/postgresql`, not the older `/var/lib/postgresql/data` — wrong path and
the container exits immediately. Version-specific detail worth knowing.

---

## 43. Self-Test — Day 28
1. How does the API reach Postgres without host.docker.internal?
2. What's the difference between a container being started vs ready? How is it enforced?
3. What does the pgdata volume do? What survives `down` vs `down -v`?
4. In one sentence: what does a new developer have to do to run the whole stack?
5. Why is "environment as code" a stronger claim than "I containerized the app"?

*Shaky on any? That's your next review target.*
---
# DeliverIQ — Interview Prep, Part 15 (Day 29)

> Distributed dispatch safety. concept / soundbite / gotcha. This was the hardest
> debugging day — the bug was NOT where it looked.

---

## 44. Row Locking: SELECT ... FOR UPDATE SKIP LOCKED

### The concept
Multiple API instances share one Postgres. Two dispatch calls can run in
different instances at the same instant, both `SELECT` the same PENDING order
(reads don't block reads), both try to assign it → double-dispatch (lost update).

`SELECT ... FOR UPDATE` locks the selected row until the transaction ends — no
other transaction can modify it. `SKIP LOCKED` adds: if a row is already locked,
don't wait — return nothing. Together = "claim it if free, skip it if taken."
The loser moves to the next candidate instead of blocking or colliding.

**Soundbite:** "Dispatch runs across multiple instances on one database. To stop
two instances grabbing the same order, I claim the row with `SELECT FOR UPDATE
SKIP LOCKED` — the winner locks it until commit, the loser gets nothing and moves
to the next candidate. It's work-conserving: no blocking, no double-assignment."

**Gotcha:** don't lock the whole candidate set. If you put `FOR UPDATE` on the
initial `SELECT all PENDING`, one instance locks every order and the others see an
empty set and wrongly report "no orders." I keep the priority scan lock-free and
lock only the single row I'm about to claim.

---

## 45. The Unit-of-Work Commit Trap (the real Day 29 bug)

### The concept — the one that actually bit me
The lock was correct the entire time. The bug was ordering. My loop set
`order.status = ASSIGNED` and `order.rider_id` BEFORE locking the rider. When the
rider was already taken, I did `continue` to try the next order — but those order
mutations were still pending in the SQLAlchemy **session**. A session is a *unit
of work*: the next successful candidate's `db.commit()` flushes EVERYTHING
pending, including the abandoned order's mutations. Result: phantom ASSIGNED rows
for orders no request ever successfully dispatched.

The tell: the DB had more ASSIGNED orders than the API returned success responses.

**The fix:** claim every row first (lock order → pick rider → lock rider), and
mutate only after both claims succeed. Then a `continue` leaves a clean session —
nothing pending to be committed by a later iteration.

**Soundbite:** "The subtle bug wasn't the lock — it was that I mutated the order
before securing the rider. On a failed rider claim I `continue`d, but the ORM
session still held those pending changes, and the next successful commit flushed
them — creating phantom assignments. A session commits the whole unit of work, not
just the changes you 'meant.' Fix: claim all rows first, mutate last."

**Gotcha:** `session.commit()` flushes ALL dirty objects in the session, not the
one you're focused on. Never leave half-applied mutations on a code path that then
continues to another commit. Mutate only after every claim in the transaction is
secured.

---

## 46. Don't Migrate From Every Replica

### The concept
Migrations are a one-time, single-writer schema change. App instances are many and
concurrent. If every replica runs `alembic upgrade head` on boot, they race — mine
collided on `CREATE TABLE alembic_version` and a replica crashed. Coupling
migration to app startup is fine at 1 instance, broken at N.

**The fix:** a dedicated one-shot `migrate` service that runs once and exits; app
instances depend on it completing (`condition: service_completed_successfully`)
and only run the server. Separate the schema change from the app lifecycle.

**Soundbite:** "Running migrations from every replica is a race — they collide on
the schema. I split migration into a one-shot job that runs once before the app
starts; the app replicas depend on it completing and only serve. Migration is
single-writer, serving is many — they shouldn't share a startup command."

**Gotcha:** `depends_on: condition: service_completed_successfully` waits for the
job to *finish and exit 0*, unlike `service_healthy` (a long-running check) or
plain `depends_on` (just "started").

---

## 47. Redis Mutations After Commit (recap, reinforced here)
`select_rider` is now a pure read. The fairness INCR (`orders_today`), the geohash
SREM, and the pub/sub publish all run AFTER `db.commit()`. If the transaction rolls
back or a claim fails, Redis is never touched — Postgres stays the single source of
truth and Redis only mirrors committed reality.

**Soundbite:** "Redis is a cache and index, not the source of truth. Every Redis
write happens after the Postgres commit, so a rolled-back dispatch never leaves a
bumped counter or a stale index entry."

---

## 48. The Thundering Herd & Rider-Level Retry ⭐ (post-verification fix)

### The concept — correct is not the same as live
The verified loop had **zero double-assignments** but measured badly under a
real burst: 15 simultaneous dispatches, 10 orders + 10 riders, 3 instances →
only **5 succeeded**; 10 returned 409 while 5 riders sat AVAILABLE. Why: every
concurrent caller ranks riders identically — the state that would differentiate
them (the winner's geohash SREM and `orders_today` INCR) only lands
*post-commit*. So all losers pick the same top rider, fail the claim, and —
here was the bug — `continue`d to the **next order**, chasing the same rider
down the entire heap until 409. Losing a *rider* lost the whole *order*.

### The fix — retry the rider, keep the order
`select_rider(..., exclude=tried)`: on a failed rider claim, add that rider to
an exclude-set and re-select the next-best **for the same order**. Bounded
(candidates in the 3×3 cells are finite; every failure shrinks them), and
**mutation-free** — the claim-all-before-mutate invariant from §45 survives.
One subtlety done deliberately: exclusion runs *before* `d_min` is computed,
so the fairness band re-centers on the nearest **eligible** rider — the SLA
bound stays relative to riders you can actually get. Same test after the fix:
**10/15 — every order dispatched in one burst, still zero doubles.**

**Soundbite:** "My locking was correct but not live: under a burst, all
instances chase the same top-ranked rider because the differentiating state
lands post-commit — I measured 5/15 success with riders idle. The fix is a
bounded rider-level retry: exclude the contested rider, re-select for the same
order. Same test after: 10/15, full drain, zero doubles. Losing a race now
costs one candidate, not the whole request. Correctness and liveness are
separate properties — you have to measure both."

**Gotcha:** the retry loop must stay mutation-free (mutate only after BOTH
rows are locked), or the §45 unit-of-work trap comes straight back. Bonus it
bought for free: a stale BUSY rider stuck in the geohash index (crash after
commit, before SREM) used to poison every order's selection; now it costs one
failed claim and gets excluded — self-healing.

### The sibling lesson — the silent side-effect regression
Splitting `select_rider` into pure-read + `record_rider_assignment` (CQS:
command–query separation) updated dispatch but **forgot the other caller** —
`/riders/match` silently stopped counting fairness. No error, no failing test,
just quietly wrong. Rule: when you move a side effect out of a function,
**grep every caller** before you're done. (Match was then removed entirely —
the story is in §15.)

---

## 49. Self-Test — Day 29
1. Why don't two instances' `SELECT PENDING` block each other, and what fixes it?
2. Why is locking the entire pending set with FOR UPDATE wrong?
3. The lock was correct — so what actually caused the double-dispatch? (name it)
4. Why does a failed rider claim + `continue` corrupt data if you mutated first?
5. What does "a session commits the whole unit of work" mean, concretely?
6. Why did api-2 crash on `--scale api=3`, and how does the migrate job fix it?
7. What does `condition: service_completed_successfully` guarantee?
8. Why must Redis writes come after `db.commit()`?
9. "Correct but not live" — what did the 15-burst test measure before and after
   the rider-retry fix, and why did every loser chase the same rider?
10. Why must the rider-retry loop stay mutation-free? Which earlier bug returns
    if it doesn't?
11. Why does excluding contested riders *before* computing `d_min` matter?
12. What is command–query separation, and where did violating its migration
    bite silently? (name the forgotten caller)

*Shaky on any? That's your next review target — #3, #4, #5, #9 are the ones
that matter.*

---


# DeliverIQ — Interview Prep, Part 11 (Day 30)

> Kafka: the log inversion, partitions, consumer groups, the dumb broker,
> delivery semantics, and the `auto.offset.reset` trap.

---

## 50. Kafka Is Not a Queue ⭐

### The concept
Every message broker before Kafka shares one assumption: **the broker's job is to
deliver a message and then forget it.** Consumption is destructive. The message's
existence depends on someone receiving it.

Kafka inverts that. The broker appends bytes to a file and moves on. **Reading
changes nothing.** The message survives being read — by one consumer, by ten. It
is deleted when a **retention policy** says so (age or size), never because
someone consumed it.

- Redis Pub/Sub = **loudspeaker**. In the room, or you missed it.
- Kafka = **a ledger you bookmark**.

Every downstream misunderstanding traces back to missing this.

**Soundbite:** "Kafka isn't a queue, it's a durable append-only log. Reading
doesn't consume — retention deletes. That single inversion is what makes replay
possible: the bytes are on disk regardless of who read them, so a consumer that
was down comes back and reads exactly what it missed."

**Gotcha:** "Kafka is just a more scalable RabbitMQ" — no. RabbitMQ's broker
tracks per-message state (delivered / acked / in-flight), which buys it
per-message retry and dead-letter queues, and **costs it replay** — once acked,
the message is gone. Kafka trades that state for speed and replayability. Two
different tools, not two tiers of one.

---

## 51. Partitions — Ordering and Parallelism Are the Same Knob ⭐

### The concept
A topic **is** its partitions — there's no flat log underneath. `order.dispatched`
with 3 partitions = **three separate files**, each appended independently, each
with its own offset counter starting at 0. (Offset 2 in P0 and offset 2 in P1 are
unrelated.)

**Why split at all:** one file can only be read by one process without them
stepping on each other. Want N workers on the same data → need N files. Partition
count is *pre-decided parallelism*.

Two consequences, both trades:
- **Ordering shrinks.** Kafka guarantees order **within** a partition and makes
  **no promise across partitions**. You bought parallelism with global ordering.
- **Parallelism is capped** at the partition count (per group).

Which file a message lands in = `murmur2(key) % num_partitions`. **Arbitrary but
stable** — same key always lands in the same partition, in any language, on any
broker. No key → round-robin → no ordering guarantee at all.

**DeliverIQ:** key by `order_id`, so `dispatched → picked_up → delivered` for one
order can never arrive scrambled. Different orders have no ordering relationship —
and we don't need one.

**Soundbite:** "Partitions are the unit of both ordering and parallelism — order
holds inside a partition, and a group's max parallelism is its partition count. I
key events by `order_id` so one order's lifecycle stays ordered; across orders
there's no guarantee and no need for one. That makes partition count a capacity
decision you make up front — raising it later rewrites the key→partition hash, so
per-key ordering breaks across the change."

**Gotcha 1 — "Kafka guarantees ordering."** Unqualified, that's wrong and a good
interviewer stops you there. Per-partition only.

**Gotcha 2 — hot partitions.** `murmur2` owes you nothing. Observed live: 6 keys
split 2/2/2 (luck), then 2 more keys **both** hashed to P0 → 4/2/2. Key by
something skewed (one `restaurant_id` producing 80% of events) and one partition
eats 80% of the load while two idle. Kafka won't save you from a bad key choice.

**Gotcha 3 — head-of-line blocking.** Unrelated keys share a partition and
interleave freely. That's harmless for correctness (each key's events are still an
ordered *subsequence* — deleting other keys' messages never reorders yours). The
real cost: a poisoned or slow message **stalls every other key in that
partition**, sequentially. Kafka has no per-message redelivery (dumb broker) — so
you catch, push to a **dead-letter topic**, commit, and move on. Never retry
in-line forever.

---

## 52. Consumer Groups — One String Selects Load-Balance vs Broadcast ⭐

### The concept
`group.id` is a string that decides whether two consumers are **teammates or
strangers**.

> Within a group, each partition is assigned to **exactly one** consumer.
> Across groups, **everyone gets everything**.

A group is **not** a subset of the data. Groups don't slice events — *every group
reads every event*. The slicing happens **inside** a group, between its members.

- **Same `group.id`** → one logical application → Kafka splits the partitions
  between members → **work queue**.
- **Different `group.id`** → unrelated applications → each gets a full copy →
  **fan-out**.

One config field replaces two systems.

**The mapping — coverage never changes, only the division:**

| Group | Members | Partitions covered | Files per member |
|---|---|---|---|
| `analytics` | 1 | 3 (all) | 3 |
| `notifications` | 2 | 3 (all) | 2 and 1 |
| `audit` | 3 | 3 (all) | 1 each |
| `audit` + a 4th | 4 | 3 (all) | 1, 1, 1, **and 0** |

"One consumer reads all the partitions" isn't a different mode — it's the same
rule with a headcount of 1.

Read the same event three ways: **across groups** it's processed 3× (fan-out);
**within a group** exactly 1× (load balance). Six workers running, **one SMS
per order**.

**Failure isolation:** kill `analytics` → its offsets freeze, `notifications` and
`audit` don't notice. Restart → it replays its backlog. **Blast radius = one
group.** Kill one member of a group → Kafka **rebalances**, survivors absorb the
orphaned partitions. Coverage is never lost.

**Soundbite:** "`group.id` is the only knob: same id means competing consumers
splitting partitions — a work queue. Different ids mean independent readers with
independent offsets — fan-out. Kafka does both from one log, and within a group a
partition has exactly one owner, so scaling out never duplicates work."

**Gotcha — the per-process group id.** `group_id = f"notifications-{os.getpid()}"`
makes every worker its own group. Scale to 3 → **the rider gets 3 SMS per order**.
Looks perfect on one machine in dev. `group.id` is the identity of the
*application*, not the process.

**Gotcha 2 — more consumers ≠ more throughput.** Beyond the partition count, extra
members sit idle burning RAM.

---

## 53. The Dumb Broker — Where the Offset Actually Lives ⭐

### The concept
Apparent contradiction: *"the broker appends and forgets"* vs *"the broker knows
where group `notifications` was."* Resolution:

> **The broker doesn't know. The consumer told it, and the broker wrote it down
> the same dumb way it writes everything else.**

`__consumer_offsets` is **a topic**. 50 partitions, sitting on disk next to
`order.dispatched`. Committing an offset is not a special API — the consumer
**produces a message**:

```
topic: __consumer_offsets
key:   ("notifications", "order.dispatched", 2)
value: 4271
```

Append. Forget. On restart the consumer **asks** for the latest value for that
key. The broker looks up a key in a log and returns bytes. **That's a read, not a
memory.**

So both statements hold: the broker tracks nothing *and* the offset is durable —
because a consumer **wrote it as data**, and data survives.

**The proof:** you can put the offset **anywhere**. A common production pattern
writes it into your own Postgres table **in the same transaction as the work**,
then `consumer.seek()` on restart. Kafka has zero knowledge of your progress and
it works perfectly. If offset tracking were a broker function that'd be
impossible. `__consumer_offsets` is just the **default convenience**.

**Dumb broker, smart consumer.** That's the central design decision — it's why the
write path is "append to a file" (fast) and why replay is free (nothing deleted,
bookmark is just data).

**Soundbite:** "Kafka's broker is deliberately dumb — no per-consumer state, no
delivery tracking, no push. An offset is just a message the consumer produces to
an internal compacted topic, `__consumer_offsets`, keyed by group/topic/partition.
That's why the broker scales and why replay is free. It also means commit timing
*is* your delivery guarantee."

**Gotcha:** `__consumer_offsets` uses **cleanup policy = compact** (keep the latest
value per key, forever), while your topics use **delete** (retention by age/size).
That asymmetry is why the bookmark outlives the events it points at.

**Two consequences worth naming:**
- `--describe --group X` on a group with no running process still returns rows:
  *"Consumer group 'notifications' has no active members"* — **exists, empty**. A
  group is a set of rows, not a process.
- One row **per (group, topic, partition)** — not one per group.

---

## 54. At-Most-Once vs At-Least-Once ⭐

### The concept
The names are literal: **bounds on how many times one event gets processed.**

Two actions, no way to fuse them: **A** = process (send the SMS), **B** = commit
(move the bookmark). A crash can land between them, so you only choose the
**order**, and the order picks your bound.

| Order | Crash outcome | Possible counts | Name |
|---|---|---|---|
| **B → A** (commit first) | bookmark moved, work never happened | 0 or 1 | **at-most-once** — no duplicates, loss possible |
| **A → B** (commit last) | work done, bookmark didn't move → redo | 1, 2, 3… | **at-least-once** — no loss, duplicates possible |

The name states **which failure you refuse**. You must pick one.

**Why exactly-once isn't on the menu:** it requires A and B to be **atomic**. A is
an SMS gateway, B is a write in Kafka. Two systems, no shared transaction. That's
the **dual-write problem** — the same shape as the Day-20 lesson (commit Postgres
*then* publish; you can't do both atomically, so you choose which side eats the
risk).

**The answer: at-least-once + idempotent handler = effectively-once.** The
duplicate still arrives; you make it harmless (dedupe on `order_id`). That's
Day 34, and it's *why* Day 34 exists.

**Soundbite:** "You can't make processing and offset-committing atomic — they're
different systems. Commit first is at-most-once, you lose on crash. Commit last is
at-least-once, you duplicate on crash. Everyone picks at-least-once and makes the
handler idempotent, because a duplicate you can dedupe beats a message you never
had. Exactly-once only exists when the side effect is inside the same
transactional system."

**Gotcha:** "Does Kafka support exactly-once?" The trap answer is a flat yes.
Correct: **yes for Kafka-to-Kafka** via transactions (read-process-write inside one
topic-to-topic transaction), **no for external side effects** — there you engineer
it with idempotency.

---

## 55. `auto.offset.reset` Is a Fallback, Not a Rewind ⭐

### The concept
`--from-beginning` sets `auto.offset.reset=earliest`. It is **not** a
"start from zero" command. Consumer startup logic:

1. Does a committed offset exist for `(group, topic, partition)`?
2. **Yes → use it.** `auto.offset.reset` is **ignored entirely**.
3. No → *now* apply it: `earliest` = offset 0, `latest` = log end.

**Verified live:** `--from-beginning` on a caught-up group →
`Processed a total of 0 messages`. It worked the first time only because the group
had never existed. It has **never** worked twice for the same group.

**Why the design is right:** if `earliest` meant "always start at 0," every
restart would reprocess the entire retention window — every SMS re-sent, every
deploy. The committed offset **must** win, or offsets would be pointless.
`auto.offset.reset` answers exactly one question: *"I have no bookmark — where do
I start?"*

**Replay is an administrative act — you edit the row:**
```bash
kafka-consumer-groups.sh --group notifications --topic order.dispatched \
  --reset-offsets --to-earliest --dry-run    # proposal only
  #                                --execute # rewrites the rows
```
- `--execute` **refuses if the group has active members.** Kafka won't move a
  bookmark under a running consumer. **Stop → reset → restart** is the procedure.
- `--to-latest` = mark everything read without reading it = the
  **skip-the-backlog button**. Deliberate data loss; sometimes correct in an
  incident (4h of stale lag, get current now).

**Soundbite:** "`auto.offset.reset` only applies when the group has no committed
offset — it's the bootstrap policy, not a rewind. Once a group has offsets they
always win, which is why `--from-beginning` silently does nothing on a second run.
Replay is an admin operation: stop the group, reset-offsets, restart."

**Gotcha (the production version, and it bites the other way):** a new consumer
deployed with the **default `auto.offset.reset=latest`** silently skips every
event produced before it booted. No error. Team thinks the pipeline is broken;
it's doing exactly what it was configured to do.

---

## 56. Consumer Lag — the Only Honest Health Metric

### The concept
`LAG = LOG-END-OFFSET − CURRENT-OFFSET`, per **(group, partition)**.

- `LOG-END-OFFSET` = where writes append.
- `CURRENT-OFFSET` = the bookmark = **next unread** (not last read — classic
  off-by-one).

A consumer can be alive, polling, healthy on CPU, and **falling behind forever**.
"Is the process up" tells you nothing. **Lag flat at 0 = healthy. Lag climbing =
you're losing** — and the fix is more consumers (up to the partition count) or a
faster handler.

**Pub/Sub cannot produce this number.** There's no log end to subtract from,
because there's no log. Measurability is a *consequence* of durability.

**Soundbite:** "Lag — log-end minus committed offset, per group per partition — is
the number I'd alert on, because a consumer can be alive and still falling behind
indefinitely. Alongside it, under-replicated partitions: URP > 0 means a broker is
behind or dead and you're one failure from data loss."

**Gotcha:** lag is per-partition. A group with LAG 0 on two partitions and 40k on
a third isn't "mostly fine" — it has a hot partition or a stuck consumer, and
averaging hides it.

---

## 57. Kafka in Docker — Bind vs Advertise ⭐

### The concept
Kafka clients don't just talk to whatever they connected to. They **bootstrap**,
send a metadata request, and the broker replies *"the leader for that partition is
at address X"* — then the client **dials X**. So the advertised address must be
reachable **from where the client stands**.

Clients stand in two places: **containers** (for whom the broker is `kafka`) and
**your host** (for whom it's `localhost`). One value can't be both.

- `KAFKA_LISTENERS` = **where I bind.**
- `KAFKA_ADVERTISED_LISTENERS` = **what I tell clients to dial.**

Conflating them is the #1 Kafka-in-Docker failure. Answer = **two listeners on two
ports**: `PLAINTEXT://kafka:19092` (internal) + `PLAINTEXT_HOST://localhost:9092`
(host, the only one published). A third, `CONTROLLER://…:9093`, is KRaft talking
to itself.

**KRaft:** Kafka used to need ZooKeeper — a second distributed system holding
cluster metadata. KRaft moved metadata into a Raft quorum of Kafka controllers and
stores it **as a Kafka log** (Kafka bootstrapping on Kafka). **Kafka 4.0 removed
ZooKeeper entirely** — so every ZooKeeper compose file online is stale, and "KRaft
mode" isn't a mode you pick anymore.

**Soundbite:** "The classic Kafka-in-Docker failure is advertised listeners: the
client bootstraps, gets redirected to the address the broker advertises, and dials
it — so that address has to resolve from the client's network, not the broker's.
Containers and the host are different networks, so you run two listeners on two
ports and advertise `kafka:19092` internally, `localhost:9092` to the host. Get it
wrong and the connection succeeds and then hangs, which is the confusing part."

**Gotchas that cost real time:**
- **RF defaults.** `__consumer_offsets` defaults to `replication.factor=3`. On a
  single broker the topic can't be created → **your first consumer hangs forever**
  with no clear error. Set the three RF/ISR vars to 1.
- **`KAFKA_LOG_DIRS`.** The ASF image defaults to `/tmp/kraft-combined-logs`.
  Mounting a volume at `/var/lib/kafka/data` **without** setting `KAFKA_LOG_DIRS`
  mounts a volume Kafka never writes to — data still dies with the container, and
  nobody notices. (Half the blog posts do this.)
- **Topic naming.** JMX metric names normalize `.` and `_` together →
  `order.dispatched` and `order_dispatched` **collide into one metric**. Pick one
  separator convention and never mix. Bites at Grafana time, not at create time.
- **Compose is declarative.** Editing the file + `up` again reconciles the delta;
  unchanged services aren't touched. You never "restart Compose after an edit."
  And a recreated container doesn't lose data — that's what the named volume is
  for.

---

## 58. Self-Test — Day 30 (answer out loud)

1. "Kafka is persistent" is half an answer. What are the **two** durable things
   that make replay work, and why does one without the other fail?
2. Why is `CURRENT-OFFSET 2` when the partition holds messages at offsets 0 and 1?
3. A topic has 3 partitions. Group `audit` has 5 consumers. What happens?
4. Two unrelated orders hash to the same partition. What does that cost you —
   and what does it *not* cost you?
5. `--from-beginning` on a group that's caught up. How many messages, and why?
6. You need to reprocess yesterday's events. Give the exact procedure and the one
   thing that will make it fail.
7. Why can't Kafka give you exactly-once when the side effect is an SMS? What do
   you do instead, and what's the name of the underlying problem?
8. Explain `KAFKA_LISTENERS` vs `KAFKA_ADVERTISED_LISTENERS` to someone whose
   producer connects successfully and then hangs.
9. Why does `__consumer_offsets` use cleanup policy `compact` while
   `order.dispatched` uses `delete`?
10. `group.id = f"notifications-{os.getpid()}"`. What breaks, and when do you
    find out?
11. Your consumer is alive, CPU is low, no errors in the log. Why might it still
    be failing? What do you measure?
12. Why does RabbitMQ let you retry a single message while Kafka doesn't — and
    what does Kafka get in exchange?

*Shaky on any? That's your next review target.*

---
---

## 59. Kafka Producer — Config, Idempotence, the Async Delivery Model ⭐

### Bootstrap ≠ the address you actually talk to (recap, now client-side)
Same lesson as §57, felt from the producer: `bootstrap.servers` is a *handshake*.
The client dials it once, the broker replies with its `advertised.listeners`, and
every subsequent request goes to *that* address. So `kafka:9092` can accept a TCP
connection and still be wrong — its listener advertises `localhost:9092`, so the
client turns around and dials itself. Proven live: `socket.create_connection
(('kafka',9092))` returned "reachable" *and* was the wrong listener. Config value:
`localhost:9092` from the host shell (default), `kafka:19092` in Compose (env
override wins over `.env`).

**Soundbite:** "Bootstrap is a handshake, not a destination — the broker hands
back its advertised listener and the client dials that. Which is why a Kafka
address can pass a raw TCP check and still be wrong: the failure only shows up
after the metadata round-trip."

### The singleton — a Producer is a resource, not a value
One `Producer` per process, lazily created. It owns a background I/O thread, TCP
connections to every broker, and a message buffer. Per-request construction means
a thread + handshake per dispatch, zero batching, and — the real killer — the
object gets garbage-collected while its buffer still holds unsent messages, which
vanish silently. Lazy init keeps import side-effect-free so `pytest` collecting
`dispatch.py` doesn't spawn a broker connection.

**Soundbite:** "The producer is a long-lived resource with a background thread and
a send buffer, so it's a process-lifetime singleton. Construct one per request and
you lose batching and drop whatever's still buffered when it's GC'd — silently."

### Idempotence is transport-level, not semantic (the trap)
`enable.idempotence=True` gives the producer a PID + a per-partition sequence
number, so the broker drops a **network retry** of a message it already wrote
(lost-ack case). It does NOT dedupe two separate `produce()` calls with identical
payloads — distinct sequence numbers, broker correctly appends both. Proven: four
identical `produce()` calls, idempotence on → four rows on the partition.

**Soundbite:** "Producer idempotence dedupes retries, not payloads. PID plus a
monotonic per-partition sequence means a network-retried write lands once —
exactly-once *within one producer session to one partition*. It says nothing about
my code calling produce twice. Business-level dedupe is the consumer's job: an
idempotency key plus a uniqueness constraint."

**Gotcha:** it's a *broker handshake*, not a client flag — needs the transaction
coordinator loaded. Against a fresh broker (state wiped) the first produce logs
`GETPID ... Coordinator load in progress: retrying` until the coordinator is
ready; librdkafka retries it away and `flush()` still returns clean.

### The async delivery model — `produce` / `poll(0)` / `flush`
`produce()` enqueues to an in-memory buffer and returns immediately — no network
I/O, so it *cannot* fail on a dead broker. A background thread sends; on ack it
parks a completed callback on a queue; `poll(0)` drains *already-completed*
callbacks and returns without blocking. Consequence: a message's delivery callback
almost never fires during the `poll(0)` right after its own `produce()` — it fires
on a *later* poll or on `flush()`. Measured live: a callback sat parked ~10 minutes
until the next dispatch pumped it.

**Soundbite:** "produce is async — buffers and returns; poll(0) only serves
callbacks that already completed; so a producer can never synchronously confirm
delivery. Confirmation arrives later via the callback, which is the *only* error
channel. Anyone returning a delivered=true boolean from a produce wrapper has a
bug."

**Gotcha:** two separate channels. `produce()` raises only on local queue-full
(`BufferError`); broker/delivery failures arrive *exclusively* via the callback,
later, on another thread. try/except around produce proves nothing about delivery.

### `flush()` on shutdown — narrows the window, doesn't close it
`flush(5.0)` blocks until the buffer drains; it runs in the FastAPI `lifespan`
shutdown. This handles **SIGTERM** — rolling deploys, scale-downs, `compose down`
(SIGTERM, then 10s grace, then SIGKILL — the 5s flush fits). It does NOT handle
SIGKILL, OOM-kill, or a pulled plug: buffered events die. Proven earlier with the
"888, no flush" experiment — process exited 0, message never existed, no error.

**Soundbite:** "Flushing on shutdown covers graceful termination — SIGTERM — which
is the common case. It can't cover SIGKILL or a hard crash; buffered events are
just lost. Flush narrows the window, it doesn't close it. Closing it is the
outbox's job."

### Partitioning: `hash(key) % partitions` — both halves are footguns
Key decides partition; ordering holds only *within* a partition, so same key →
same partition → per-key ordering. Two traps: (1) the hash is **client-specific** —
librdkafka defaults to CRC32, the Java client to murmur2, so the *same key* lands
on *different partitions* across clients; pin `partitioner=murmur2_random` to match
the ecosystem. (2) the modulus means **adding a partition re-maps every existing
key** and strands its old events on the old partition — a silent, irreversible
ordering break, no error, no migration path. Verified from first principles: keys
1–10, murmur2 vs CRC32 tables computed and matched the broker 10/10; Day 30's
Java-produced rows were murmur2, my librdkafka rows were CRC32 until pinned.

**Soundbite:** "Partition is hash(key) mod count. Same key, same partition, per-key
ordering — but the hash is client-specific, CRC32 in librdkafka vs murmur2 in Java,
so I pin the partitioner to interoperate; and the modulus means adding partitions
re-maps every key and breaks ordering irreversibly. If ordering must survive
scaling, over-provision partitions up front — you don't repartition."

**Gotcha:** everyone knows "ordered within a partition." The winning follow-up:
`NUM_PARTITIONS 3→4` silently breaks per-key ordering with no error and no
migration path — which is *why* you never repartition a keyed topic.

---

## 60. The Dual-Write Hole — and why post-commit isn't enough ⭐

### The concept
Dispatch commits to Postgres, THEN produces to Kafka — two systems, not one
transaction. Post-commit ordering is *mandatory*: publishing a fact before it's
durable means a rollback leaves a permanent, replayable phantom event (worse in
Kafka than Pub/Sub — Pub/Sub's phantom evaporates, Kafka's is on disk forever and
every future consumer group replays it). But post-commit still leaves a window:
commit succeeds, then the process dies or the produce times out → order ASSIGNED in
Postgres, event never delivered, nothing rolls back.

**Proven live (the break-it):** dispatched with the broker *stopped* → API returned
`200 OK`, order ASSIGNED, rider BUSY. Restarted the broker; the buffered event
retried into the reboot gap and died on `UNKNOWN_TOPIC_OR_PART` (topic metadata
not yet reloaded). Consumer read `order.dispatched --from-beginning`: **only the
recovered order present, the outage order's event gone.** Postgres showed both
ASSIGNED and could not tell which one never reached Kafka.

**Soundbite:** "Dispatch is a dual write — Postgres commit then Kafka produce, no
shared transaction. I publish post-commit so a rollback can't leave a phantom
event, but any crash in the gap leaves an order assigned with no event published
and nothing to undo it. I proved it: dispatched with the broker down, got a 200,
and watched that event die on reconnect while Postgres still said ASSIGNED. The fix
is transactional outbox — write the event to an outbox table inside the order's
transaction, then a relay tails it and publishes. The event becomes as durable as
the state change because it *is* the state change. I scoped it out for a portfolio
project, but that's exactly where I'd take it if these were payments."

**Gotcha:** "just publish inside the transaction" is *strictly worse*, not a fix —
rollback then leaves Kafka with a permanent record of an assignment that never
happened. Neither pre- nor post-commit is correct for two independent systems;
that's the whole reason the outbox pattern exists. Anyone who thinks reordering the
two lines solves it hasn't seen the problem.

**Honest scope:** the `UNKNOWN_TOPIC_OR_PART` death was partly amplified by an
earlier `down -v` that destroyed the topic. In a steady-state outage (topic already
durable in the volume) the buffered event more likely self-heals on reconnect. The
precise, defensible claim is narrower and stronger: *a dual write has no atomicity,
so a failure window exists where Postgres commits and the event doesn't, and no
client-side retry closes it.* That window is real and measured.

---

## 61. Self-Test — Day 31 (answer out loud)
1. Why can a Kafka address pass a raw TCP connection test and still be the wrong
   one to use?
2. Why is the Producer a process-lifetime singleton and not a per-request object?
   Name the silent failure of getting it wrong.
3. Idempotence is ON. You call `produce()` four times with the same payload. How
   many rows land, and why isn't that a bug in idempotence?
4. Name the two distinct channels for `produce()` errors vs delivery errors. Which
   one does a dead broker use?
5. Why can a producer never synchronously return "delivered = true"?
6. What does `poll(0)` actually do, and what two things break if you never call it?
7. `flush()` on shutdown covers which failures and not which others? Name the
   signal boundary.
8. Same key produced by a Python and a Java client lands on different partitions.
   Why, and what's the one-line fix?
9. Why is `NUM_PARTITIONS 3→4` a silent, irreversible ordering break?
10. Why must the dispatch publish be post-commit — and why is pre-commit *worse*,
    not merely different?
11. You dispatched with the broker down and got a 200. Where did the event go, and
    what does Postgres believe happened?
12. What is the transactional outbox, and precisely which failure does it close
    that post-commit publishing cannot?

*Shaky on any? #3, #5, #10, #12 are the ones that separate "used Kafka" from
"understands Kafka."*

---

## 62. Environment Split-Brain (Two Postgres, One `.env`) ⭐

**Concept (why).** Dev ran hybrid: host-native Postgres on 5432 AND a Compose
Postgres remapped to 5433 (the remap dodged a port-bind conflict). `.env` still
pointed at 5432, so pytest + host app wrote to the native DB while the `api`
container wrote to Compose. Two fully-migrated schemas, diverging silently
(3 orders vs 2). No error ever fired — which is what made it dangerous. A change
verified on one side was invisibly stale on the other.

**Soundbite (~30s).** "I had a split-brain across two Postgres instances — host
and containerized — because my env config and my compose file disagreed on the
port. Nothing errored; the databases just quietly forked. The fix wasn't cleaning
data, it was eliminating the redundant instance: I decommissioned the native
Postgres, made Compose canonical, and repointed every hardcoded connection
string. `docker compose down -v` is now my reset button."

**Gotcha.** The tell was a sequence reset that "didn't take" — `RESTART WITH 4`
on one DB, then reading `3267` back. It took fine; I was reading a different
database than I wrote to. A sequence/value that won't change after you set it is a
classic signature of a read/write split across two backends. Also: env-driven
config (`alembic/env.py` reads `DATABASE_URL`) can silently override a hardcoded
`alembic.ini` — a stale ini value is a dormant landmine, not dead code.

**Self-test.**
- Q1: You `UPDATE` a row, commit, re-`SELECT`, and see the old value. Two
  explanations — which is the environment one?  (A: uncommitted txn / wrong
  isolation, *or* you're connected to a different DB than you wrote to.)
- Q2: Why does `docker-compose.yml` correctly use `@db:5432` internally while
  `.env` needs `@localhost:5433`?  (Container-network service name + internal
  port vs host-published remap.)
- Q3: The report guessed Redis was also forked. It wasn't. What one command
  settles "how many Redis are actually running?" before you theorize?
  (`ss -tlnp | grep 6379` — one docker-proxy = one Redis.)

---

## §63 — Reproducible-From-Empty: One-Shot Init Jobs & Real Readiness Gates

**Concept (why).** A `docker compose down -v` wipes all data volumes. "Clean and
ready" is only true if EVERY required setup artifact is rebuilt by code on the
next `up`, not by remembered manual commands. Three artifacts needed rebuilding:
Postgres schema, the isolated pytest database, and the Kafka topic. Two were
manual (tribal knowledge — the thing that rots). Fix: make each reproducible.
  - Schema → one-shot `migrate` job (`alembic upgrade head`), gated on db healthy.
  - Test DB → Postgres init-script in `/docker-entrypoint-initdb.d/`, which runs
    ONCE on a fresh data dir — exactly the down -v → up case.
  - Topic → one-shot `kafka-init` job (`kafka-topics --create --if-not-exists
    --partitions 3`), gated on kafka HEALTHY.

**Soundbite (~30s).** "The whole stack reproduces from an empty volume with one
command. Schema via a one-shot Alembic job, the pytest database via a Postgres
init-script, Kafka topics with pinned partition counts via a one-shot admin job —
all ordered by health-gated depends_on. Clone and `docker compose up`; no setup
steps, no README dance. Making the environment declarative is what lets me trust
`down -v` as a real reset button."

**Gotcha 1 — `service_started` ≠ ready.** `depends_on: condition: service_started`
only means the container process launched. A dependent that does real I/O on boot
(kafka-init creating a topic) will race a broker that isn't accepting connections
yet and fail intermittently. Fix: give the dependency a healthcheck that does a
real round-trip (`kafka-topics --list`) and gate on `service_healthy`. Lazy
clients (the producer) hide this; eager ones expose it.

**Gotcha 2 — init-scripts run ONCE.** Files in `/docker-entrypoint-initdb.d/` run
only when the data directory is empty. A warm restart (`down` without `-v`) skips
them — correct, because the DB already exists — but it means you can't use them to
apply ongoing changes. They're for first-init bootstrap only; schema *changes*
belong in migrations.

**Gotcha 3 — idempotent one-shots.** `--if-not-exists` (topic) and `alembic
upgrade head` (schema) are safe to re-run on every `up`. A one-shot that errors on
"already exists" breaks warm starts. Make boot jobs idempotent or gate them on
first-init only.

**Self-test.**
- Q1: After `down -v && up`, schema and topic come back but pytest fails "database
  does not exist." Why does schema auto-restore and the test DB not?  (migrate job
  targets deliveriq_db only; test DB had no code responsible for it until the
  init-script.)
- Q2: `kafka-init` fails ~1 in 5 runs with connection refused, passes on retry.
  Root cause and fix?  (Gated on service_started not service_healthy → races
  broker readiness; add broker healthcheck, gate on service_healthy.)
- Q3: Why put test-DB creation in an init-script but schema in a migration —
  why not both in init-scripts?  (Init-scripts run once on fresh volume only;
  schema evolves, must replay on every environment → migrations. DB existence is
  a one-time bootstrap → init-script.)
---

---
---
---
---
