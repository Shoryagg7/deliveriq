# DeliverIQ — Interview Prep

> **One file.** What I built, why I built it that way, how it actually works,
> and where it breaks. It replaces the three docs that used to live here
> (`Interview_prep.md`, `PLAN.md`, `Backend_Interview_Zero_to_Master.md`) —
> the build plan is history now that the project is done, and the general
> backend theory only earns its place where the project demonstrates it.

> **Companion file:** [`INTERVIEW_NOTES.md`](./INTERVIEW_NOTES.md) — a refined,
> beginner-level pass over the resume skills (what each is, why it was chosen,
> what was rejected) plus deep dives on **Redis rate-limiting algorithms** and
> **Kafka partitions / consumer groups / delivery semantics**, which is where
> follow-up questions have actually gone. Read that one the night before; read
> this one to build the depth behind it.

## How to use this

Every section runs in the same order, because that is the order an interview
runs in:

**Concept (the basics)** → **What DeliverIQ does (the why)** → **How it works
(the depth)** → **Soundbite** (say it out loud, ~20–30 s) → **Gotcha** (the
follow-up that separates "used it" from "understands it").

Read top-to-bottom once. After that, use the ladder: a question starts at the
basics level of a section and the interviewer walks down it. If you can hold
the soundbite *and* the gotcha for a section, you own that rung.

**The ladder, section by section**

```
 0  Pitch            what the system is, and the one design choice that's mine
 1  Foundations      backend, HTTP, REST, validation          (junior floor)
 2  Persistence      SQL, ORM, migrations, indexes            (junior → mid)
 3  Fast layer       Redis, rate limiting, cache consistency  (mid)
 4  Algorithms       heap+aging, geohash+band, state machine  (the DSA hook)
 5  Concurrency      ACID, isolation, SKIP LOCKED, liveness   (mid → senior)
 6  Events           Kafka, delivery semantics, DLQ, outbox   (senior)
 7  Production       auth, idempotency, observability, CI     (senior)
 8  Scaling up       system design, sharding, CAP, saga       (staff signal)
 9  The audit        what I found in my own code, and fixed  (credibility)
```

**Governing rule:** the gaps in §9 are **volunteered, never hidden**. A
self-reported flaw reads as engineering judgement; the same flaw extracted by
an interviewer reads as either not knowing or not saying.

---
---

# 0 — The pitch

## 0.1 The opener (deliver in one breath, under 20 s)

> "I built a distributed order-dispatch service where three stateless API
> replicas contend for shared state. The interesting parts were concurrency
> correctness — a double-dispatch race I fixed with row-level locking using
> `SELECT … FOR UPDATE SKIP LOCKED` — and the consistency gap between my
> database and my event log, which is the dual-write problem."

Why this opener works: it names a **race** and a **known named problem** in the
first fifteen seconds, and hands the interviewer two threads to pull. The
food-delivery framing is the domain; distributed systems is the subject.

The softer, product-first version when the room isn't systems-flavoured:

> "A production-grade REST API that dispatches food-delivery orders to riders
> using priority queues, geohashing, rate limiting and event streaming —
> FastAPI, Postgres, Redis, Kafka, Docker."

## 0.2 The differentiator — fairness-banded dispatch

Instead of naive nearest-rider: among riders within a distance band Δ of the
**nearest** candidate, assign the one with the **fewest orders today**.

- **"How is this different from Swiggy/Zomato?"** → "Theirs optimizes pure ETA.
  Mine adds a bounded fairness constraint — greedy-nearest reframed as a
  constrained assignment problem."
- **"What problem does it solve?"** → "Naive nearest starves some riders and
  overloads others. The band spreads earnings while Δ keeps the delivery SLA."
- **"Social impact?"** → "Fairer earnings for gig riders — honest, no
  fabrication."

## 0.3 Honest framing (use it early, once)

> "It's a portfolio project where I went deep on the engineering and the
> trade-offs — not production experience. I can defend every design decision and
> tell you what I'd change at scale."

## 0.4 The stack, and the alternative I rejected

Interviewers ask "why X?" to check whether you **decided** or copied a tutorial.
The strong answer always names the trade-off and a credible alternative.

| Choice | Why | Alternative rejected |
|---|---|---|
| **Python** | I/O-bound service; developer speed beats raw speed | Go (faster, more verbose); Java/Spring (heavy) |
| **FastAPI** | async-first, Pydantic validation, free OpenAPI docs | Flask (rebuild validation/docs); Django+DRF (heavy for API-only) |
| **PostgreSQL** | ACID; orders are relational and can't be lost | MySQL (weaker window fns/geo); Mongo (consistency); SQLite (no concurrency) |
| **SQLAlchemy** | mature, drops to raw SQL when needed | raw psycopg2 (boilerplate); SQLModel (less battle-tested) |
| **Redis** | shared sub-ms ephemeral state across replicas | Memcached (no sets/geo); in-process memory (dies at N instances) |
| **Kafka** | durable replayable log, many independent consumers | RabbitMQ (queue, not log, no replay); Redis Pub/Sub (not durable) |
| **Docker Compose** | environment as code, one-command stack | bare venv (not reproducible) |
| **Prometheus + Grafana** | pull-based metrics, dashboard provisioned from repo | Datadog/New Relic (paid SaaS) |

**The honest meta-answer:** "Some of these — Kafka, Prometheus — are more than a
project this size strictly needs. I added them deliberately to learn the
production patterns, and I can defend each one's trade-off rather than list it."

## 0.5 What I built → what it demonstrates

| Built | Demonstrates | Section |
|---|---|---|
| Token-bucket limiter, atomic Lua | atomicity, read-modify-write races, distributed counters | §3.2–3.3 |
| heapq dispatch + aging | scheduling, starvation, priority queues | §4.1 |
| Geohash + haversine + fairness band | spatial indexing, constrained assignment | §4.2–4.3 |
| Order state machine | state modelling, error semantics (400 vs 500) | §4.4 |
| Postgres ↔ Redis dual write | cache consistency, reconciliation | §3.4 |
| `FOR UPDATE SKIP LOCKED` two-phase claim | lost updates, pessimistic locking, multi-instance | §5.3–5.5 |
| Commit-then-publish + DLQ | delivery semantics, phantom events, outbox | §6.6–6.9 |
| JWT + role/ownership authz | authn vs authz, actor-vs-edge guards | §7.1 |
| Idempotency-Key middleware | retry safety, ambiguous timeouts | §7.2 |
| Structured logs, RED metrics, /ready | observability, cardinality, liveness vs readiness | §7.4–7.5 |
| Compose, one-shot jobs, CI | environment as code, readiness gating | §7.6–7.8 |

---
---

# 1 — Foundations

## 1.1 What a backend actually is

**Concept.** The frontend runs on the user's device. The backend runs on a
machine you control and holds the truth: the data, the rules, the secrets. The
client is **enemy territory** — anyone can modify it and send anything.

```
  USER'S DEVICE                     YOUR SERVER(S)
 ┌─────────────┐   HTTP request   ┌─────────────┐     SQL      ┌──────────┐
 │  Browser /  │ ───────────────► │   Backend   │ ───────────► │ Database │
 │ Mobile app  │ ◄─────────────── │  (FastAPI)  │ ◄─────────── │(Postgres)│
 └─────────────┘   HTTP response  └─────────────┘    rows      └──────────┘
   renders UI         (JSON)       business logic            durable truth
```

**Soundbite:** "The backend is the trust boundary. Clients can lie — the server
validates, authorizes and owns the data. That's why business rules live
server-side even when the UI also checks them."

**Gotcha:** UI validation is UX, not security. Every frontend check must be
repeated server-side, because an attacker curls the API directly.

## 1.2 What happens when you type a URL

```
 1. DNS         api.deliveriq.com → 203.0.113.7   (cached at every layer)
 2. TCP         SYN → SYN-ACK → ACK               (reliable ordered pipe)
 3. TLS         key exchange + certificate        (the S in HTTPS)
 4. HTTP        GET /orders/3 + headers
 5. LB          picks one healthy instance
 6. App         middleware → router → handler → service
 7. DB          SELECT … WHERE id = 3             (index lookup)
 8. Response    200 + JSON back up the chain
```

**Soundbite:** "DNS resolves, TCP connects, TLS encrypts, HTTP carries. Server
side it's load balancer → app instance → database → serialized JSON. Every one
of those steps has a cache and a failure mode — that's the whole backend
syllabus in one question."

**Gotcha:** TCP guarantees *delivery and order*, not speed — that's what the
handshake buys. UDP skips it: fire-and-forget datagrams for video, DNS, gaming.

## 1.3 HTTP on the wire, and why statelessness matters

```
REQUEST                                RESPONSE
POST /orders HTTP/1.1                  HTTP/1.1 201 Created
Host: api.deliveriq.com                Content-Type: application/json
Content-Type: application/json         X-Request-ID: 7f3a-…
Authorization: Bearer eyJhb…           X-RateLimit-Remaining: 98
Idempotency-Key: 9c1e-…
{"customer_id":1,"value":250.0}        {"id":42,"status":"PENDING"}
```

**HTTP is stateless:** each request stands alone. Any continuity — who's logged
in — must ride on every request, in a cookie or an `Authorization` header. That
one property is why horizontal scaling works at all: no request depends on a
particular instance's memory, so any instance can serve any request.

**Soundbite:** "Statelessness is the feature, not a limitation. Because no
request depends on server memory of the last one, any replica can serve any
request — which is exactly what let me run `--scale api=3`."

## 1.4 Status codes — the contract

```
                       Did the request succeed?
                        │yes              │no
            created something?        whose fault?
            │yes        │no        │client        │server → 500
           201         200         │                (bug, impossible state)
                            malformed shape? ─yes→ 422
                                   │no
                            resource missing? ─yes→ 404
                                   │no
                            auth problem? ─yes→ 401 (who are you?)
                                   │no          403 (you can't)
                            conflicts with state? ─yes→ 409 / 429
                                   │no → 400 (illegal transition)
```

**What DeliverIQ returns, and why:**

| Code | Where | Reason |
|---|---|---|
| `201` | `POST /orders` | created a resource |
| `400` | illegal status transition | well-formed but illegal *given state* |
| `401` | missing/invalid JWT | not authenticated |
| `403` | customer touching status | authenticated, not permitted |
| `404` | `NoPendingOrders`, missing order | the resource isn't there |
| `409` | `RiderUnavailable`, idempotency in flight | conflicts with current state |
| `422` | Pydantic validation | input doesn't match the declared shape |
| `429` | token bucket empty | rate limited |
| `503` | `/ready` with a dead dependency | can't serve traffic right now |

**400 vs 422 — the distinction that gets asked.** 422 is *malformed*: the input
doesn't match the declared shape, and Pydantic raises it automatically at the
boundary (`status="banana"` against an Enum). 400 is *well-formed but illegal*:
a valid-looking status that is an illegal **transition** — and **I** raise it at
runtime.

**Soundbite:** "422 is the type system rejecting a malformed request
automatically; 400 is my own runtime check rejecting a well-formed but
state-illegal one. Same family, different cause, different layer — type it if
you can, raise it if you must."

**409 vs 404 for "no rider":** orders exist and riders exist — they're all BUSY.
That's a conflict with current state, not a missing resource.

## 1.5 Verbs, safety, idempotency

| Verb | Safe? | Idempotent? | Use |
|---|---|---|---|
| GET | ✅ | ✅ | read |
| POST | ❌ | ❌ | create / side-effecting action |
| PUT | ❌ | ✅ | full replace |
| PATCH | ❌ | ❌ | partial update |
| DELETE | ❌ | ✅ | remove |

**Idempotent** = N calls leave the same end state as one. It matters because
**networks retry**, and a timeout is ambiguous — you cannot tell whether the
request landed. That ambiguity is the entire reason for idempotency keys (§7.2).

**In DeliverIQ:** `POST /orders/dispatch` is POST despite creating nothing — it
has side effects (assigns a rider, flips statuses, bumps counters), and side
effects cannot sit behind a GET. Location and status updates are PATCH: partial
edits, not full replacements.

**Gotcha:** putting a mutation behind GET is the classic violation — a crawler
or a retry fires it silently. Safe/idempotent is a contract, not a suggestion.

**Path vs query:** path = identity (`/orders/3`), query = filter
(`/orders?status=PENDING`). Putting an optional filter in the path makes it
required and reads as identity.

## 1.6 Validation — type it if you can, raise it if you must

**Concept.** FastAPI validates against **the exact type you declare — no more**.
`str` accepts any string: a loose gate. `int`, an `Enum`, `Field(gt=0)`: a tight
one.

The rule for which mechanism to use:

- **Type it (declarative)** — "is the input the right *shape*?" Knowable from
  the input alone → Enum / Pydantic model / constraint. Automatic 422.
- **Raise it (runtime)** — "the input is valid, but does it make sense against
  the *data*?" Only knowable at runtime → check and raise.

`status ∈ {PENDING, …}` is a static known set → **Enum**. `order_id=3` exists? →
depends on the DB → **runtime check + 404**. Is this transition legal? → depends
on current state → **runtime check + 400**.

**Soundbite:** "Static, known-at-code-time sets become types. Data-dependent
truths — does this row exist, is this transition legal — must be runtime checks.
Both look like `x not in collection`, but one the type system can express and
the other it can't."

**Two kinds of model, both correct to have:**

| | Pydantic model (`app/schemas`) | SQLAlchemy model (`app/models`) |
|---|---|---|
| Job | shape of API data | shape of a DB table |
| Guards | the API door | the storage shelf |

`response_model` **filters output** — any field not declared is stripped, so
internal fields can't leak. That's a security boundary, not just documentation.

**Gotcha:** `OrderStatus` lives in exactly one file (`app/core/enums.py`). Two
definitions drift silently — and two enum classes compare unequal even when
their values match.

## 1.7 Project structure — why these folders

