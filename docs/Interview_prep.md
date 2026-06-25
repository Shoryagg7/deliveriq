# DeliverIQ — Interview Prep & Concept Guide

> A self-study reference for everything built so far. Each topic has: **the concept (why)**,
> the **interview soundbite** (how to say it out loud), and the **gotcha** (what trips people up).
> If you can explain every soundbite without looking, you own the material.

---

## 1. REST & HTTP Basics

### Status codes — what they signal
- `200 OK` — success, here's the data
- `201 Created` — success, a new resource was created (use for POST that creates)
- `404 Not Found` — the resource doesn't exist
- `422 Unprocessable Entity` — input failed validation (wrong type, missing field, constraint broken)

**Soundbite:** "Status codes are the contract — a client decides success vs failure from the code, not the body. A missing resource is `404`, not a `200` with an error message inside."

**Gotcha:** returning `200` with `{"error": "not found"}` is wrong — the client can't tell it failed. Use the right code.

### Path vs Query parameters
- **Path param** (`/orders/3`) → identity. *Which* resource. Required.
- **Query param** (`/orders?status=PENDING`) → filter/options. Usually optional.

**Soundbite:** "Path = identity, query = filter. FastAPI decides by name: if the param name appears in the route path inside `{}`, it's a path param; otherwise it's a query param."

**Gotcha:** an optional filter like `status` should be a query param, not `/orders/{status}` — putting it in the path makes it required and reads as identity.

---

## 2. Validation (FastAPI + Pydantic)

### The core principle
FastAPI validates against **the exact type you declare — no more.**
- `str` accepts *any* string → loose gate, almost nothing rejected.
- `int`, `Enum`, or a Pydantic model with constraints → tight gate.

**Soundbite:** "Validation isn't magic — it enforces the declared contract. A loose type is a loose gate. I tighten inputs by typing them specifically: `int`, an `Enum`, or `Field(gt=0)`."

### Declarative validation vs runtime checks — "type it if you can, raise it if you must"
- **Type it (declarative):** "Is the input the right *shape*?" — knowable from input alone → use a type/Enum/Pydantic. Auto `422` at the boundary.
- **Raise it (`HTTPException`):** "Input is valid, but does it make sense against the *data/state*?" — only knowable at runtime → check and raise.

**Example:** `status` must be one of {PENDING, DELIVERED} → *static known set* → **Enum**.
`order_id=3` exists? → *dynamic, depends on the database* → **runtime check + 404**.

**Soundbite:** "Static, known-at-code-time sets become types. Data-dependent truths (does this row exist?) must be runtime checks that raise. Both look like `x not in collection`, but one the type system can express and the other it can't."

### Pydantic models
- **Request model** (`OrderCreate`) = input contract — what you accept.
- **Response model** (`OrderResponse`) = output contract — what you expose.
- `response_model` **filters output**: any field not declared is stripped — so internal fields can't leak. (Security boundary, not just docs.)
- `Field(gt=0, description=...)` adds constraints + Swagger docs.
- Pydantic **coerces when it can** (`"250"` → `250.0`), **rejects when it can't** (`"abc"` → 422).

**Gotcha:** to return a SQLAlchemy object through a response model, the schema needs
`model_config = ConfigDict(from_attributes=True)` (Pydantic v2; was `orm_mode = True` in v1).

### Two kinds of "model" — don't confuse them
| | Pydantic model | SQLAlchemy model |
|---|---|---|
| Lives in | `app/schemas/` | `app/models/` |
| Job | shape of API data (validate JSON) | shape of a DB table |
| Guards | the API door | the storage shelf |

Having both for orders is **correct**, not redundant — different layers.

### The error envelope
`422` responses look like: `{"detail":[{"type","loc","msg","input"}]}`.
`loc` tells you *where* it failed — `["body","value"]`, `["query","status"]`, `["path","order_id"]`.

---

## 3. Databases & Persistence

### In-memory vs on-disk
A Python dict lives in the process's **RAM** → killed on restart (counter resets, data gone).
PostgreSQL writes to **disk** → survives restarts, crashes, redeploys.

**Soundbite:** "In-memory state dies with the process. A database persists to disk, so it's the durable source of truth even as the app restarts or scales to multiple instances."

### Client / server model
The database is a **separate server process** (port `5432`). Your app, `psql`, and DBeaver are all **clients** talking to it.

**Soundbite:** "Postgres runs as its own server; my app is just one client connecting over a socket. That separation is what gives persistence, concurrency, and one shared source of truth."

### Primary key / auto-increment
`id` is a `SERIAL` (auto-incrementing sequence) — the DB generates it, and the counter **also persists** (next insert is 4, not 1, after a restart).

---

## 4. SQLAlchemy / ORM

### What an ORM is
Object-Relational Mapper = a **translator**. You write Python classes; it generates SQL.
- `engine` — the connection manager to the DB (lazy; connects when needed).
- `Session` — one conversation/transaction with the DB.
- `Base` — the registry; every model inheriting from it is tracked.

