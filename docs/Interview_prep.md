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