```
app/
  core/        config · database · redis · security · enums · exceptions · metrics · kafka producer
  middleware/  request_id · rate limit · idempotency · metrics
  models/      SQLAlchemy models (tables)
  schemas/     Pydantic models (API in/out)
  routers/     orders · riders · auth · admin
  services/    dispatch · geohash matching · order state machine
  workers/     shared consumer runner + notification/analytics/audit
```

**`core` = infrastructure glue; `services` = business logic.** That's why
`dispatch.py` is a service, not core. Routers say *what endpoints exist*,
schemas say *what shape data has*, services say *how the logic works*, models
say *what is stored*.

## 1.8 Level check — §1

1. Why must every frontend validation be repeated on the backend?
2. Six steps of the URL journey; a failure mode at each.
3. TCP vs UDP in one sentence each.
4. 400 vs 422 — which does FastAPI raise for you, and why?
5. Why is `/orders/dispatch` a POST? Why is location update PATCH?
6. "Type it if you can, raise it if you must" — apply it to `status`,
   `order_id`, and a *transition*.
7. What does `response_model` do to an undeclared field you return?

---
---

# 2 — Persistence

## 2.1 Tables, keys, joins (the floor)

- **Primary key** — uniquely identifies a row (`orders.id`, a `SERIAL`; the
  sequence persists across restarts, and gaps are intentional so old references
  never silently re-point).
- **Foreign key** — holds another table's PK; the relationship, enforced by the
  DB (`orders.rider_id → riders.id`).

```
 orders                              riders
 ┌────┬───────┬────────┬──────────┐  ┌────┬──────┬───────────┐
 │ id │ value │ status │ rider_id │  │ id │ name │ status    │
 │ 1  │ 250.0 │ ASSIGN │    2 ────┼──┼► 2 │ Asha │ BUSY      │
 │ 2  │ 800.0 │PENDING │   NULL   │  │ 3  │ Ravi │ AVAILABLE │
 └────┴───────┴────────┴──────────┘  └────┴──────┴───────────┘

 INNER JOIN drops order 2 (no match); LEFT JOIN keeps it with name = NULL.
```

**Gotcha:** `WHERE` filters rows *before* grouping, `HAVING` filters groups
*after*. `COUNT(col)` skips NULLs; `COUNT(*)` doesn't.

**Where DeliverIQ uses this:** `GET /admin/stats` computes counts in the
**database** — `func.count`, `func.avg`, `group_by` — not by pulling every row
into Python and looping.

**Gotcha:** `func.avg` returns `None` on an empty table (not 0) — guard it or
the response carries `null`. And `group_by(status)` returns only statuses that
*exist*; a status with zero rows is absent, not present with 0.

## 2.2 The ORM, and the trap in it

`engine` = the connection manager. `Session` = one conversation, and one
**transaction**. `Base` = the registry of models.

**Create → commit → refresh.** `db.add(obj)` stages, `db.commit()` runs the
INSERT, `db.refresh(obj)` reloads DB-generated fields (`id`, `created_at`).
Skip `refresh` and `obj.id` is still `None` — which breaks anything downstream
that needs it, e.g. indexing a new rider into Redis.

**Dependency injection:** `db: Session = Depends(get_db)` gives every request
its own short-lived session, closed automatically in a `finally`. No leaked
connections — and it's the seam that lets tests swap the database (§7.7).

**Gotcha (the ORM tax):** ORMs can generate inefficient queries. The canonical
one is **N+1** — fetch 100 orders, touch `order.rider.name` in a loop, and the
ORM lazily fires one query per order: 101 round-trips. Fix with eager loading
(`selectinload` / `joinedload`) or a JOIN. You spot it in query logs.

**Soundbite:** "N+1 is the ORM lazily loading a relationship inside a loop. It's
the canonical case of an abstraction hiding a cost you still have to
understand."

## 2.3 Migrations — why `create_all` is not production

**Concept.** `Base.metadata.create_all()` **only creates missing tables — it
never alters an existing one.** Add a column and it does nothing, so code and
schema drift apart and crash. Migrations are versioned, incremental, reversible
scripts describing schema *changes*. Git for your schema. Alembic is the tool.

**Workflow:** configure `env.py` (import `Base` *and every model*) →
`alembic revision --autogenerate` → **review the generated upgrade/downgrade** →
`alembic upgrade head`, which stamps the current revision into
`alembic_version`.

**Soundbite:** "Production never uses `create_all` — it can't alter existing
tables. Alembic gives me versioned, reversible schema changes that keep every
environment in sync."

**Gotcha — the import trap:** `env.py` must import the **model classes**, not
just `Base`. A model only lands in `Base.metadata` when imported. Miss it and
autogenerate believes there are no tables — and generates `DROP` statements for
your real ones.

**Gotcha:** `default=` ≠ `nullable=False`. A model `default=` fills the value
via the ORM at insert time; the column still allows NULL at the DB level. And
wrap a callable default in `lambda` (`default=lambda: datetime.now(UTC)`) so it
evaluates per insert, not once at import.

**Gotcha (Day 29, the multi-replica one):** migrations are single-writer;
app instances are many. Running `alembic upgrade head` from every replica on
boot is a race — mine collided on `CREATE TABLE alembic_version` and a replica
crashed. Fix: a dedicated one-shot `migrate` service that runs once and exits,
with the API depending on `condition: service_completed_successfully`. Migration
is single-writer, serving is many — they shouldn't share a startup command.

## 2.4 Indexes — how lookups get fast

Without an index, `WHERE id = 42` is a **sequential scan**: O(n). An index is a
**B-tree** — sorted, shallow — making it O(log n), roughly 3–4 page reads even
over millions of rows.

What you must be able to say:

- **Indexes cost writes.** Every INSERT/UPDATE maintains every index. Index the
  columns you *query by*, not everything.
- **Composite `(a, b)`** is a phone book sorted by (last, first): great for
  `a=… AND b=…` or `a=…` alone, useless for `b` alone — **leftmost prefix**.
- **Why the planner ignores your index:** low selectivity, a function on the
  column (`lower(email)` needs an index *on* `lower(email)`), or a tiny table.
- **`EXPLAIN ANALYZE`** is the tool. "I'd check the plan" is the senior move.

**Gotcha, and it applies directly here:** an index on `orders.status` barely
helps dispatch — five statuses, low selectivity, half the table matches. A
**partial index** (`CREATE INDEX … WHERE status = 'PENDING'`) is tiny and
exactly right for "fetch pending orders." Naming partial indexes is a strong
Postgres signal.

## 2.5 In-memory vs on-disk, client vs server

A Python dict lives in the process's RAM and dies with it. Postgres writes to
disk and survives restarts. And both Postgres (5432) and Redis (6379) are
**separate server processes** — your app is one client over a socket, `psql` and
`redis-cli` are others.

**Soundbite:** "Postgres and Redis aren't libraries inside my app — they're
separate servers I connect to. That separation is what gives shared state across
many app instances." (It's also why `localhost` breaks inside Docker — §7.6.)

**Gotcha:** "why isn't X in DBeaver?" is almost always "because X is Redis
state." `orders_today` counters, geohash cells, rate-limit buckets and
idempotency records never appear in a Postgres client.

## 2.6 Level check — §2

1. Draw orders ⋈ riders; give both JOIN results.
2. `WHERE` vs `HAVING`; `COUNT(*)` vs `COUNT(col)`.
3. Walk `add → commit → refresh`. What breaks without `refresh`?
4. What is N+1, how do you detect it, two fixes?
5. Why can't `create_all` replace migrations? What's the `env.py` import trap?
6. Why might the planner ignore an index on `status`? What's a partial index?
7. Why is running migrations from every replica wrong, and what replaces it?

---
---

# 3 — The fast layer: Redis

## 3.1 What Redis is here for

**Concept.** Postgres is a durable map backed by disk. Redis is a hash map in
RAM: O(1), microseconds, no durability by default. You use it for state you
read/write constantly and can afford to rebuild.

**What DeliverIQ keeps in Redis** — and nothing else:

| Key | Type | Job |
|---|---|---|
| `ratelimit:<client>` | hash | tokens + last-refill timestamp |
| `geohash:<cell>` | set | which riders are in this cell |
| `rider:<id>:loc` | hash | that rider's lat/lon/cell |
| `rider:<id>:orders:<UTC-date>` | counter | fairness — orders today |
| `idempotency:<key>` | string | cached response for a POST retry |

**The rule: set = a bag of interchangeable peers; hash = one record with named
fields.** A rider is a *member* of a cell roster and the *owner* of a location
record — same rider, two roles, two structures.

**Soundbite:** "Redis is in-memory, so it's microsecond-fast but lossy on
restart. I use it for hot ephemeral state — rate-limit buckets, the geohash
index, daily counters, idempotency records — never as a source of truth.
Postgres stays the durable record; Redis is the fast layer over it."

**Gotcha:** Redis returns everything as strings, even with
`decode_responses=True` — `float(loc["lat"])`, `int(count)`. Forget the cast and
the math chokes.

## 3.2 The token-bucket rate limiter

**Concept.** A bucket holds up to N tokens (100). Each request spends one. It
refills continuously from elapsed time:
`tokens = min(CAP, tokens + elapsed × refill_rate)` (100/min). Empty → `429`.

**Why token bucket over fixed window** — two reasons, both worth saying:

1. **It allows controlled bursts.** An idle client accumulates up to bucket size,
   bursts that, then is throttled to the refill rate. That matches real traffic.
2. **No boundary-burst flaw.** A fixed window resets its whole count at the
   window edge, so a client fires 2× the limit straddling the reset (5 at 0:59,
   5 at 1:00). Token bucket refills smoothly — that instant of a fresh full
   budget never exists.

The price is slightly more state: tokens *plus* a timestamp, not one counter.

**Why it's middleware, not a dependency.** A dependency runs before the handler
and hands a value in — it sits on the **entry path only** and never sees the
response. Middleware wraps the handler via `call_next`, so it can gate the
request *and* decorate the response with `X-RateLimit-Remaining`. The limiter
needs both sides; only middleware has both.

**Gotcha, and it's a good one:** what does `expire(key, 120)` actually do? It's
**memory housekeeping, not recovery.** A client that makes one request and
vanishes would otherwise leave its bucket in RAM forever. *Delete the expire
line and rate limiting still recovers perfectly* — recovery comes entirely from
the elapsed-time refill math. It **would** break a fixed-window limiter, where
the TTL *is* the window reset. Knowing that the TTL plays a different role in
two algorithms is the senior signal.

## 3.3 Making it atomic — the Lua script

**The race.** The first version did three Redis ops: HGETALL → compute in Python
→ HSET. Between the read and the write a concurrent request reads the **same**
token count, so two requests both see "1 token left" and both pass. Classic
read-modify-write race, and it's real the moment you run more than one worker.

**The fix.** Collapse refill + check + decrement into **one Lua script**. Redis
executes commands single-threaded and runs a script to completion before serving
any other client, so nothing interleaves. One `EVALSHA` round-trip, still
sub-millisecond, now correct.

**Soundbite:** "Three Redis calls with a gap between read and write meant two
concurrent requests could both read the same count and both pass. I collapsed it
into one Lua script — Redis runs a script atomically because command execution
is single-threaded — so the whole check is a single indivisible round-trip.
That's what makes the limiter safe across three API replicas sharing one Redis."

**Gotcha:** `register_script()` uses `EVALSHA` (send the hash, not the body,
every call). And Lua numbers are floats while Redis integer-truncates a bare
numeric return — so the script returns `tostring(tokens)` and Python parses it
back, or the remaining-tokens header loses its fraction.

**Gotcha — this was a real gap, now fixed (§9.4):** the limiter used to key on
`X-API-Key or client.host`, so a client could rotate a header it controls and
mint a fresh bucket per request — a rate limiter anyone could opt out of. It now
keys on the **verified** token subject first, falling back to `X-Forwarded-For`
only when `trust_proxy_headers` is set (that header is spoofable unless a proxy
you control overwrites it), and finally the peer address. Worth stating as the
general rule: **throttle on the most trustworthy identifier available, never on
one the caller can choose.**

## 3.4 Dual-write consistency: Postgres ↔ Redis

**Concept.** Riders live in **two stores at once**: Postgres is the durable
truth, Redis is a hot geohash index for matching. Every rider write — create,
move, go BUSY, go AVAILABLE — must update both in one request. That's a **dual
write**, and there is no transaction spanning two systems.

**Why riders and not orders?** Orders live in Postgres only — the dispatch heap
is rebuilt from the DB each call, nothing cached. Being able to say *why* one
needs dual-write and the other doesn't shows you understand the pattern:
**the dual-write cost only appears when you cache derived state.**

**The move-path trap (the real bug).** Indexing a rider does `sadd` to their
cell's set. On a **move** you must `srem` them from the *old* cell **before**
`sadd`-ing the new one, or they stay a phantom member of every cell they have
ever been in and get matched at a location they already left. The old cell is
recoverable from the `rider:{id}:loc` hash. Guard with
`if old_cell and old_cell != new_cell` so a no-op move doesn't churn the set.

**What if the second write fails?** Postgres commits, the Redis write throws,
they drift. Recovery is **reconciliation**: Redis is fully reconstructable from
Postgres, so `scripts/reindex_riders.py` rebuilds the whole index from the DB.
Truth is never at risk; only the cache goes briefly stale, and it self-heals.

**Soundbite:** "Riders are in two stores — Postgres authoritative, Redis a hot
geohash index — so every rider write is a dual write with no shared transaction.
I keep Postgres authoritative precisely because Redis is the rebuildable layer:
if they drift, a reindex job restores the index from the DB. The subtle bug is
the move path — you must remove the rider from the old cell before adding the
new one, or they become a phantom member of stale cells."

**Gotcha:** a flushed Redis leaves every rider invisible to dispatch **with no
error raised anywhere** — dispatch just reports "no rider available". Derived
state that fails silently needs an explicit rebuild path, which is why that
script exists.

## 3.5 Cache patterns — the general theory behind §3.4