**Soundbite:** "SQLAlchemy maps a Python class to a table. I write objects, it writes the SQL. `engine` is the connection, a `session` is one transaction, `Base` is the registry of all my tables."

### create_all + THE classic trap
`Base.metadata.create_all(bind=engine)` creates all registered tables that don't exist yet.

**Gotcha:** a model only registers on `Base` when its file is **imported**. If you don't `import` the model before `create_all`, the table silently isn't created. (`from app.models.order import Order` is doing work just by running.)

### Column options
- `primary_key=True` → unique row id, DB auto-generates it.
- `index=True` → builds a B-tree index → O(log n) lookups (vs O(n) scan).
- `nullable=False` → required at the DB level (second layer beyond Pydantic).
- `default=...` → auto-filled if not provided (e.g. `status="PENDING"`).

### CRUD operations
- **Create:** `db.add(obj)` → `db.commit()` (runs the INSERT) → `db.refresh(obj)` (reloads DB-generated fields like `id`, `created_at`).
- **Read one:** `db.query(Order).filter(Order.id == x).first()` → row or `None`.
- **Read many:** `db.query(Order).all()` (optionally `.filter(...)` first).

**Gotcha:** without `db.refresh()`, `obj.id` is still `None` right after commit.

### Dependency Injection (`Depends(get_db)`)
`db: Session = Depends(get_db)` → FastAPI runs `get_db` before the endpoint, hands in a fresh session, and closes it after (the `try/finally`). Every request gets its own short-lived, auto-closed session.

**Soundbite:** "Each request gets its own DB session via dependency injection — opened before the handler, closed after, automatically. No leaked connections."

---

## 5. Project Structure

```
app/
├── core/        # database.py: engine, SessionLocal, Base, get_db
├── models/      # SQLAlchemy models (DB tables)
├── schemas/     # Pydantic models (API in/out)
├── routers/     # APIRouter modules (grouped endpoints)
└── main.py      # create_all + FastAPI app + include_router
```

**APIRouter:** `APIRouter(prefix="/orders", tags=["orders"])` groups related routes in their own file; `app.include_router(...)` plugs them in. Keeps `main.py` thin.

---

## 6. DeliverIQ — Project Talking Points

### The differentiator: fairness-banded dispatch
Instead of naive nearest-rider, among riders within a distance band Δ of the nearest, assign the one with the **fewest orders today**.

- **"How is it different from Swiggy/Zomato?"** → "Theirs optimizes pure ETA. Mine adds a bounded fairness constraint — greedy-nearest reframed as a constrained assignment problem."
- **"What problem does it solve?"** → "Naive nearest-rider starves some riders and overloads others. Banding spreads earnings while Δ guarantees delivery SLA isn't sacrificed."
- **"Social impact?"** → "Fairer earnings for gig riders — an honest angle, no fabrication."
- **"Why a band, not a weighted score?"** → "A blended `α·dist + β·fairness` can silently send a far rider (cold food). The band makes the SLA guarantee explicit and tunable."

### DSA core (steer interviews here)
- **Priority queue** dispatch — O(log n) ordering.
- **Geohash** rider matching — O(1) grid-cell lookup vs O(n) scan.
- These are the same nearest-neighbour shape as the FAISS work in SemanticCache.

### Honest framing
"It's a pattern-aware portfolio project where I went deep on the engineering and trade-offs — not production experience. I can speak to every design decision and what I'd change at scale."

---

## 7. Quick-Fire Self-Test (answer out loud, no notes)

1. When do you return `201` vs `200` vs `404` vs `422`?
2. Path param vs query param — how does FastAPI decide which is which?
3. Why does `status="banana"` give `422` with an Enum but `200 []` with a plain `str`?
4. "Type it if you can, raise it if you must" — explain with `status` vs `order_id`.
5. What does `response_model` do to fields you return but didn't declare?
6. What's the difference between a Pydantic model and a SQLAlchemy model?
7. Why does in-memory data reset on restart but the DB doesn't?
8. What are `engine`, `session`, and `Base`?
9. Why must you `import` a model before `create_all`?
10. Walk through `add` → `commit` → `refresh`. What breaks if you skip `refresh`?
11. What does `Depends(get_db)` give each request, and what closes the session?
12. Explain fairness-banded dispatch and why it's a constrained assignment problem.
13. Why can't you keep using `create_all` in production?
14. What's the `env.py` import trap, and what bad thing happens if you hit it?
15. Why review an autogenerated migration before applying it?
16. What does the `alembic_version` table store?
17. `default=` vs `nullable=False` — what's the difference?

*If any answer is shaky, that's your next review target.*

---

## 8. Tech Stack — Why These, and the Alternatives

> Interviewers ask "why did you choose X?" to check whether you **decided** or just
> copied a tutorial. The strong answer always names the **trade-off** and a credible
> alternative. Honest framing: part of the reason is fit, part is that these are the
> industry-standard tools my target companies (Uber, Razorpay, PhonePe) actually use.