```
 CACHE-ASIDE (the default)
                ┌── hit → return              (fast path)
 request ──► Redis
                └── miss → Postgres → write to Redis + TTL → return

 WRITE path: update Postgres, then INVALIDATE (delete) the key —
 delete, don't overwrite: the next read repopulates a guaranteed-fresh value.
```

- **Write-through** (cache+DB together) and **write-behind** (cache now, DB
  async — fast, risks loss) are the variants. Name them; default to cache-aside.
- **TTL** bounds staleness even when invalidation misses.
- **Stampede:** a hot key expires and 1000 concurrent requests all miss and hit
  the DB together. Fix with a short per-key recompute lock, or jittered TTLs.

**Soundbite:** "Cache-aside with TTL, and on writes I invalidate rather than
update — a deletion can't be stale. The two failure modes to design for are
staleness, bounded by TTL, and stampede, bounded by recompute locks or jitter."

## 3.6 Level check — §3

1. What's in Redis vs Postgres here, and why is that split correct?
2. Set vs hash — which question does each answer?
3. Token bucket vs fixed window — name both advantages.
4. Why is the limiter middleware and not a dependency?
5. Does deleting `expire(key,120)` break recovery? Why does the answer flip for
   a fixed-window limiter?
6. What exactly is the read-modify-write race, and why is Lua atomic?
7. Why do riders need a dual write but orders don't?
8. What's phantom cell membership, and what's the fix — in what order?
9. Postgres commits, Redis write fails — what's the state and the recovery?

---
---

# 4 — The algorithms (steer the interview here)

## 4.1 Priority-queue dispatch with aging

**The problem.** Orders pile up as PENDING. FIFO is wrong — a ₹2000 order
shouldn't wait behind a just-arrived ₹150 one. You always want the
highest-priority pending order next. That's a heap.

**The mechanics.** `std::priority_queue` is a max-heap; Python's `heapq` is a
**min-heap with no max flag**, so you push the **negated** key. Push tuples
`(-priority, id)`; tuples compare element-by-element. `heapq` operates on a
plain list — it isn't a class you instantiate.

**Priority is a design decision, not a given.** Two factors compete: order
**value** (revenue) and **wait time** (don't starve cheap orders). Value-only
priority starves a ₹150 order forever. The fix is **aging**:

```python
priority = order.value + wait_minutes * AGING_WEIGHT   # AGING_WEIGHT = 10
```

The longer an order waits, the higher it climbs until it outranks fresh
expensive ones.

**Soundbite:** "Dispatch pops the highest-priority pending order from a max-heap
— negated keys, because Python's heapq is a min-heap. Priority is value plus a
wait-time aging term: without aging, a cheap order starves behind a stream of
expensive ones, which is the classic scheduling-starvation problem, and aging is
the OS technique for exactly it."

**Gotcha — volunteer this, it's a strength (see §9.5):** the current
implementation reloads *all* pending orders and rebuilds the heap on every call,
so it is **O(n log n) per dispatch**, not O(log n). For a single pop, a plain
`max()` would do equal work. The heap earns its keep when you pop many in
sequence or keep it warm across calls. The fix is a persistent/indexed priority
queue updated incrementally.

**The distributed alternative I know but didn't use:** move the queue into a
Redis sorted set — `ZADD` on create, `ZREVRANGE` to peek, `ZREM` to claim, where
`ZREM` returning 1-or-0 is an atomic concurrent-claim guard. I went with
Postgres row locks instead (§5.3) because they keep the aging and fairness logic
in one place and give me the same guarantee with the database as the single
arbiter. The sorted set also *hides* the DSA inside Redis; the heap demonstrates
it.

## 4.2 Geohash matching — two filters, in order

Matching is **two independent filters in sequence**, not one step:

1. **Geohash — coarse "who is even considered."** Encode (lat, lon) into a
   base-32 string where nearby points share a prefix. Look up the home cell plus
   its **8 neighbours** — a cheap set union, constant time regardless of fleet
   size, instead of a distance calculation against every rider. At precision 6 a
   cell is ~1.2 km × 0.61 km, so the 3×3 ring reaches ~3.6 km.
2. **Haversine — precise "how far, exactly" inside that set.** Cells are
   approximate; haversine gives real great-circle distance to rank survivors.
   Euclidean is wrong on a sphere — 1° of longitude shrinks toward the poles.

**Soundbite:** "Matching is a cheap filter then a precise sort: geohash gives an
O(1) candidate set because nearby points share a string prefix, so I read the
home cell plus eight neighbours instead of scanning every rider; haversine then
gives exact great-circle distance over that small set."

**Gotcha — the boundary bug (gold material, and I hit it live):** an order at a
cell *edge* can have its nearest rider just across the line, in a cell with a
completely different geohash string. Checking only the home cell misses them —
dropping the neighbours made a rider 10 m away invisible.

**Gotcha — range ≠ band.** The fairness band only filters riders geohash already
*found*. A rider 13 km away is outside the neighbour ring, so no band size —
even 50 km — pulls them in. Two filters, in sequence: geohash decides who is
considered, the band decides who is feasible among those.

## 4.3 The fairness band — the differentiator

```
 d_min    = nearest candidate's distance
 feasible = riders within d_min + Δ          (Δ = 500 m)
 winner   = min(feasible) on key (orders_today, distance)
```

**Why a hard band, not a blended score.** A blended `α·dist + β·load` can
**silently send a far rider** when the load term dominates — cold food, broken
SLA, and the formula gives you no way to know when it will happen. The hard band
makes the SLA guarantee **explicit and tunable**: fairness operates *only
inside* Δ, so a rider outside it is never eligible no matter how idle. Δ is the
single knob between competing goals — wider = more fairness, narrower = tighter
SLA.

**The behaviour you actually observe: two phases.** The system drains the load
imbalance first — idle riders absorb orders until they catch up — and then
reverts to nearest-rider, because once all loads tie the distance tiebreak takes
over. A nearest-only dispatcher would hammer the closest rider forever.

**Heap framing:** the selection is a min-heap on the composite key
`(orders_today, distance)` over the small feasible set — greedy on a composite
key, O(k log k) on candidates k, not O(n) over the fleet.

**Soundbite:** "Greedy-nearest optimizes pure distance. I add a bounded fairness
constraint: among riders within a band Δ of the nearest, assign the least-loaded.
It's a constrained assignment problem — minimize rider load subject to a distance
bound. A blended score could silently send a far rider when load dominates; the
hard band makes the SLA guarantee non-negotiable and tunable."

**The daily counter, with no cron.** `orders_today` is a **date-stamped key**:
`rider:<id>:orders:<YYYY-MM-DD>`. Tomorrow is a *different key* that starts at 0
— the key name **is** the reset. No midnight job, no reset race. A 48 h TTL
garbage-collects old days, and it **slides**: every order refreshes it, so an
active rider's key never dies mid-day.

**Gotcha:** the count and the TTL are independent. `incr` accumulates the day's
total; `expire` only refreshes the death clock. The reset comes from the date in
the key, not from the TTL. Keys are stamped in **UTC** — consistent across
servers, DST-free — so on IST the key reads the previous calendar day for the
first ~5.5 h after local midnight. In production you'd reset on the business
timezone so "today" matches the rider's day.

**Counted at assignment, not delivery.** `orders_today` answers "who has earned
the least today?" A rider assigned 5 orders has had 5 earning opportunities
regardless of delivery progress; counting at delivery would let a mid-delivery
rider keep looking idle and get piled on.

**The orthogonality worth naming:** BUSY and `orders_today` are independent axes.
BUSY = "can take work *now*?" (exclusion). `orders_today` = "earned least
*today*?" (ranking). BUSY already stops pile-on by removing the rider from the
index, so the counter doesn't need to.

**A story worth telling: I removed my own endpoint.** `POST /riders/match` was
the original demo of this algorithm. Once dispatch became the only real consumer
of `select_rider`, match's remaining effect was charging a rider an
`orders_today` point for an order that never existed. *Dead code with a live
side effect is worse than dead code — it's a latent bug.*

## 4.4 The order state machine

**Concept.** Order status is not a settable string — it's a **directed graph** of
legal transitions. Each status is a node, each allowed move an edge. The table is
an adjacency list; "is this legal?" is an O(1) set-membership check. Terminal
states have empty neighbour sets.

```
 PENDING ──→ ASSIGNED ──→ PICKED_UP ──→ DELIVERED
    │            │
    └──→ CANCELLED ←┘
```

**Why strict — no ASSIGNED → PENDING.** A rider who accepts then abandons does
not bounce the order back to the pool: re-dispatching means the customer waits
through a *second* matching cycle. Instead: cancel and penalize the rider. The
penalty lives on the **rider**, not as an order-state edge. *Order-state and
rider-penalty are independent state spaces; don't couple them.*

**The best point in this section — same call, two failure semantics ⭐**

The *same* `transition()` call means different things at different call sites:

- **The status endpoint** — the target comes from the **user**. An illegal
  transition is expected bad input → catch it, return **400**.
- **Dispatch** — the transition (PENDING→ASSIGNED) is derived from my own
  `status == PENDING` filter. A failure means a **server-side bug** → do not
  catch it, let it raise into a **500**.

**Soundbite:** "Same `transition()` call, two different failure semantics. In
the user-facing endpoint an illegal transition is expected bad input — catch it,
400. In dispatch the transition is derived from my own query invariant, so a
failure is a server bug — I let it raise into a 500 rather than mislabel my bug
as the client's bad request. Error handling follows *who caused the error*, not
the function being called."

**Gotcha:** wrapping the dispatch call in `try/except → 400` would blame the
client for a server logic error. That `transition()` is really an assertion —
and assertions aren't meant to be caught.

**Single gate.** Before the refactor, status changed in two places with two rule
sets. Routing dispatch through `transition()` too means every status change goes
through one gate. It's provably always-legal given the PENDING filter, so it
never fires — but the *invariant* is what's worth having: "there is exactly one
place order status changes legally," with no "except in dispatch" caveat. (The
honest counterpoint, have it ready: a check that provably can't fail is arguably
noise. Both positions are defensible; I lean to the invariant because it costs
one line.)

**Legal transition vs permitted actor — orthogonal guards.** The state machine
answers "is this move legal *at all*?" It does **not** answer "may *this caller*
make it?" A customer marking their own order DELIVERED is a legal edge by the
wrong actor. That second guard needs authenticated identity, so it lives in the
auth layer (§7.1) — and both must pass.

## 4.5 Level check — §4

1. Why negate keys in `heapq`? What do tuples compare on?
2. What is starvation, and how does aging fix it? What's the real complexity of
   my dispatcher?
3. Why two filters (geohash then haversine)? Why the 8 neighbours?
4. Why can't a huge band rescue a rider 13 km away?
5. Band vs blended score — argue the hard band.
6. Describe the two-phase behaviour of fairness dispatch.
7. How does the daily counter reset with no cron job?
8. Why does `orders_today` increment at assignment, not delivery?
9. Why does dispatch *not* catch `InvalidTransition` when the endpoint does?
10. Legal-transition vs permitted-actor — give an example that passes one and
    fails the other.

---
---

# 5 — Concurrency and distribution

This is the section the opener promises. Everything before it is table stakes.

## 5.1 Transactions and ACID, concretely

Assigning an order touches two rows. A transaction makes that one all-or-nothing
unit:

```sql
BEGIN;
UPDATE orders SET status='ASSIGNED', rider_id=2 WHERE id=1;
UPDATE riders SET status='BUSY' WHERE id=2;
COMMIT;   -- both, or (rollback/crash) neither
```

- **A — Atomicity:** crash between the updates and both are undone (via the WAL).
- **C — Consistency:** constraints hold before and after; the DB refuses a commit
  that breaks them.
- **I — Isolation:** concurrent transactions don't see each other's half-done
  work. The interesting one — it has *levels*.
- **D — Durability:** once COMMIT returns, the data survives power loss, because
  the WAL was fsynced before the DB said yes.

**Gotcha (SQLAlchemy):** the Session opens a transaction implicitly at your first
query and holds it until `commit()`/`rollback()`. Everything between is already
one transaction — knowing exactly where that boundary sits is what the row
locking below depends on.

## 5.2 Isolation levels and the anomalies

| Anomaly ↓ / Level → | Read Uncommitted | **Read Committed** (PG default) | Repeatable Read | Serializable |
|---|---|---|---|---|
| Dirty read | possible | ✅ prevented | ✅ | ✅ |
| Non-repeatable read | possible | possible | ✅ | ✅ |
| Phantom read | possible | possible | ✅ (in PG) | ✅ |
| Lost update / write skew | possible | possible | partly | ✅ |

Postgres implements Repeatable Read as **snapshot isolation** — a frozen snapshot
from transaction start; phantoms don't appear, but **write skew** still can.
Serializable catches even that, at the cost of serialization failures you must
retry.

**Soundbite:** "Postgres defaults to Read Committed, so no dirty reads — but two
reads in one transaction can disagree, and read-then-write races like a double
dispatch are absolutely possible. You fix those either by escalating to
Serializable and retrying failures, or — usually better — by explicit locking on
the rows that actually contend."

## 5.3 The lost update, and the fix ⭐