### Python
- **Why:** fast to build, huge ecosystem, and it spans backend *and* AI/ML (matters for SemanticCache). The bottleneck in this app is I/O (DB, network), not CPU, so raw language speed isn't the constraint.
- **Alternatives:** **Go** (compiled, excellent concurrency — Uber uses it heavily; faster but more verbose, weaker ML ecosystem). **Java/Spring** (enterprise-standard, very mature, but heavy boilerplate). **Node.js** (also great at I/O; Python won for the AI side).
- **Soundbite:** "I/O-bound service, so developer speed beat raw speed. Go would be faster but I wanted Python's ecosystem and the ML overlap with my second project."

### FastAPI (web framework)
- **Why:** async-first (handles many concurrent I/O requests), validation built in via Pydantic, and **auto-generated OpenAPI/Swagger docs**. Minimal boilerplate, type-hint driven.
- **Alternatives:** **Flask** (simpler but you bolt on validation/docs/async yourself). **Django + DRF** (batteries-included with ORM/admin/auth, but heavy and opinionated — overkill for a focused API, less async-native).
- **Soundbite:** "FastAPI gives me async, validation, and live docs out of the box. Flask is lighter but I'd rebuild those; Django is heavier than an API-first service needs."

### PostgreSQL (database)
- **Why:** ACID-compliant relational DB — orders and riders have clear relationships and I can't afford to lose an order. Rich SQL (window functions, indexes), great JSON support, and **PostGIS** for geospatial (relevant to a location-based dispatch system).
- **Alternatives:** **MySQL** (also solid; Postgres wins on window functions, JSON, geospatial, stricter SQL). **MongoDB** (flexible schema, but my data is relational and needs consistency — NoSQL fits unstructured, denormalized, massive-scale data). **SQLite** (great for dev, not concurrent production load).
- **Soundbite:** "Structured, related data that needs consistency → relational + ACID. Postgres over MySQL for window functions and geospatial; over Mongo because losing an order isn't acceptable."

### SQLAlchemy (ORM)
- **Why:** most mature Python ORM, pairs cleanly with FastAPI, lets me write Python but drop to raw SQL when needed, and is database-agnostic.
- **Alternatives:** **Raw SQL via psycopg2** (max control/performance, more boilerplate, injection risk if careless). **SQLModel** (newer, merges Pydantic + SQLAlchemy — promising but less battle-tested). **Tortoise ORM** (async-native).
- **Trade-off to acknowledge:** ORMs add abstraction and can generate inefficient queries (the N+1 problem) — you trade some control for productivity.

### Pydantic (validation)
- **Why:** comes with FastAPI; declarative validation + serialization from type hints, with structured error output.
- **Alternatives:** **marshmallow** (older, more manual), or hand-rolled validation. Pydantic is the modern standard.

### Redis (caching, rate limiting, rider state) — *upcoming*
- **Why:** in-memory key-value store, sub-millisecond, perfect for hot ephemeral state: rate-limit counters, rider locations, `orders_today`. Has TTLs, pub/sub, and rich structures (sorted sets, native geo commands, hashes).
- **Alternatives:** **Memcached** (simpler cache, but no rich structures/persistence/pub-sub). **In-process memory** (doesn't work across multiple app instances — Redis is shared state).
- **Soundbite:** "I need fast, shared, ephemeral state across app instances. Redis over Memcached for sorted sets and geo; over in-memory because that doesn't survive scaling horizontally."

### Kafka (event streaming) — *upcoming*
- **Why:** durable, high-throughput, replayable event log. Decouples producers from consumers — one order event fans out to notification, analytics, and audit as independent consumer groups reading the same log.
- **Alternatives:** **RabbitMQ** (great task queue with smart routing/acks, but Kafka is better for high-throughput streaming, replay, and many independent consumers of the same stream). **Redis Pub/Sub** (simple but not durable — messages vanish with no subscriber). **AWS SQS/SNS** (managed, but ties you to AWS).
- **Soundbite:** "I want a durable, replayable log many consumers read independently — that's Kafka's model. RabbitMQ is a queue, not a log; Redis pub/sub isn't durable."

### Docker (containerization) — *upcoming*
- **Why:** reproducible environment ("works on my machine" → works everywhere), easy multi-service local setup with Compose (app + Postgres + Redis + Kafka), simple deploys.
- **Alternatives:** bare-metal/venv only (not reproducible across machines), **Podman** (Docker-compatible). Docker is the de facto standard.

### Prometheus + Grafana (observability) — *upcoming*
- **Why:** Prometheus scrapes metrics (pull model), Grafana visualizes them. The standard open-source combo.
- **Alternatives:** **Datadog / New Relic** (managed SaaS, paid), **ELK** (more for logs than metrics).

### The honest meta-answer
"Some of these (Kafka, Prometheus) are more than a small project strictly needs. I added them deliberately to learn the production patterns my target companies use, and I can defend each one's trade-off rather than just listing it."

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