**This is the core story of the project.** Three replicas share one Postgres. Two
dispatch calls run at the same instant, both `SELECT` the same PENDING order
(reads don't block reads), both assign it.

```
 TIME  INSTANCE A                        INSTANCE B
  │    BEGIN                             BEGIN
  │    SELECT … WHERE status='PENDING'   SELECT … WHERE status='PENDING'
  │        → sees order 1                    → sees order 1  (same row!)
  │    UPDATE order 1 → ASSIGNED, r=2
  │    COMMIT ✅
  │                                      UPDATE order 1 → ASSIGNED, r=9
  ▼                                      COMMIT ✅ ← silently overwrites A
 RESULT: order 1 assigned to rider 9; rider 2 is BUSY for nothing.
 No error was raised anywhere — that's what makes lost updates dangerous.
```

**Fix 1 — pessimistic ("assume conflict, take the lock first"), what I used:**

```sql
SELECT * FROM orders
WHERE id = :id AND status = 'PENDING'
FOR UPDATE SKIP LOCKED;
```

- `FOR UPDATE` = lock the returned rows until my transaction commits.
- `SKIP LOCKED` = rows someone else holds are **invisible to me** — don't wait,
  move on. (`NOWAIT` errors instead of skipping.) That turns a table into a safe
  multi-consumer job queue.
- The lock exists **only inside an open transaction**. Lock, mutate and commit
  must be one transaction or it's theatre.

**Fix 2 — optimistic ("assume no conflict, detect at write time"):**

```sql
UPDATE orders SET status='ASSIGNED', rider_id=2, version=8
WHERE id=1 AND version=7;     -- 1 row → you won; 0 rows → reload and retry
```

| | Pessimistic (`FOR UPDATE`) | Optimistic (version guard) |
|---|---|---|
| Contention | high — everyone wants the same hot rows (a dispatch queue) | low — conflicts rare |
| Cost | holds locks; others wait or skip | retries wasted work on conflict |

**Soundbite:** "Read-then-write with no guard is a lost update — two replicas
read the same PENDING row and the second silently wins. For a dispatch queue I
went pessimistic: `SELECT … FOR UPDATE SKIP LOCKED` inside the transaction, so
each instance claims a disjoint row and skips rather than waits. For a
low-contention update I'd go optimistic — a version column and a conditional
UPDATE, retrying on zero rows affected."

**Gotcha:** do **not** lock the whole candidate set. Put `FOR UPDATE` on the
initial "select all PENDING" and one instance locks every order while the others
see an empty set and wrongly report "no orders." I keep the priority scan
lock-free and lock only the single row I'm about to claim.

**Gotcha:** a Postgres lock covers nothing in Redis. Every store needs its own
atomicity story — Lua for the limiter (§3.3), an atomic `SREM`/`ZREM` for a
Redis-side claim.

## 5.4 The two-phase claim — claim everything before mutating anything ⭐

**The bug that actually bit me, and it was not the lock.** The lock was correct
the whole time. The ordering was wrong. The loop set `order.status = ASSIGNED`
and `order.rider_id` **before** locking the rider. When the rider turned out to
be taken, it did `continue` to the next order — but those order mutations were
still pending in the SQLAlchemy **session**. A session is a *unit of work*: the
next successful candidate's `db.commit()` flushes **everything** pending,
including the abandoned order's mutations.

Result: phantom ASSIGNED rows for orders no request ever successfully dispatched.
The tell was that the DB had more ASSIGNED orders than the API returned success
responses.

**The fix — the shape of the final code:**

```
 CLAIM 1  lock the order row      (FOR UPDATE SKIP LOCKED)   → miss? next order
 CLAIM 2  select a rider, lock the rider row                 → miss? next rider
          ── both rows exclusively mine ──
 MUTATE   transition(), set status/rider_id, rider → BUSY
 COMMIT
 THEN     Redis (SREM from index, INCR orders_today) and Kafka publish
```

**Soundbite:** "The subtle bug wasn't the lock — it was that I mutated the order
before securing the rider. On a failed rider claim I `continue`d, but the ORM
session still held those pending changes, and the next successful commit flushed
them, creating phantom assignments. A session commits the whole unit of work, not
just the changes you meant. Fix: claim all rows first, mutate last."

**Gotcha:** `session.commit()` flushes **all** dirty objects, not the one you're
focused on. Never leave half-applied mutations on a code path that continues to
another commit.

**Why Redis writes come after the commit.** `select_rider` is a pure read. The
fairness INCR, the geohash SREM and the publish all run **after** `db.commit()`,
so a rolled-back or failed dispatch never leaves a bumped counter or a stale
index entry. Postgres stays the single source of truth; Redis only ever mirrors
committed reality.

## 5.5 Correct is not the same as live — the thundering herd ⭐

**The measurement that changed the design.** The verified loop had **zero**
double-assignments, and still behaved badly under a real burst: 15 simultaneous
dispatches, 10 orders and 10 riders, 3 replicas → only **5 succeeded**. Ten
returned 409 while five riders sat AVAILABLE.

**Why.** Every concurrent caller ranks riders identically, because the state that
would differentiate them — the winner's SREM and `orders_today` INCR — only lands
*post-commit*. So all losers pick the same top rider, fail the claim, and — the
actual bug — `continue`d to the **next order**, chasing that same rider down the
entire heap until 409. *Losing a rider lost the whole order.*

**The fix — retry the rider, keep the order.** `select_rider(…, exclude=tried)`:
on a failed rider claim, add that rider to an exclude set and re-select the
next-best **for the same order**. Bounded (candidates in the 3×3 ring are finite
and every failure shrinks them) and **mutation-free**, so the claim-all-before-
mutate invariant survives. One deliberate subtlety: exclusion runs *before*
`d_min` is computed, so the fairness band re-centres on the nearest **eligible**
rider — the SLA bound stays relative to riders you can actually get.

**Same test after the fix: 10/15 — every order dispatched in one burst, still
zero doubles.**

**Soundbite:** "My locking was correct but not live. Under a burst all instances
chase the same top-ranked rider, because the differentiating state only lands
post-commit — I measured 5 of 15 succeeding with riders idle. The fix is a
bounded rider-level retry: exclude the contested rider and re-select for the same
order. Same test after: 10 of 15, full drain, zero doubles. Losing a race now
costs one candidate, not the whole request. Correctness and liveness are separate
properties and you have to measure both."

**A bonus it bought for free:** a stale BUSY rider stuck in the geohash index —
crash after commit, before SREM — used to poison every order's selection. Now it
costs one failed claim and gets excluded. Self-healing.

**The sibling lesson — the silent side-effect regression.** Splitting
`select_rider` into pure-read plus `record_rider_assignment` (command–query
separation) updated dispatch but **forgot the other caller**: `/riders/match`
silently stopped counting fairness. No error, no failing test, just quietly
wrong. Rule: when you move a side effect out of a function, **grep every caller**
before you call it done.

## 5.6 Deadlocks and pooling (the two follow-ups)

**Deadlock** = a lock cycle: A holds order 1 and wants rider 2; B holds rider 2
and wants order 1. Postgres detects the cycle and **kills one** transaction; your
app retries. The real fix is **consistent lock ordering** across all code paths
(always order-then-rider) plus short transactions. DeliverIQ acquires order then
rider, always — that's not incidental.

**Connection pooling.** Opening a connection is expensive (TCP + auth + a
Postgres backend process). The engine keeps N warm connections that requests
borrow and return. Sizing is `instances × pool_size` against `max_connections`
(~100 default): 3 replicas × 20 = 60. That 20 is configured explicitly in
`app/core/database.py` — SQLAlchemy's default is 5 + 10 overflow, so quoting the
arithmetic without setting the value describes a system you do not have. Do the
arithmetic before the DB does it for you; PgBouncer is the next tier.

## 5.7 The statelessness checklist — "can I run 3 of these?"

```
                       ┌──► replica 1 ─┐
 clients ──► LOAD      ├──► replica 2 ─┼──► shared Postgres
             BALANCER  └──► replica 3 ─┘──► shared Redis / Kafka
```

Horizontal scaling requires that every piece of mutable state either moves to a
shared store or gets a concurrency-safe claim protocol. What breaks at N:

- ❌ in-memory counters (the rate limiter had to live in Redis, atomically)
- ❌ module-level mutable state, local file writes
- ❌ in-process queues — a per-process heap means two instances pick the same
  order, which is exactly the §5.3 race
- ❌ migrations on app boot (§2.3) — single-writer work in a many-instance path
- ❌ cron inside the app — 3 instances, 3 executions
- ⚠️ sticky sessions are a smell; fix statelessness instead

**Soundbite:** "My audit found two single-instance assumptions — the in-process
dispatch pick and pre-commit Redis writes — and the SKIP LOCKED work plus
post-commit mirroring is what fixed them. That's the difference between 'designed
for scaling' and 'ran three replicas and measured it.'"

## 5.8 Postgres internals — the "how does it actually work" answer

- **WAL (write-ahead log):** every change is appended to a sequential log and
  **fsynced before COMMIT returns** — that's Durability. Crash recovery replays
  the WAL; replication streams it. Sequential appends are why commits are fast.
- **MVCC:** an UPDATE doesn't overwrite, it writes a **new row version**; each
  transaction reads versions visible to *its* snapshot. Hence readers never block
  writers and writers never block readers — only writer-vs-writer needs locks.
  Dead versions pile up until **VACUUM** reclaims them.

**Soundbite:** "Commit means the WAL hit disk; data pages catch up later, and
replicas are just WAL consumers. MVCC gives every transaction a snapshot over row
versions, so reads and writes don't block each other. The costs are vacuum debt
and the fact that MVCC does *not* prevent write-write races — which is exactly
what my explicit row locks are still for."

## 5.9 Level check — §5

1. Draw the lost-update interleaving. Fix it both ways; say when each is right.
2. Why must `FOR UPDATE` sit inside the transaction that also writes?
3. Why is locking the entire pending set wrong?
4. The lock was correct — so what actually caused the phantom assignments?
5. "A session commits the whole unit of work" — concretely, what does that mean?
6. Why must every Redis write come after `db.commit()`?
7. "Correct but not live" — what did the 15-burst test measure before and after,
   and why did every loser chase the same rider?
8. Why must the rider-retry loop stay mutation-free?
9. Deadlock: cause, what Postgres does, the prevention rule.
10. Name four things that break when you run three replicas.
11. What does "COMMIT returned" guarantee, mechanically? What race does MVCC not
    solve?

---
---

# 6 — Events: from Pub/Sub to Kafka

## 6.1 Why events at all — the coupling I felt first

The status endpoint does *rider* side effects: on DELIVERED/CANCELLED it frees
the rider and re-indexes them. That's legitimate coupling — the rider's freedom
depends on the order finishing — but it's exactly what an event-driven design
decouples. I built it coupled first so the seam was visible, then moved order
events onto a bus.

**Commit before publish, always.** The event announces a *durable fact*.
Publishing before `db.commit()` risks a consumer reacting to an assignment that
then rolls back. Order is always: mutate → commit (truth) → publish (announce).

## 6.2 Redis Pub/Sub — the flaw that motivates Kafka

Redis Pub/Sub delivers only to subscribers **alive at publish time**. No queue,
no persistence, no replay. Stop the worker, dispatch, restart — the event is gone
with no record it existed.

**Soundbite:** "I used Pub/Sub first deliberately so I'd feel the limitation
firsthand: it's fire-and-forget, so a subscriber that's down misses the message
forever. Then I moved order events to Kafka, which persists to disk and lets a
recovered consumer resume from its last offset."

**Gotcha:** the first frame from `SUBSCRIBE` is a `type="subscribe"` confirmation
whose `data` is the subscription *count*, not a payload. Skip it or the first
`json.loads` parses an integer and crashes.

## 6.3 Kafka is not a queue ⭐

Every broker before Kafka assumes the broker's job is to deliver a message and
then forget it — **consumption is destructive**. Kafka inverts that: the broker
appends bytes to a file and moves on. **Reading changes nothing.** The message is
deleted when a **retention policy** says so, never because someone read it.

- Redis Pub/Sub = a **loudspeaker**. In the room, or you missed it.
- Kafka = **a ledger you bookmark**.

**Soundbite:** "Kafka isn't a queue, it's a durable append-only log. Reading
doesn't consume — retention deletes. That single inversion is what makes replay
possible: the bytes are on disk regardless of who read them, so a consumer that
was down comes back and reads exactly what it missed."

**Gotcha:** "Kafka is just a more scalable RabbitMQ" — no. RabbitMQ's broker
tracks per-message state (delivered/acked/in-flight), which buys it per-message
retry and dead-letter handling and **costs it replay**. Kafka trades that state
for speed and replayability. Two different tools, not two tiers of one.

## 6.4 Partitions — ordering and parallelism are the same knob ⭐

A topic **is** its partitions; there's no flat log underneath.
`order.dispatched` with 3 partitions = three separate files, each appended
independently, each with its own offset counter from 0.

Two consequences, both trades:

- **Ordering shrinks.** Kafka guarantees order **within** a partition and makes
  **no promise across** partitions. You bought parallelism with global ordering.
- **Parallelism is capped** at the partition count, per group.

Placement is `hash(key) % num_partitions` — arbitrary but **stable**. No key →
round-robin → no ordering guarantee at all.

**DeliverIQ keys by `order_id`**, so one order's lifecycle can never arrive
scrambled. Different orders have no ordering relationship, and don't need one.

**Soundbite:** "Partitions are the unit of both ordering and parallelism — order
holds inside a partition and a group's max parallelism is its partition count. I
key by `order_id` so one order's events stay ordered; across orders there's no
guarantee and no need for one."

**Gotcha 1 — "Kafka guarantees ordering."** Unqualified that's wrong, and a good
interviewer stops you there. Per-partition only.

**Gotcha 2 — hot partitions.** The hash owes you nothing. Observed live: 6 keys
split 2/2/2, then two more keys both hashed to P0 → 4/2/2. Key by something
skewed (one restaurant producing 80% of events) and one partition eats 80% of the
load while two idle.

**Gotcha 3 — head-of-line blocking.** Unrelated keys share a partition. Harmless
for correctness (each key's events are still an ordered subsequence). The real
cost: a poisoned or slow message **stalls every other key in that partition** —
which is why the DLQ in §6.8 exists.

**Gotcha 4 — the hash is client-specific.** librdkafka defaults to CRC32, the
Java client to murmur2, so the *same key* lands on *different partitions* across
clients. Pin `partitioner=murmur2_random` to interoperate. And the modulus means
**adding a partition re-maps every existing key** and strands its old events —
a silent, irreversible ordering break with no error and no migration path. If
ordering must survive scaling, over-provision partitions up front.

## 6.5 Consumer groups — one string picks load-balance or broadcast ⭐

> Within a group, each partition is assigned to **exactly one** consumer.
> Across groups, **everyone gets everything**.

A group is **not** a subset of the data. Groups don't slice events — every group
reads every event. The slicing happens *inside* a group, between its members.

| Group | Members | Partitions covered | Files per member |
|---|---|---|---|
| `analytics` | 1 | 3 (all) | 3 |
| `notifications` | 2 | 3 (all) | 2 and 1 |
| `audit` | 3 | 3 (all) | 1 each |
| `audit` + a 4th | 4 | 3 (all) | 1, 1, 1, **and 0** |

**DeliverIQ runs three groups on one topic:** `notifications`, `analytics`
(writes Postgres), `audit` (appends a file). Each has its own committed offsets,
so one failing or falling behind cannot affect the others, and a new group
replays history from the start.

**Failure isolation:** kill `analytics` → its offsets freeze; the other two don't
notice; restart and it replays its backlog. **Blast radius = one group.** Kill
one *member* → Kafka rebalances and survivors absorb the orphaned partitions.

**Soundbite:** "`group.id` is the only knob: same id means competing consumers
splitting partitions — a work queue; different ids mean independent readers with
independent offsets — fan-out. Kafka does both from one log, and within a group a
partition has exactly one owner, so scaling out never duplicates work."

**Gotcha — the per-process group id.** `group_id = f"notifications-{os.getpid()}"`
makes every worker its own group. Scale to 3 and the rider gets **3 SMS per
order**. It looks perfect on one machine in dev. `group.id` is the identity of the
*application*, not the process.

**Gotcha 2 — more consumers ≠ more throughput.** Past the partition count, extra
members sit idle burning RAM.

## 6.6 The dumb broker — where the offset actually lives ⭐

Apparent contradiction: "the broker appends and forgets" vs "the broker knows
where group `notifications` was." Resolution:

> **The broker doesn't know. The consumer told it, and the broker wrote it down
> the same dumb way it writes everything else.**

`__consumer_offsets` is **a topic**. Committing an offset is not a special API —
the consumer *produces a message* keyed by `(group, topic, partition)` with the
offset as the value. On restart the consumer **asks** for the latest value for
that key. That's a read, not a memory.

**The proof:** you can put the offset **anywhere**. A common production pattern
writes it into your own Postgres table *in the same transaction as the work*, and
`seek()`s on restart. Kafka has zero knowledge of your progress and it works
perfectly.

**Soundbite:** "Kafka's broker is deliberately dumb — no per-consumer state, no
delivery tracking, no push. An offset is just a message the consumer produces to
an internal compacted topic. That's why the broker scales and why replay is free
— and it means commit *timing* is your delivery guarantee."

**Gotcha:** `__consumer_offsets` uses cleanup policy **compact** (keep the latest
value per key forever) while your topics use **delete** (retention by age/size).
That asymmetry is why the bookmark outlives the events it points at.

**Gotcha:** `--describe --group X` on a group with no running process still
returns rows — "no active members" means *exists, empty*. A group is a set of
rows, not a process.

## 6.7 Delivery semantics — a commit *placement*, not a setting ⭐

Two actions that cannot be fused: **A** = process (send the SMS), **B** = commit
(move the bookmark). A crash can land between them, so you only choose the
**order**, and the order picks your bound.

| Order | Crash outcome | Counts | Name |
|---|---|---|---|
| **B → A** (commit first) | bookmark moved, work never happened | 0 or 1 | **at-most-once** — no dupes, loss possible |
| **A → B** (commit last) | work done, bookmark didn't move → redo | 1, 2, 3… | **at-least-once** — no loss, dupes possible |

DeliverIQ's shared runner sets `enable.auto.commit=False` and calls
`consumer.commit(message=msg)` **after** the handler returns. Auto-commit hands
that ordering to a timer that fires whether or not processing finished, which
silently converts a correct at-least-once worker into a lossy at-most-once one.

**Proven, not assumed.** I injected a crash *between* PROCESS and COMMIT:

```
 RUN A  [notify] order 99 (offset 0)   → killed before commit landed
 RUN B  [notify] order 99 (offset 0)   ← RE-DELIVERED
 RUN C  (silent)                        ← offset now committed
```

**Why exactly-once isn't on the menu:** it needs A and B to be atomic. A is an
SMS gateway, B is a write in Kafka — two systems, no shared transaction. That's
the **dual-write problem** again. The answer is **at-least-once + idempotent
handler = effectively once**: the duplicate still arrives, you make it harmless.

**How DeliverIQ makes it harmless:** the analytics consumer inserts with
`ON CONFLICT DO NOTHING` against a unique constraint on **(partition, offset)**,
so a redelivered message inserts zero rows instead of double-counting. Doing the
dedupe in **one statement** matters — a SELECT-then-INSERT would race a second
worker in the same group and both would decide the row was absent.

**Soundbite:** "At-least-once isn't a flag, it's where I put the commit. I
disable auto-commit and commit after the handler returns, so a crash in the gap
re-delivers rather than skips — I proved it by killing the process in that gap.
The cost is that duplicates become my problem, so the analytics consumer
deduplicates on partition and offset with ON CONFLICT DO NOTHING. Delivery stays
at-least-once; the *effect* becomes exactly-once."

**Gotcha:** "Does Kafka support exactly-once?" The trap answer is a flat yes.
Correct: **yes for Kafka-to-Kafka** via transactions; **no for external side
effects** — there you engineer it with idempotency.

**Gotcha:** `commit(message=msg)` commits `msg.offset() + 1` — the *next* offset
to read. A group's CURRENT-OFFSET is always "where I'd resume," which is why it
reads one higher than the last message you saw.

## 6.8 The poison pill and the DLQ — the half of at-least-once nobody mentions ⭐

**Concept.** Commit-after has a corollary that follows inescapably: **a message
that can never be processed can never be skipped.** One malformed payload throws,
the process dies before the commit, the restart re-reads the same message, and
the partition never advances again. Every valid event queued behind it on that
partition is never delivered.

**And the lag dashboard says everything is fine.** `kafka-consumer-groups
--describe` prints *no row at all* for a partition with no committed offset — so
the wedged partition doesn't appear, and the remaining partitions honestly report
LAG 0. Health is green while a third of the topic is stuck.

**The fix, and the ordering that makes it safe.** The handler is wrapped:
anything that throws is published to `order.dispatched.dlq` with its original
topic, partition, offset, key, raw bytes and the exception — then **flushed
until the broker acks** — and only then does the offset advance. If the flush
isn't confirmed, the worker **stops without committing** so the message is
redelivered rather than lost.

**Soundbite:** "Commit-after gives me at-least-once, but it also means a message
I can't parse blocks its partition forever — and the lag metric won't show it,
because a partition with no committed offset has no lag row. So unprocessable
messages go to a dead-letter topic with full context, and the offset advances
only once that publish is acknowledged. The subtle part is the ordering:
committing on an unacked DLQ publish steps past the message with no copy of it
anywhere."

**Gotcha:** a DLQ you commit *optimistically* is worse than no DLQ — it converts
"stuck but recoverable" into "silently gone." And a DLQ nobody reads is a
landfill; the follow-up work is a replay tool, not just the topic.

## 6.9 The dual-write hole — and why post-commit isn't enough ⭐

Dispatch commits to Postgres, **then** produces to Kafka. Two systems, one
non-atomic pair of writes.

Post-commit ordering is *mandatory*: publishing before the fact is durable means
a rollback leaves a permanent, replayable phantom event — **worse** in Kafka than
in Pub/Sub, because Pub/Sub's phantom evaporates while Kafka's sits on disk and
every future consumer group replays it.

But post-commit still leaves a window: commit succeeds, then the process dies or
the produce times out → order ASSIGNED in Postgres, event never delivered,
nothing rolls back.

**Proven live.** I dispatched with the broker *stopped*: the API returned
`200 OK`, order ASSIGNED, rider BUSY — because `produce()` does no I/O and cannot
fail. The consumer reading `--from-beginning` showed only the recovered order;
the outage order's event was gone, and Postgres could not tell which one never
reached Kafka.

**The mechanism, measured:** the event doesn't fail on reconnect — it sits in the
producer's **in-memory queue and keeps retrying** for `message.timeout.ms`, then
is dropped (`_MSG_TIMED_OUT`). So a *short* outage is invisibly survived by the
retry buffer, and the event is lost when the retry window expires **or the
process exits**. That buffer is memory: a deploy or crash during the outage loses
it with no trace at all.

**The fix I did not build: the transactional outbox.**

```
 ┌─ one Postgres transaction ──────────────────┐
 │ UPDATE orders SET status='ASSIGNED' …       │  state change and event
 │ INSERT INTO outbox (event_json)             │  recorded ATOMICALLY
 └─────────────────────────────────────────────┘
        │  a relay polls the outbox (or tails the WAL — CDC/Debezium)
        ▼  Kafka ──► mark the outbox row published
        (the relay may retry ⇒ duplicates ⇒ consumers must be idempotent)
```

**Soundbite:** "Dispatch is a dual write — Postgres commit then Kafka produce,
no shared transaction. I publish post-commit so a rollback can't leave a phantom
event, but any crash in that gap leaves an order assigned with no event and
nothing to undo it. I proved it: dispatched with the broker down, got a 200, and
the event sat retrying in a memory buffer until it timed out. The fix is the
transactional outbox — write the event to an outbox table inside the order's
transaction and let a relay publish it, so the event is exactly as durable as the
state change because it *is* the state change. I scoped it out for a portfolio
project; it's the first thing I'd add if this were payments."

**Gotcha:** "just publish inside the transaction" is **strictly worse**, not a
fix — a rollback then leaves Kafka with a permanent record of an assignment that
never happened. Neither pre- nor post-commit is correct for two independent
systems; that's the whole reason the outbox pattern exists.

## 6.10 The producer — async, and what that costs you

- **The producer is a resource, not a value.** One per process, lazily created.
  It owns a background I/O thread, TCP connections and a message buffer.
  Per-request construction means a thread and handshake per dispatch, zero
  batching, and — the real killer — the object gets garbage-collected while its
  buffer still holds unsent messages, which vanish silently.
- **`produce()` is async.** It enqueues to memory and returns immediately, doing
  no network I/O, so it **cannot fail on a dead broker**. A background thread
  sends; `poll(0)` drains *already-completed* callbacks. A producer can therefore
  never synchronously confirm delivery — anyone returning `delivered=True` from a
  produce wrapper has a bug.
- **Two separate error channels.** `produce()` raises only on local queue-full
  (`BufferError`); broker and delivery failures arrive **exclusively via the
  callback**, later, on another thread. A `try/except` around `produce` proves
  nothing about delivery.
- **`flush()` on shutdown narrows the window, doesn't close it.** It runs in the
  FastAPI lifespan shutdown and handles **SIGTERM** — rolling deploys,
  scale-downs, `compose down` (SIGTERM, 10 s grace, then SIGKILL — a 5 s flush
  fits). It cannot cover SIGKILL, OOM-kill or a pulled plug. Closing that window
  is the outbox's job.

**Idempotence is transport-level, not semantic (the trap).**
`enable.idempotence=True` gives the producer a PID plus a per-partition sequence
number, so the broker drops a **network retry** of a message it already wrote. It
does **not** dedupe two separate `produce()` calls with identical payloads —
proven: four identical calls with idempotence on produced four rows.

**Soundbite:** "Producer idempotence dedupes retries, not payloads —
exactly-once *within one producer session to one partition*. It says nothing
about my code calling produce twice. Business-level dedupe is the consumer's job:
an idempotency key plus a uniqueness constraint."

## 6.11 Operating it: lag, offsets, and Kafka in Docker

**Consumer lag** = `LOG-END-OFFSET − CURRENT-OFFSET`, per (group, partition). A
consumer can be alive, polling, healthy on CPU and **falling behind forever** —
"is the process up" tells you nothing. Lag flat at 0 is healthy; lag climbing
means you're losing, and the fix is more consumers (up to the partition count) or
a faster handler. Pub/Sub *cannot produce this number* — there's no log end to
subtract from. Measurability is a consequence of durability.

**Gotcha:** lag is per-partition. LAG 0 on two partitions and 40k on a third
isn't "mostly fine" — it's a hot partition or a stuck consumer, and averaging
hides it.

**`auto.offset.reset` is a fallback, not a rewind.** Startup logic: does a
committed offset exist for (group, topic, partition)? **Yes → use it, the setting
is ignored entirely.** No → *now* apply it (`earliest` = 0, `latest` = log end).
Verified live: `--from-beginning` on a caught-up group processed **0 messages**.
It worked the first time only because the group had never existed.

Replay is an **administrative act** — you edit the row:
`kafka-consumer-groups --reset-offsets --to-earliest --dry-run`, then
`--execute`, which **refuses while the group has active members**. Stop → reset →
restart is the procedure.

**Gotcha (it bites the other way in production):** a new consumer deployed with
the default `auto.offset.reset=latest` silently skips every event produced before
it booted. No error. The team thinks the pipeline is broken; it is doing exactly
what it was configured to do.

**`poll()` returns three things, not one.** `None` (timeout), an error/event
object, or a message. Treating "not None" as "I have data" means `.value()` on an
event object — a crash on the rare path that survives testing and fails later.
Honest note: `_PARTITION_EOF` is off by default (`enable.partition.eof=false`),
so that sub-branch is defensive; the outer `msg.error()` check is live and
necessary.

**SIGTERM is not KeyboardInterrupt.** `except KeyboardInterrupt` catches SIGINT —
Ctrl-C. Every orchestrator stops a container with **SIGTERM**, and Python's
default disposition terminates the process outright: no exception, no `finally`,
no `consumer.close()`. The member never leaves the group, so the coordinator
holds its partitions until `session.timeout.ms`. **Measured from the consumer's
own timestamps: a 44.7 s gap**, against librdkafka's 45 s default — on every
deploy. The fix is a handler for both signals that flips a flag so the loop
finishes its current message and exits through `finally`.

**Gotcha:** this is invisible in local dev, because Ctrl-C is SIGINT and works
perfectly. It appears the day you containerise the worker — which is why the
signal handler belongs in the *same* change as the compose service.

**Kafka in Docker — bind vs advertise.** Clients **bootstrap**: they connect,
request metadata, and the broker replies "the leader is at address X" — then the
client dials X. So the advertised address must resolve **from where the client
stands**, and containers and your host are different networks.

- `KAFKA_LISTENERS` = **where I bind.**
- `KAFKA_ADVERTISED_LISTENERS` = **what I tell clients to dial.**

Answer: two listeners on two ports — `PLAINTEXT://kafka:19092` internal,
`PLAINTEXT_HOST://localhost:9092` for the host. Get it wrong and the connection
*succeeds and then hangs*, which is the confusing part. (Proven: a raw
`socket.create_connection(('kafka',9092))` reported "reachable" and was still the
wrong listener.)

**Gotchas that cost real time:**

- `__consumer_offsets` defaults to `replication.factor=3`. On a single broker the
  topic can't be created and **your first consumer hangs forever** with no clear
  error. Set the RF/ISR vars to 1.
- Mounting a volume at `/var/lib/kafka/data` without setting `KAFKA_LOG_DIRS`
  mounts a volume Kafka never writes to — data still dies with the container.
- JMX metric names normalize `.` and `_` together, so `order.dispatched` and
  `order_dispatched` **collide into one metric**. Pick one separator and never
  mix; it bites at Grafana time, not at create time.
- **KRaft:** Kafka 4.0 removed ZooKeeper entirely — metadata now lives in a Raft
  quorum of Kafka controllers, stored as a Kafka log. Every ZooKeeper compose
  file online is stale.

## 6.12 Level check — §6

1. "Kafka is persistent" is half an answer — what are the *two* durable things
   that make replay work?
2. A topic has 3 partitions and group `audit` has 5 consumers. What happens?
3. Two unrelated orders hash to the same partition. What does that cost, and what
   does it *not* cost?
4. `--from-beginning` on a caught-up group — how many messages, and why?
5. Give the exact replay procedure and the one thing that makes it fail.
6. Why can't Kafka give exactly-once when the side effect is an SMS? What's the
   real recipe, and what's the underlying problem called?
7. Trace a message that throws every time: what happens to it, the partition, the
   messages behind it, and the lag metric?
8. Why must the DLQ publish be *flushed* before the commit?
9. Idempotence is on; you call `produce()` four times with the same payload. How
   many rows, and why isn't that a bug?
10. Why can a producer never synchronously return "delivered = true"?
11. You dispatched with the broker down and got a 200. Where did the event go,
    and what does Postgres believe?
12. What does the outbox close that post-commit publishing cannot?
13. `group.id = f"notifications-{os.getpid()}"` — what breaks, and when do you
    find out?
14. Worker restarts cleanly with Ctrl-C but stalls ~45 s per restart in Docker.
    What's the bug, and what is 45 actually measuring?

---
---

# 7 — The production surface

## 7.1 Auth — authentication, then authorization

**Authentication = who are you (401). Authorization = what may you do (403).**
Mixing the two codes is a red flag.

**Sessions vs JWT — the trade I had to make:**

```
 SESSIONS (stateful)                    JWT (stateless)
 login → server stores {sid: user 7}    login → server SIGNS {sub, role, exp}
 request + cookie → DB/Redis lookup     request + Bearer → verify signature,
   per request                            no lookup
 revoke = delete the session ✅         revoke = hard ❌ (valid until exp)
 needs shared session storage ❌        any replica verifies independently ✅
```

I chose **JWT** because the API is horizontally scaled: any of three replicas
must be able to verify a caller with no shared session store. `HS256`, expiry
from config, and **the token is verified — signature *and* `exp` — never
decoded-without-verification**, which is the classic JWT hole: the payload is
base64, not encrypted, so anyone can read it and only the signature makes it
trustworthy.

**One deliberate deviation from pure statelessness:** `get_current_user` loads
the user row rather than trusting the token's claims wholesale. A token stays
valid until it expires, so a user deleted or demoted a minute ago would otherwise
keep full access for the rest of the token's life. That's a lookup per request I
chose to pay.

**Passwords:** bcrypt directly (passlib is unmaintained and breaks against bcrypt
4.x). Slow hashing is the point — it turns a leaked table into an expensive
brute-force, which is why SHA-256 is wrong for passwords. `checkpw` is
constant-time, so a wrong password costs the same as a right one and leaks no
timing signal.

**Gotcha worth telling:** bcrypt silently truncates past **72 bytes** — two
different long passwords would hash identically. I reject instead of truncating,
so the limit is visible rather than a silent security downgrade.

**The authorization model — and the guard the state machine couldn't give me.**
`transition()` answers "is `PENDING → DELIVERED` a legal move?" It does not
answer "may *this caller* make it?" So `assert_may_change_status` is a second,
orthogonal guard:

| Role | May |
|---|---|
| `ops` | anything, including cancelling |
| `rider` | advance **only** orders assigned to them; never cancel |
| `customer` | place orders; may not touch status at all |

Roles cannot be self-assigned — registration always creates a customer, and
promotion is an operator action.

**Soundbite:** "Status changes pass two orthogonal guards: the move must be
*legal* — a state machine question — and the caller must be *permitted* — an
identity question. A customer marking their own order delivered is a legal edge
by the wrong actor, and a state machine alone can never catch that."

## 7.2 Idempotency keys — making a POST retry-safe

**The problem is the ambiguous timeout.** A client POSTs an order, times out, and
has no way to know whether the first attempt landed. Retry and you get a second
order; don't retry and you may have none.

```
 client generates key K ──► POST /orders   Idempotency-Key: K
 server: claim K in Redis with SET NX      (atomic — two concurrent retries
   ├─ claimed  → run the request, cache     cannot both decide they're first)
   │             the response against K
   └─ present  → in-flight? 409 : replay the STORED response
 client retries with the SAME K → original result, no duplicate order
```

Details that matter, all of them decisions:

- **Opt-in**: POST only, and only when the header is present. A caller that
  doesn't care pays nothing.
- **`SET NX` claims the key *before* the work**, so two concurrent retries can't
  both believe they're the first attempt. A still-running first attempt returns
  **409 IDEMPOTENCY_IN_PROGRESS** rather than double-executing.
- **Failures aren't cached.** A response ≥ 400 deletes the key — a retry after a
  500 should genuinely re-run.
- **24 h TTL** — longer than any sane client retry window.
- **Fails open** on a Redis error: without Redis we can't dedupe, but refusing
  traffic would be worse. The duplicate that slips through is exactly why the
  analytics consumer dedupes independently — defence at both layers.

**Gotcha (the implementation trap):** in `BaseHTTPMiddleware` the response is a
*stream*; `response.body` isn't populated. You must drain `body_iterator` — and
draining **exhausts** it, so the response has to be rebuilt or the client gets an
empty body.

**Soundbite:** "A timeout is ambiguous, so clients retry POSTs with an
idempotency key and the server replays the stored response instead of
re-executing. The claim is a Redis `SET NX` taken before the work, so concurrent
retries can't both run; an in-flight duplicate gets a 409 rather than a
half-finished result; and errors aren't cached, because a retry after a 500
should really re-run."

## 7.3 Config, exceptions, and the middleware chain

**Centralized config.** One pydantic-settings `Settings` object reads everything
from env. Nothing hardcodes a URL. A field with no default is **required**, so a
missing `DATABASE_URL` fails startup loudly instead of silently running against
the wrong database.

**Soundbite:** "All config is one settings object read from env. Local reads
`.env`; Docker and CI inject their own — so moving environments is a config
change, not a code change. It's also the test seam: conftest sets the test
database and Redis URLs *before* the app imports."

**Gotcha:** `settings = Settings()` runs at **import time**, so test env vars must
be set before the first import that pulls it in. Same import-time seam
everywhere: a module-level client is bound once, at import.

**Gotcha:** `.env` is gitignored; `.env.example` is committed as the template.

**One error envelope.** A base `DeliverIQError` carries `status_code` + `code`;
each domain error subclasses it (`OrderNotFound` 404, `NoPendingOrders` 404,
`RiderUnavailable` 409, `InvalidTransition` 400). **One** handler registered on
the base covers every current and future subclass, returning
`{"error": CODE, "message": …}`. No stack traces leak.

**Why the service raises, not the router:** `pick_next_order` used to return
`None` for two different failures — no pending orders vs orders-exist-but-no-rider
— and the router collapsed both into a vague 404. The service is the only layer
that knows *why* it failed, so it raises the specific exception and the caller
gets the right code.

**Gotcha:** don't pre-invent exceptions for conditions you don't have. Validation
is already 422, generic bugs are 500. Each custom exception lands with its
feature, so none is dead code.

**Middleware order is a decision, not an accident.** FastAPI runs middleware in
**reverse registration order**. Effective order per request:

```
 request_id → rate limit → idempotency → metrics → route
```

- **request_id outermost**, so every log line — including a 429 — carries a trace
  id. If it ran inner, the rate limiter's own logs would be uncorrelated.
- **rate limit before idempotency**, so a flood of replayed keys is still
  throttled.

## 7.4 Structured logging and request correlation

**Why JSON, not `print`.** A log aggregator can't filter a dead string. Emitting
`{"level","logger","message","request_id",…}` makes every field queryable —
"show me all ERROR lines for request X" becomes a real query. Production logs are
data, not prose.

**Why a request_id.** Under load, hundreds of requests interleave in one stream.
A per-request UUID stamped on every line pulls out just that request's trail, and
it goes back to the client as `X-Request-ID` — a user reporting a bug can quote
it and you find their exact request.

**Why a contextvar, not a global ⭐.** Async interleaves many requests on one
thread. A plain global would be overwritten by whichever request touched it last
and ids would bleed across requests. A `ContextVar` holds a separate value **per
async context** — that isolation is the entire reason contextvars exist.

**Gotcha:** log lines emitted *outside* any request (startup, file-watch events)
have `request_id: null`. That's correct, not a bug — null means "not inside a
request."

**Gotcha:** clear and replace the root logger's handlers in `setup_logging()`, or
you get double lines — uvicorn's text handler plus your JSON one.

## 7.5 Metrics, and health vs readiness

**What to measure: the things an on-call engineer would page on** — request rate,
error rate, latency histograms, dependency status, Kafka published-vs-delivered,
rate-limit rejections, idempotent replays, and dispatch outcomes labelled
`assigned` / `no_pending_orders` / `no_rider_available`. That last split matters:
**a supply problem and a demand problem need opposite responses.**

**Cardinality is the thing to say out loud.** Every distinct label combination is
a separate time series held in memory by both the app and Prometheus. So route
labels use the **route template** (`/orders/{order_id}`), never the raw path,
which would mint one series per order id forever; unmatched paths collapse into
one bucket so a 404 scanner can't create series either.

**Two more deliberate choices:** histogram buckets are tuned to this API's shape
(10 ms–1 s, because dispatch does real DB work under lock) rather than the
library default — p99 can only ever be reported to the nearest bucket edge. And
`dependency_up` is a **Gauge**, 0/1 per dependency, so one alert rule covers all
of them.

**`/health` vs `/ready` — separate on purpose:**

| | `/health` (liveness) | `/ready` (readiness) |
|---|---|---|
| Question | "restart me?" | "route traffic to me?" |
| Cost | trivial, zero dependencies | round-trips Postgres, Redis, Kafka |
| Failure | container restarted | taken out of rotation, 503 naming the dep |

**Soundbite:** "Liveness and readiness answer different questions, so they're
different endpoints. A liveness probe that depends on Redis turns one cache blip
into an orchestrator restarting the entire fleet. Readiness actually round-trips
each dependency — a connection pool can look healthy while the server behind it
is gone — and returns 503 with a per-dependency breakdown so the failing one is
named, not guessed. The Kafka check uses a short-timeout metadata call, because a
readiness probe that blocks is itself an outage."

**Fail-open vs fail-closed, decided per dependency.** The rate limiter fails
**open**: a protective control must not cause the outage it exists to prevent.
For an auth or payment control the trade-off inverts. Saying "I decide this per
dependency" is the answer; "fail open" alone is not.

## 7.6 Docker and Compose — environment as code

**What Docker solves.** Your app needs a specific Python and dozens of pinned
packages; another machine has different ones. Docker ships the app **together
with its environment** as one sealed unit. **Image** = the read-only blueprint
(a class); **container** = a running instance (an object); **Dockerfile** = the
recipe.

**Layer caching is why the Dockerfile is ordered the way it is:** copy
`requirements.txt` and install **before** copying code, so a code edit doesn't
invalidate the dependency layer and reinstall everything.

**Container networking — the bug worth telling.** Each container has its own
network namespace, so `localhost` inside it means *the container*, not the host.
Alembic was reading a hardcoded `localhost` URL from `alembic.ini` and migrations
failed with "connection refused" inside the container. Fix: `env.py` prefers
`DATABASE_URL` from the environment. Same config-from-environment principle the
app already used.

**Compose removes that entire class of problem:** API, Postgres, Redis and Kafka
run as containers on one network and address each other **by service name**
(`db:5432`, `redis:6379`, `kafka:19092`). No `host.docker.internal`, no opening
host services to Docker's subnet, and the stack runs identically on any machine.

**Started ≠ ready.** `depends_on` alone waits only for the container to *start*.
Postgres takes a moment before it accepts connections, so `db` has a healthcheck
(`pg_isready`) and dependents gate on `condition: service_healthy`. Three
conditions, three meanings:

| Condition | Guarantees |
|---|---|
| `service_started` | the process launched — nothing more |
| `service_healthy` | its healthcheck passes (a real round-trip) |
| `service_completed_successfully` | a one-shot job finished and exited 0 |

**Reproducible from empty ⭐.** `docker compose down -v` wipes every volume, and
"clean and ready" is only true if **every** setup artifact is rebuilt by code on
the next `up` — not by remembered manual commands, which is the tribal knowledge
that rots. Three artifacts needed it:

- **Schema** → one-shot `migrate` job (`alembic upgrade head`), gated on db
  healthy.
- **The pytest database** → a Postgres init-script in
  `/docker-entrypoint-initdb.d/`, which runs **once on a fresh data dir** —
  exactly the `down -v` case.
- **Kafka topic** → one-shot `kafka-init` (`--create --if-not-exists
  --partitions 3`), gated on the broker being **healthy**, not started.

**Soundbite:** "The whole stack reproduces from an empty volume with one command:
schema via a one-shot Alembic job, the test database via a Postgres init-script,
Kafka topics with pinned partition counts via a one-shot admin job, all ordered
by health-gated `depends_on`. Making the environment declarative is what lets me
trust `down -v` as a real reset button."

**Gotcha:** init-scripts run **only** when the data directory is empty, so a warm
restart skips them — correct, but it means they're for first-init bootstrap only;
schema *changes* belong in migrations. And one-shot jobs must be idempotent
(`--if-not-exists`, `upgrade head`) or warm starts break.

**Gotcha (version-specific, cost me time):** the Postgres 18 image expects its
volume at `/var/lib/postgresql`, not the older `/var/lib/postgresql/data` —
wrong path and the container exits immediately.

**Gotcha (the one that had no error at all):** I once ran a host-native Postgres
on 5432 *and* a Compose Postgres remapped to 5433, with `.env` pointing at 5432.
pytest and the host app wrote to one database while the `api` container wrote to
the other. Two fully-migrated schemas, diverging silently. The tell was a sequence
reset that "didn't take" — I was reading a different database than I wrote to.
**A value that won't change after you set it is the classic signature of a
read/write split across two backends.** The fix wasn't cleaning data, it was
decommissioning the redundant instance and making Compose canonical.

## 7.7 Testing — and what makes a test a test

**These are integration tests.** Each drives a real HTTP request through the full
stack — endpoint → service → Redis → Postgres → assert on the response — against
real infrastructure rather than mocks. That's deliberate: the bugs in this
project live in the **seams** (a BUSY rider removed from the Redis index, a rider
relocated on delivery), not inside any single function.

**Isolation is the discipline:** a throwaway test database, a separate Redis
logical DB (15, not 0), and an **autouse fixture** that drops/recreates tables and
`flushdb()`s before every test. Result: repeatable and order-independent. The
`id == 1` assertion in the create test only holds because the reset wiped prior
rows — a free proof the isolation works.

**Two override mechanisms, and knowing why is the signal ⭐.** Postgres is
injected via `Depends(get_db)`, so I use FastAPI's `app.dependency_overrides`.
Redis is a **module global** imported directly — there's no dependency to
override, so the seam is an env var read at **import time**, set in conftest
*before* the app imports. Recognizing that a global needs a different override
strategy than an injected dependency is the part most people miss.

**Kafka publishing is patched at the *call sites*, not the definition site.**
Every module that did `from … import publish_event` holds its **own binding**, so
patching the definition leaves the real function in place — the test passes and
the event still reaches the broker. The fixture records calls, so publishing is
*asserted* rather than merely silenced, and it fails if any code path constructs a
real producer.

**Coverage is a map, not a grade.** 86% isn't a target hit — the useful part is
the **Missing** column, which names what you forgot to test. Chasing 100% means
testing defensive branches that aren't worth it yet.

**The methodological lesson worth telling ⭐ — a test without a working control
proves nothing.** To prove at-least-once redelivery I monkeypatched
`Consumer.commit` to kill the process. It **silently did nothing**:
`confluent_kafka.Consumer` is a C extension type whose attributes can't be
reassigned. The patch failed, the consumer committed normally, and the
"redelivery" I observed on the next run was simply a **first** delivery. Green
result, zero evidence. The fix was a delegating proxy — an ordinary Python object
that forwards everything and dies on `commit`.

Three separate green results lied on that one day: the immutable-type patch that
never fired; a **backgrounded** process inheriting SIGINT-ignored, which made
"Ctrl-C is broken too" an artifact of `&`; and piping a timed run into `grep`,
which measured the `timeout 90` window rather than the event. **The habit that
catches all three: run the control — make the thing you think you're detecting
*not* happen, and confirm your test notices.**

## 7.8 CI, and the load numbers

**CI** runs lint, migrations and the full suite on every push, bringing up
infrastructure from **the same `docker-compose.yml` used locally**, so the two
can't drift. It works without code changes because config is env-driven (§7.3) —
CI just points `DATABASE_URL`/`REDIS_URL` at its service containers.

**I have no load number I'm willing to quote, and that is deliberate.** The old
figure — "~123 RPS, p99 220 ms" — came from a Locust run that only hit
unauthenticated `POST /orders`. It measured a plain INSERT: no auth, no matching,
no row locks, no Kafka. The number was real; the claim attached to it was not, so
I retired it (§9.5).

The load profile now drives `POST /orders/dispatch` — the **claim** — under
contention with a seeded fleet, which is the number anyone actually cares about.
It has not been re-run, so there is nothing to report yet. Say exactly that: *"I
retired that figure because it measured the wrong endpoint, and I haven't
re-measured."* **An honest absence beats a confident irrelevance**, and an
interviewer who probes a quoted number is testing whether you know what it
covered.

**Percentiles, plainly:** p99 = 220 ms means 99% of requests finished within
220 ms. Percentiles beat averages because the average hides the slow tail, and
the tail is what users feel.

**Gotcha, and it's the whole point:** always name *which configuration and which
endpoint* a load number came from. A big RPS with the limiter silently off, or a
low one with it on, is a misleading number — and so is a fast one measuring an
endpoint that does none of the work the system is interesting for. Running it
twice, limiter on and off, is what makes either number mean something: with the
limiter **on**, 97% of requests returned 429, which measures the *limiter*, not
the app.

## 7.9 Level check — §7

1. Sessions vs JWT for a 3-replica API — two pros and the killer con of each.
2. Why does `get_current_user` load the user row instead of trusting claims?
3. Why bcrypt and not SHA-256? What happens past 72 bytes?
4. 401 vs 403 — give a DeliverIQ example of each.
5. Why is the idempotency claim a `SET NX` *before* the work? Why aren't errors
   cached?
6. Why must request_id be a contextvar and the outermost middleware?
7. Why route templates instead of raw paths in metric labels?
8. `/health` vs `/ready` — what breaks if you merge them?
9. `service_started` vs `service_healthy` vs `service_completed_successfully`.
10. Why patch Kafka at the call sites rather than the definition site?
11. What's a control, and what did its absence let you conclude falsely?

---
---

# 8 — Scaling it up (the system-design conversation)

## 8.1 The framework — never jump to boxes and arrows

```
 1. REQUIREMENTS (5 min)  functional + non-functional. ASK, don't assume:
                          "orders/day? cities? peak factor? latency SLO?"
 2. ESTIMATE (2 min)      QPS, storage, the hot path — envelope math
 3. API + DATA MODEL      core endpoints, tables, the ids everything hangs on
 4. HIGH-LEVEL DIAGRAM    client → LB → services → stores → async pipeline
 5. DEEP DIVE             1–2 bottlenecks — where Levels §5–6 knowledge is spent
 6. WRAP                  failure modes, monitoring, what you'd build first
```

Every choice stated as a **trade-off** — "X buys me A at the cost of B, and here
A matters more because…" That habit *is* the senior signal.

## 8.2 Envelope math — numbers to carry in your head

```
 LATENCY                          THROUGHPUT
 RAM access          ~100 ns      1M requests/day ≈ 12 rps average
 SSD random read     ~100 µs      peak ≈ 3–10× avg → plan ~50–100 rps
 same-DC round trip  ~0.5 ms      1 Postgres node: ~1k–10k simple qps
 Redis op (network)  ~0.5 ms      1 API instance: ~100s of rps (I/O bound)
 Postgres indexed    ~1–5 ms      1M orders × ~1 KB ≈ 1 GB/day ≈ 365 GB/yr
 cross-region RTT    ~50–150 ms
```

The point isn't precision — it's catching absurdities: "that's 12 rps, we don't
need Kafka for intake," or "100M location pings/day can't hit Postgres raw."

## 8.3 Replication and sharding

**Replication** copies all data: leader takes writes, followers replay the WAL and
serve reads. Buys read scaling and HA.

**Gotcha — the classic bug:** async replication means lag, so a user writes and
their next read hits a replica and their write "disappears." Fix:
**read-your-writes** — route that user's reads to the leader briefly. Sync
replication trades write latency for zero-loss failover.

**Sharding** splits data when *writes* or size outgrow one machine. The shard key
decides everything — you want the hot path to hit one shard, so **DeliverIQ would
shard by city**: dispatch is city-local anyway.

**Gotcha:** `hash(key) % N` reshuffles almost every key when you add a node —
the same modulus problem as Kafka repartitioning (§6.4). **Consistent hashing**
places nodes and keys on a ring so adding a node moves only the keys in one arc
(~1/N), with virtual nodes for balance. The tax on any sharding is cross-shard
JOINs and transactions.

## 8.4 CAP — answer it per feature, never in the abstract

CAP only bites **during a partition**, and P is not optional — networks fail. So
you choose: **CP** (refuse or stall, stay correct) or **AP** (keep answering,
possibly stale).

**Soundbite:** "I answer CAP per feature. Dispatch and payments must be CP — I'd
rather fail a request than double-assign a rider. Rider location tracking is AP —
a two-second-stale location is fine and unavailability is worse. PACELC is the
grown-up version: even without a partition, replication trades latency against
consistency."

## 8.5 Resilience — the stack, in order

1. **Timeout everything.** An un-timeouted call turns a slow dependency into your
   own outage as connections pile up waiting.
2. **Retry with exponential backoff + jitter** — only on idempotent operations.
   Jitter stops every client retrying in lockstep and re-stampeding a recovering
   service.
3. **Circuit breaker** — CLOSED → (failures ≥ threshold) → OPEN → (cooldown) →
   HALF-OPEN → CLOSED. Fail fast instead of hammering something that's down.
4. **Graceful degradation** — decided per dependency, as in §7.5.

DeliverIQ has (1) — short timeouts on the readiness probe and producer — and (4);
(2) exists as the bounded rider-level retry (§5.5). A circuit breaker is honest
"what I'd add next" material.

## 8.6 Distributed transactions — sagas, not 2PC

A checkout spans services with no shared transaction. **2PC** blocks everything on
the slowest or dead participant. The workhorse is the **saga**: a chain of local
transactions, each with a **compensating action**.

```
 create order ──► charge payment ──► assign rider ──► done ✅
      │                │                  ✗ fails
      │                ◄── REFUND (compensate)
      ◄── CANCEL order (compensate)              → eventual consistency
```

**Soundbite:** "Across services I'd use a saga — local transactions plus
compensations — rather than 2PC, which blocks on a dead coordinator. Compensation
isn't rollback: the charge *happened*, then a refund happened, so intermediate
states are visible and must be modelled explicitly. And every step and every
compensation has to be idempotent, because the saga itself retries."

**Event sourcing, in one paragraph:** CRUD stores current state; event sourcing
stores the sequence of facts and derives state by replay — perfect audit log,
time travel, natural Kafka fit, at the cost of projections, snapshots and event
versioning. The middle path most teams take is CRUD tables **plus** an
append-only events/outbox table.

## 8.7 The worked example — "design a food-delivery dispatch system"

This is DeliverIQ scaled up, which is why it's the design prompt to steer toward.

**Requirements:** create orders, track live rider locations, assign the best rider
within ~5 s, order lifecycle, notifications. Say 1M orders/day, 100k riders, 20
cities. An order goes to **exactly one** rider (CP); locations may be stale (AP).

**Envelope — and the punchline:** 1M orders/day ≈ 12 rps (peak ~100). Locations:
100k riders × one ping per 5 s ≈ **20k writes/s**. *The hot path is locations,
not orders* — and noticing that is the whole point of doing the math.

**Data model:** `orders`, `riders`, `users` in Postgres, sharded by **city**.
Locations in **Redis geohash cells**, not Postgres — 20k writes/s of ephemeral
data is precisely what Redis is for.

```
 customer app ─► LB ─► ORDER SVC ─► Postgres (orders, by city)
                          │ outbox → Kafka "order.events"
 rider app ────► LB ─► LOCATION SVC ─► Redis geohash cells (TTL'd)
                       DISPATCH WORKERS (per city, N instances)
                         SELECT … WHERE status='PENDING' ORDER BY priority
                           LIMIT 1 FOR UPDATE SKIP LOCKED       ← §5.3
                         → nearby riders from Redis             ← §4.2–4.3
                         → claim rider (lock / atomic SREM)
                         → commit → outbox event
 Kafka ─► notifications │ analytics │ audit  (independent groups)  ← §6.5
```

**Deep dives to offer:** the assignment race (§5.3–5.5); location write volume
(Redis, with TTL as liveness — a rider whose key expires stops being matchable);
fairness vs ETA (§4.3); surge and backpressure (priority aging, §4.1); a dispatch
worker dying (its locks die with its transaction, another worker picks the row
straight up).

**Wrap:** alert on assignment-latency p99 and unassigned-order age; read replicas;
build the single-city monolith first and shard when one city's write volume
demands it.

---
---

# 9 — The audit: what was wrong, and what I did about it

This section used to list seven known flaws. Then I audited every source file
line by line and found **nine more** — including four endpoints that had no
authentication at all. Thirteen are now fixed; six are not.

That story is worth more in an interview than the original list was, because it
demonstrates the thing the list only claimed: that I look for my own defects and
then close them. Lead with it.

**Governing rule, unchanged:** a gap is only "owned" when you can state **both
the flaw and the fix**. For the fixed ones, state the flaw, the fix, and *why the
fix is shaped the way it is* — that last part is where the signal is.

**One command re-checks all of it:** `./scripts/verify.sh` — config guard, lint,
71 tests, and a live smoke test of every auth boundary against a real server,
including an attempt to authenticate with a token forged using the old shipped
secret.

## 9.1 The four auth holes ⭐ (lead with this one)

The project's role table was enforced on *write* paths that looked dangerous and
skipped on ones that didn't. Four endpoints shipped open:

| Endpoint | Was | Now |
|---|---|---|
| `PATCH /riders/{id}/location` | anonymous | ops, or the rider themselves |
| `POST /orders` | anonymous, `customer_id` from the body | authenticated, id from the token |
| `GET /orders`, `GET /orders/{id}` | anonymous, every order | scoped by role |
| `GET /riders`, `GET /riders/{id}` | anonymous, full roster + positions | ops, or the rider themselves |

**The worst one, and why it's the worst.** `PATCH /riders/{id}/location` writes
through to the Redis geohash index, and **that index is the matching engine**.
Anyone who could call it could teleport the whole fleet onto one coordinate and
defeat the distance filter, the fairness band and the two-phase claim in a single
unauthenticated request. It shipped open because it reads like a profile update.
The lesson to say out loud: *"who may write this field" and "who may decide
dispatch outcomes" turned out to be the same question, and I had not noticed they
were.*

**The ownership hole.** `POST /orders` took `customer_id` from the request body,
so anyone could place an order as anyone — and the system therefore had no
trustworthy notion of ownership at all, which is what every read-scoping rule
depends on. The fix removes the field from the schema entirely rather than
validating it: **a field the server must check against the token is a field the
client should not be sending.**

**The 403-vs-404 pair ⭐** — my favourite detail here, because the two endpoints
point opposite ways *on purpose*:

- `GET /orders/{id}` returns **404** for an order you may not see. A 403 would
  confirm the id exists and let you enumerate orders one request at a time.
- `PATCH /riders/{id}/location` returns **403 before checking existence**. Here
  the rider id is not the secret, and authorising first stops the 404-vs-403
  difference from mapping the fleet.

Same mechanism, opposite answers. The deciding question is *which fact is worth
hiding* — and being able to argue both directions is the point.

**Soundbite:** "My audit found four endpoints with no auth at all. The worst let
anyone move any rider, and since rider positions are the matching index, that was
full control of dispatch from an unauthenticated request. I fixed the authz, but
the more useful takeaway was why it happened: it looked like a profile update, so
I'd classified it by shape instead of by blast radius."

## 9.2 The signing key had a working default ⭐

`JWT_SECRET` defaulted to `dev-only-change-me` — a value published in the
repository — so anyone with the source could mint an ops token, and every
`require_ops` guard in the project was decorative. Not just in production: in
*every* environment, because nothing anywhere overrode it or objected.

**The fix is the interesting part.** I removed the default rather than improving
it. A better default would still have been a default, and **a control that can be
skipped by forgetting a variable is not a control.** The app now refuses to
import without a secret, rejects known placeholders by name, and enforces a
32-**byte** floor — bytes, not characters, for the same reason bcrypt's 72-byte
limit is counted in bytes.

Two operational details worth having ready:

- Every process needs it, `migrate` included, because `alembic/env.py` imports
  `app.core.database` → `app.core.config`. One `x-app-env` YAML anchor delivers
  it to all five services; a secret pasted five times is a secret that ends up
  wrong in one of them.
- Compose interpolates `${JWT_SECRET:?}` when the **file** is parsed, so even
  `docker compose up db` fails without it. That is why CI sets it at job level
  rather than on the pytest step.

**Soundbite:** "The signing key had a working default, which meant every
authorization guard in the project was decorative. I removed the default instead
of improving it — the app now refuses to boot without a real secret, because a
control you can skip by forgetting an environment variable isn't a control."

## 9.3 Correctness and availability

**Idempotency keys were global.** The cache key was `idempotency:{key}` with no
caller in it, so two users who both sent `Idempotency-Key: retry-1` collided and
the second received *the first user's response body*. A cross-tenant leak, not a
correctness nit. Now namespaced by the **verified** token subject, and bound to a
hash of method+path+body — so the same key with a different payload is a 422
instead of a confidently wrong replay.

**The middleware was blocking the event loop ⭐.** Both middlewares used the
*synchronous* Redis client while being `async def`. The routes were fine — they
are sync `def`, so FastAPI runs them in a threadpool — but the middleware chain
runs on the loop, so every request stalled every other in-flight request on the
process. The irony worth admitting: §7.4 sells the `ContextVar` on the grounds
that "async interleaves many requests on one thread," and the middleware was
preventing exactly that. Now two clients: async for middleware, sync for services.

**"Fail open" was only half-built ⭐.** Both middlewares catch `redis.RedisError`
and deliberately fail open, and that reasoning is sound. But there were no socket
timeouts — so it only caught a *refused* connection. A Redis that accepts and
then **hangs**, which is the more common production failure, raised nothing and
blocked forever. The protective control failed in exactly the mode it was written
to survive. A timeout is what turns a hang into an error the fallback can act on.

**The pool sizing was fiction.** §5.6 quotes "3 replicas × 20 = 60" — the code
called bare `create_engine()`, whose default is 5 + 10. Now configured
explicitly, with `pool_pre_ping` so a Postgres restart doesn't hand out dead
connections until each one fails a real query.

**Soundbite:** "The one I'd flag hardest is that my fail-open only caught refused
connections. Redis hanging is the likelier failure and it had no timeout, so the
degradation path I'd written a comment about could never actually run. Adding
socket timeouts is what made the design I'd described real."

## 9.4 Keying, pipelining, and measuring

- **The rate limiter was opt-out.** It keyed on `X-API-Key or client.host`, so
  rotating a header you control minted a fresh bucket per request. Now: verified
  `sub` first, then `X-Forwarded-For` **only** behind an explicit
  `trust_proxy_headers` flag (trusting it unconditionally is the same bypass in a
  different header), then the peer address. The key is hashed so a bucket can
  never leak an email into Redis or a log.
- **Matching did 2 un-pipelined Redis round trips per candidate**, inside the
  dispatch hot path, *while holding a Postgres row lock on the order* — so
  per-candidate latency was lock-hold time. One pipeline now.
- **Idempotent replays bypassed the metrics middleware**, which sat inside
  idempotency: `idempotent_replays_total` counted them while
  `http_requests_total` did not, and the two metrics disagreed about how much
  traffic the service had served. Moving metrics outermost fixed the count — and
  **broke the label**, because `scope["route"]` is only populated once the router
  matches. Counting replays under `__unmatched__` is a worse lie than a missing
  count, so the route template is now resolved directly. Good thing to tell:
  *the fix needed a second fix, and a test caught it.*
- **Request ids were minted unconditionally**, discarding any upstream
  `X-Request-ID`, so a trail could not be followed across a hop — which is the
  entire point of having one. Now adopted when well-formed, and validated first,
  because that value goes straight into every log line for the request.
- **The idempotency in-flight lock was 30s**, shorter than a slow request, so the
  claim could expire mid-flight and let a retry double-execute — precisely what
  the middleware exists to prevent.

## 9.5 Still open — the genuine remaining gaps

Volunteer these. They are the honest half of the story and each one has a fix I
can describe.

**No transactional outbox.** A crash between `db.commit()` and the Kafka publish
loses the event permanently (§6.9). **This is the dual-write problem, by name** —
the most important thing still outstanding. *Fix:* an `outbox` table written
inside the order's transaction plus a relay (polling, or WAL-tailing via
Debezium), accepting the at-least-once publishing that the existing idempotent
consumers already absorb.

**Durability theatre.** One Kafka broker with RF=1 means `acks=all` provides no
real durability — "all" is one replica. *Fix:* three brokers, RF=3,
`min.insync.replicas=2`. **The producer config is already correct; the topology
isn't**, which is the whole point.

**The dispatcher is still O(n log n) per call.** Every dispatch reloads all
pending orders and rebuilds the heap; the `heappop` is O(log n) but the build
dominates. The README wording is corrected. *Fix:* push the ordering into the
database (`ORDER BY priority LIMIT 1 FOR UPDATE SKIP LOCKED`) and drop the
in-process heap entirely.

**No benchmark numbers I'm willing to quote.** The old "~123 RPS, p99 220 ms"
came from a Locust run hitting unauthenticated `POST /orders` — it measured a
plain INSERT, not matching, locking or Kafka. The load profile now drives the
dispatch **claim** under contention, but **I have not re-run it**, so I have no
number. Say that rather than quoting the old one: *"I retired that figure because
it measured the wrong endpoint, and I haven't re-measured yet."* An honest
absence beats a confident irrelevance.

**The concurrency proof isn't in CI.** `scripts/race_test.py` is a manual script,
so the project's headline correctness property is not regression-protected. No
test asserts an event round-trips a real broker either — publishing is patched at
the call sites. *Fix:* the race test as a CI job with `--scale api=3`, and one
end-to-end produce-and-consume test.

**No token revocation.** §7.1 names revocation as JWT's weakness and offers the
per-request user lookup as mitigation — that covers *deleted* and *demoted* users
only. A stolen token, a password change, or "log me out everywhere" all stay
valid until `exp`. *Fix:* a `jti` claim plus a Redis denylist with a TTL matching
the token's remaining life. Redis is already a hard dependency, so it costs no
new infrastructure.

**No FK on `orders.customer_id`.** Ownership is enforced in the handler but not
by the database. *Fix:* a migration adding the constraint — deferred because
applying it to existing rows needs a decision about orphaned demo data.

## 9.6 Known-and-deliberate, not gaps

State these as choices, not omissions: the fairness band Δ is a fixed constant
rather than per-city-tuned; `orders_today` resets on **UTC** midnight rather than
the business timezone; there's no rider-penalty tracking (the state machine
deliberately keeps order-state and rider-penalty as independent state spaces,
§4.4); and there's no circuit breaker — timeouts and a bounded retry cover the
cases this system actually has.

---
---

# 10 — Drills

## 10.1 Cold-open drill (do these unprompted)

- [ ] Deliver the §0.1 opener cold, in under twenty seconds
- [ ] Volunteer the O(n log n) correction (§9.5) before being asked
- [ ] Volunteer the missing outbox (§9.5) before being asked
- [ ] Defend `SKIP LOCKED` — **including what it costs** (§5.3)
- [ ] Answer "how would you make this production-ready?" using §9.5 as the answer
- [ ] Sketch the architecture from memory, naming a trade-off at every arrow
- [ ] Tell the §5.5 story with the numbers: 5/15 → 10/15, zero doubles

## 10.2 The six stories worth having ready

Every one is Situation → constraint → decision *and the alternative* → measured
result → what I'd change.

1. **The phantom assignments** (§5.4) — the lock was right, the mutation ordering
   was wrong; a session commits the whole unit of work.
2. **Correct but not live** (§5.5) — zero doubles and still only 5 of 15
   dispatching; measured, diagnosed, fixed, re-measured.
3. **The boundary cell** (§4.2) — a rider 10 m away invisible because I checked
   one geohash cell instead of nine.
4. **The 200 with the broker down** (§6.9) — `produce()` does no I/O, so it
   cannot fail; the event died in a memory buffer.
5. **The 44.7-second deploy stall** (§6.11) — SIGTERM is not KeyboardInterrupt,
   and the number was `session.timeout.ms`.
6. **The test that proved nothing** (§7.7) — a monkeypatch that silently didn't
   apply, and why you always run the control.

## 10.3 How to answer anything

- **Clarify → structure → answer → trade-off.** Restate the question, say the
  shape of your answer ("two parts: the mechanism, then when it breaks"), fill it
  in, then name the alternative you rejected and why.
- **No tool is "better," it's better *for* something.** "Redis over Memcached
  because sorted sets and geo" beats "Redis is fast." Every soundbite in this
  file is built that shape, deliberately.
- **Say "it depends," then immediately say on what.** "Pessimistic or optimistic?
  Depends on contention: hot dispatch queue → locks; rare profile edits →
  versions."
- **When you don't know, reason out loud from what you do know.** "I haven't used
  Cassandra, but it's AP and write-optimized, so I'd expect…" is worth more than
  a memorized fact.

## 10.4 Master checklist — can you, without notes…

- [ ] narrate the URL journey and name a failure mode at each hop (§1.2)
- [ ] fill the verb safety/idempotency table and justify POST for `/dispatch` (§1.5)
- [ ] explain 400 vs 422 vs 409 with a DeliverIQ example each (§1.4)
- [ ] explain N+1 and two fixes; name a partial index use here (§2.2, §2.4)
- [ ] explain why `create_all` can't replace migrations, and the import trap (§2.3)
- [ ] derive the token bucket's advantages *and* what `expire` really does (§3.2)
- [ ] explain why Lua is atomic and what race it removes (§3.3)
- [ ] explain the dual write, the phantom-cell bug, and reconciliation (§3.4)
- [ ] justify aging, and state the real complexity of your dispatcher (§4.1, §9.5)
- [ ] argue the fairness band against a blended score (§4.3)
- [ ] give the two failure semantics of the same `transition()` call (§4.4)
- [ ] draw the lost update and fix it both ways (§5.3)
- [ ] tell the unit-of-work trap and the claim-before-mutate rule (§5.4)
- [ ] tell the thundering-herd story with before/after numbers (§5.5)
- [ ] recite the statelessness checklist (§5.7) and WAL/MVCC (§5.8)
- [ ] contrast queue vs log; derive at-least-once from commit placement (§6.3, §6.7)
- [ ] explain the poison pill, the DLQ, and the flush-then-commit ordering (§6.8)
- [ ] sketch the outbox and say exactly which window it closes (§6.9)
- [ ] explain producer async delivery and why `delivered=true` is a bug (§6.10)
- [ ] justify JWT over sessions here, and the two orthogonal authz guards (§7.1)
- [ ] explain the idempotency claim, the 409, and the uncached failures (§7.2)
- [ ] explain metric cardinality and liveness vs readiness (§7.5)
- [ ] run the 6-step design framework with envelope math on a fresh prompt (§8.1–8.2)
- [ ] whiteboard the dispatch system with a trade-off at every arrow (§8.7)
- [ ] state the six remaining gaps in §9.5 *with their fixes*

*Every unchecked box is your next review target.*


