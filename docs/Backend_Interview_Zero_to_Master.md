# Backend Engineering — Zero to Master (SDE Interview Guide)

> The complete curriculum: from "what is a server" to staff-level system design.
> Format matches the project guide: **concept (why)** → **diagram (see it)** →
> **soundbite (say it out loud)** → **gotcha (what trips people up)**.
>
> **How the two docs fit together:**
> - **This file** = the *general* backend knowledge every SDE interview tests.
> - **[Interview_prep.md](Interview_prep.md)** = the *DeliverIQ-specific* deep
>   dives (token bucket §11, geohash §14, state machine §19, testing §23,
>   logging §25, Docker §35–42). Cross-referenced below as `→ IP §n`.
>
> **The path:**
>
> ```
> LEVEL 0          LEVEL 1          LEVEL 2           LEVEL 3            LEVEL 4
> Foundations  →   Core Backend  →  Data & Concurrency → Distributed  →  Master
> (what is a       (REST, SQL,      (indexes, ACID,      (Kafka, CAP,    (system design,
>  server, HTTP)    auth, ORM)       locking, caching)    scaling)        sagas, MVCC)
> zero experience  junior SDE       mid-level SDE       senior SDE       staff signal
> ```
>
> Rule of thumb: a junior interview lives in Levels 0–2. A mid-level interview
> lives in Levels 1–3. Senior+ interviews assume 0–3 and probe Level 4.

---
---

# LEVEL 0 — Foundations (assume nothing)

## 0.1 What a backend actually is

A **frontend** is what runs on the user's device (browser, mobile app). A
**backend** is a program running on a computer you control (a *server*), whose
job is to hold the truth: the data, the rules, the security. The frontend asks;
the backend decides and answers.

```
  USER'S DEVICE                     YOUR SERVER(S)
 ┌─────────────┐    HTTP request   ┌─────────────┐      SQL       ┌──────────┐
 │   Browser / │ ────────────────► │   Backend   │ ─────────────► │ Database │
 │  Mobile app │                   │  (FastAPI)  │                │(Postgres)│
 │             │ ◄──────────────── │             │ ◄───────────── │          │
 └─────────────┘    HTTP response  └─────────────┘     rows       └──────────┘
   renders UI        (JSON)          business logic                durable truth
```

Why can't the app talk to the database directly? Because the client is **enemy
territory** — anyone can modify a client and send anything. The backend is the
only layer you trust: it validates input, enforces rules ("you can't cancel a
delivered order"), and hides secrets (DB passwords never reach the client).

**Soundbite:** "The backend is the trust boundary. Clients can lie — the server
validates, authorizes, and owns the data. That's why business rules live
server-side even if the UI also checks them."

**Gotcha:** UI validation is UX, not security. Every check the frontend does
must be repeated on the backend, because attackers skip the frontend entirely
(curl straight to your API).

## 0.2 What happens when you type a URL (the classic opener)

`https://api.deliveriq.com/orders/3` — the full journey:

```
 1. DNS lookup        "api.deliveriq.com" → 203.0.113.7
    (phone book: domain name → IP address; cached at every layer)
                │
 2. TCP handshake     SYN ──► SYN-ACK ◄── ACK   (3-way; now a reliable pipe)
                │
 3. TLS handshake     agree on encryption keys; server proves identity
    (the S in HTTPS)  via certificate → everything after is encrypted
                │
 4. HTTP request      GET /orders/3 HTTP/1.1  + headers
                │
 5. Load balancer     picks one healthy backend instance  (Level 3 topic)
                │
 6. App server        FastAPI: middleware → router → handler → service
                │
 7. Database          SELECT * FROM orders WHERE id = 3  (index lookup)
                │
 8. Response          200 OK + JSON body travels all the way back
```

**Soundbite:** "DNS resolves the name to an IP, TCP gives a reliable connection,
TLS encrypts it, then HTTP carries the request. Server-side it passes a load
balancer, hits an app instance, which queries the database and serializes a JSON
response. Every one of those steps has a cache and a failure mode — that's
basically the whole backend syllabus in one question."

**Gotcha:** TCP guarantees *delivery and order* of bytes, not speed — that's why
it needs the handshake. UDP skips the handshake (fast, no guarantees) — used for
video, DNS queries, gaming. Interviewers love "TCP vs UDP": **TCP = reliable
ordered stream; UDP = fire-and-forget datagrams.**

## 0.3 Anatomy of HTTP — what's actually on the wire

HTTP is plain text: a request line, headers (key: value metadata), blank line,
optional body.

```
REQUEST                                RESPONSE
────────────────────────────          ────────────────────────────
POST /orders HTTP/1.1                 HTTP/1.1 201 Created
Host: api.deliveriq.com               Content-Type: application/json
Content-Type: application/json        X-Request-ID: 7f3a-...
Authorization: Bearer eyJhb...        X-RateLimit-Remaining: 98
                                      
{"customer_id": 1,                    {"id": 42,
 "value": 250.0, ...}                  "status": "PENDING", ...}
────────────────────────────          ────────────────────────────
 verb + path + version                 status code + reason
 headers = metadata                    headers = metadata
 body = the payload (JSON)             body = the payload
```

- **Headers** carry cross-cutting metadata: auth tokens, content type, caching
  directives, your own custom ones (`X-Request-ID` → IP §25).
- **The body** carries the data, almost always JSON for APIs: a text format of
  objects `{}`, arrays `[]`, strings, numbers, booleans, null.
- **HTTP is stateless**: each request stands alone; the server keeps no memory
  of the previous one. Any continuity (who's logged in) must ride along on every
  request — via a cookie or an `Authorization` header. This one property drives
  half of backend design (sessions, JWTs, and why servers scale horizontally).

**Soundbite:** "HTTP is a stateless text protocol: verb, path, headers, body.
Statelessness is the feature — because no request depends on server memory of
the last one, any instance can serve any request, which is what makes horizontal
scaling possible."

For verbs, status codes, path-vs-query params, and error envelopes → **IP §3**
(already excellent). One diagram worth adding — the status code decision tree:

```
                         Did the request succeed?
                          │yes              │no
              created something?      whose fault?
              │yes        │no         │client            │server
             201         200          │                   500
                              malformed shape?      (bug, crash,
                              │yes        │no        impossible state)
                             422          │
                                   resource missing?
                                   │yes        │no
                                  404          │
                                        auth problem?
                                        │yes        │no
                              401 (who are you?)     │
                              403 (you can't)   conflicts with state?
                                                │yes            │no
                                          409 (busy/dup)   400 (illegal
                                          429 (rate limit)  transition etc.)
```

## 0.4 Processes, ports, servers

A **server** is just a program in an infinite loop: listen, accept, respond.
Your machine runs many; **ports** are how one IP address hosts many programs —
Postgres owns 5432, Redis 6379, your API 8000. `localhost` (127.0.0.1) means
"this same machine."

```
        ONE MACHINE (one IP)
 ┌──────────────────────────────────┐
 │  :8000  uvicorn (your FastAPI)   │◄── HTTP clients
 │  :5432  postgres server process  │◄── SQL clients (your app, psql, DBeaver)
 │  :6379  redis server process     │◄── redis clients (your app, redis-cli)
 └──────────────────────────────────┘
```

**Soundbite:** "Postgres and Redis aren't libraries inside my app — they're
separate server processes my app connects to over a socket. That separation is
what gives shared state across many app instances." (→ IP §5, and it's why
`localhost` breaks inside Docker → IP §37.)

## 0.5 Level 0 self-test

1. Why must every frontend validation be repeated on the backend?
2. Walk through what happens when a browser requests a URL — name 6 steps.
3. TCP vs UDP in one sentence each. Which does HTTP use?
4. What does "HTTP is stateless" mean, and name two consequences.
5. What is a port? Why can Postgres and Redis share one machine?
6. Where do auth tokens travel in an HTTP request?

---
---

# LEVEL 1 — Core Backend (junior SDE)

## 1.1 REST resource design

REST models the world as **resources** (nouns) at URLs, manipulated with
standard verbs — instead of a zoo of RPC endpoints like `/getOrder`,
`/makeNewOrder`.

```
Collection:   /orders            GET (list)    POST (create)
Item:         /orders/42         GET (read)    PATCH (update)   DELETE
Sub-resource: /orders/42/events  GET
Action:       /orders/dispatch   POST (side-effecting verbs are POST)
```

Two properties define each verb — **memorize this table**:

| Verb   | Safe? (no side effects) | Idempotent? (N calls = 1 call) | Use            |
|--------|------------------------|-------------------------------|----------------|
| GET    | ✅                     | ✅                            | read           |
| POST   | ❌                     | ❌                            | create / action|
| PUT    | ❌                     | ✅ (full replace)             | replace        |
| PATCH  | ❌                     | ❌ (usually)                  | partial update |
| DELETE | ❌                     | ✅ (gone stays gone)          | remove         |

**Idempotent** = calling it twice leaves the same end state as once. It matters
because **networks retry**: a timeout doesn't tell you whether the request
landed. Retrying a GET/PUT/DELETE is safe; retrying a POST can double-create —
which is why payment APIs demand idempotency keys (→ Level 4.3).

**Soundbite:** "Verbs are chosen by semantics — safety and idempotency — not
habit. Idempotency is what makes retries safe, and retries are inevitable
because a timeout is ambiguous: the request may or may not have executed."

More depth on 400-vs-422, QUERY, envelopes → **IP §3–4**.

## 1.2 Databases from zero — tables, keys, joins

A relational DB stores data in **tables** (rows × typed columns). Two ideas make
it "relational":

- **Primary key (PK):** a column that uniquely identifies each row (`orders.id`).
- **Foreign key (FK):** a column holding another table's PK — the *relationship*
  (`orders.rider_id → riders.id`). The DB enforces it: you can't reference a
  rider that doesn't exist.

```
 orders                              riders
 ┌────┬────────┬───────┬──────────┐  ┌────┬───────┬───────────┐
 │ id │ value  │status │ rider_id │  │ id │ name  │ status    │
 ├────┼────────┼───────┼──────────┤  ├────┼───────┼───────────┤
 │ 1  │ 250.0  │ASSIGN │    2 ────┼──┼► 2 │ Asha  │ BUSY      │
 │ 2  │ 800.0  │PENDING│   NULL   │  │ 3  │ Ravi  │ AVAILABLE │
 └────┴────────┴───────┴──────────┘  └────┴───────┴───────────┘
                FK ──────────────────── PK

 JOIN = stitch rows across the FK:
 SELECT o.id, o.value, r.name
 FROM orders o JOIN riders r ON o.rider_id = r.id;
 → │ 1 │ 250.0 │ Asha │        (order 2 drops out: INNER JOIN needs a match;
                                LEFT JOIN would keep it with name = NULL)
```

The SQL you must be fluent in (practice, don't memorize):

```sql
SELECT status, COUNT(*), AVG(value)      -- aggregate
FROM orders
WHERE created_at > now() - interval '1 day'
GROUP BY status                          -- one row per group
HAVING COUNT(*) > 10                     -- filter groups (WHERE filters rows)
ORDER BY 2 DESC
LIMIT 5;
```

**Soundbite:** "Primary keys identify rows; foreign keys are enforced pointers
between tables; JOINs stitch them back together at query time. INNER JOIN keeps
only matches, LEFT JOIN keeps every left row with NULLs where the right side is
missing."

**Gotcha:** `WHERE` filters *rows before* grouping; `HAVING` filters *groups
after*. And `COUNT(col)` skips NULLs while `COUNT(*)` doesn't — a classic
off-by-surprise in interviews.

**Normalization in one breath:** store each fact once (rider's name lives only
in `riders`, referenced by id everywhere else) — so an update happens in one
place. Denormalize (copy data) only deliberately, for read speed, accepting the
update anomaly. That trade — write simplicity vs read speed — recurs all the way
to Level 4.

ORM, sessions, migrations → **IP §6, §9**.

## 1.3 The N+1 query problem (the #1 ORM interview question)

Fetch 100 orders, then access `order.rider.name` in a loop — the ORM lazily
fires one query *per order*:

```
 N+1 (bad):                             Fixed (2 queries or 1 JOIN):
 SELECT * FROM orders;        1 query   SELECT * FROM orders;
 SELECT * FROM riders WHERE id=2;  ┐    SELECT * FROM riders
 SELECT * FROM riders WHERE id=7;  │      WHERE id IN (2,7,9,...);
 SELECT * FROM riders WHERE id=9;  ├ N   -- or: JOIN in one query
 ...                               ┘    (SQLAlchemy: selectinload / joinedload)
```

100 orders = 101 round-trips ≈ 101 × network latency. The fix is eager loading:
tell the ORM up front which relationships you'll touch.

**Soundbite:** "N+1 is the ORM lazily loading a relationship inside a loop — one
query becomes a hundred and one. You spot it in query logs and fix it with eager
loading, a JOIN or an IN-batch. It's the canonical case of the ORM hiding a cost
you must still understand."

## 1.4 Authentication — sessions vs JWT

**Authentication** = who are you. **Authorization** = what may you do (401 vs
403). HTTP is stateless, so identity must ride on every request. Two patterns:

```
 SESSIONS (stateful)                      JWT (stateless)
 ─────────────────────                    ──────────────────────
 login ──► server stores                  login ──► server SIGNS a token
           {sid: user 7}                            {user:7, role, exp}
       ◄── Set-Cookie: sid=abc                  ◄── token (client stores it)
                                          
 request + cookie sid=abc                 request + Authorization: Bearer <jwt>
   server looks up abc ──► user 7           server VERIFIES the signature —
   (DB/Redis hit per request)               no lookup; the token carries
                                            the identity, tamper-proof
 revoke = delete the session ✅           revoke = hard ❌ (valid till exp;
 extra store, sticky-ish     ❌            needs a blocklist) — so keep
                                           tokens short-lived + refresh token
```

A JWT is `header.payload.signature` — the payload is **readable by anyone**
(base64, not encrypted); the *signature* is what makes it trustworthy. Never put
secrets in it.

**Passwords:** never store them — store a slow salted hash (**bcrypt/argon2**).
Login re-hashes the attempt and compares. Slow is the point: it turns a leaked
table into an expensive brute-force. Fast hashes (SHA-256) are wrong for
passwords.

**Soundbite:** "Sessions keep state server-side and are easy to revoke but cost
a lookup per request and shared session storage when you scale. JWTs push the
state into a signed token — any instance can verify it with no lookup, which
suits horizontally scaled APIs — but revocation is hard, so you keep them
short-lived with refresh tokens. Passwords are bcrypt-hashed; a signed token is
readable but not forgeable."

**Gotcha:** 401 = "not authenticated (or token invalid)"; 403 = "authenticated,
but not allowed." Mixing them up is a red flag. Also know the *actor vs edge*
distinction → IP §19 (a legal state transition by the wrong actor).

## 1.5 Level 1 self-test

1. Why does idempotency matter? Which verbs have it, and why do payment APIs
   need idempotency keys on POST?
2. Draw the two tables + FK for orders→riders. INNER vs LEFT JOIN result?
3. WHERE vs HAVING. `COUNT(*)` vs `COUNT(col)`.
4. What is N+1, how do you detect it, two ways to fix it?
5. Sessions vs JWT — two pros and the killer con of each. Where does each break
   at 3 instances?
6. Why bcrypt and not SHA-256 for passwords? What's in a JWT's three parts?
7. 401 vs 403?

---
---

# LEVEL 2 — Data & Concurrency (mid-level SDE)

## 2.1 Indexes — how lookups get fast

Without an index, `WHERE id = 42` is a **sequential scan**: read every row,
O(n). An index is a **B-tree** — a sorted, shallow tree kept alongside the
table — making the lookup O(log n) with ~3–4 page reads even for millions of
rows.

```
                    B-TREE on orders.id
                        ┌─────────┐
                        │  ≤400 │ >400
                        └──┬───────┬──┘
                 ┌─────────┴─┐   ┌─┴─────────┐
                 │ ≤200 │>200│   │ ≤700 │>700│
                 └─┬──────┬──┘   └──┬──────┬─┘
                  leaf   leaf     leaf    leaf     ← sorted keys + row pointers
                                    │
                        id=420 → (points to the row on disk)

 million rows: seq scan = 1,000,000 reads   index = ~3 levels + 1 row fetch
```

What you must be able to say:

- **Indexes cost writes.** Every INSERT/UPDATE must also update every index —
  so you index the columns you *query by*, not everything.
- **Composite index `(a, b)`** works like a phone book sorted by (last, first):
  great for `WHERE a=… AND b=…` or just `a=…`; useless for `b` alone —
  **leftmost-prefix rule**.
- **Why the planner ignores your index:** low selectivity (status has 5 values —
  half the table matches, seq scan is cheaper), a function on the column
  (`WHERE lower(email)=…` needs an index *on* `lower(email)`), or a tiny table.
- **`EXPLAIN ANALYZE`** is the tool: it shows seq-scan vs index-scan and real
  timings. Saying "I'd check the plan with EXPLAIN" is the senior move.

**Soundbite:** "An index is a B-tree — O(log n) lookups bought at the price of
extra work on every write. I index what appears in WHERE/JOIN/ORDER BY, mind the
leftmost-prefix rule on composites, and verify with EXPLAIN ANALYZE rather than
assuming the planner uses it."

**Gotcha:** an index on `status` alone barely helps DeliverIQ's dispatch query
(5 statuses, low selectivity) — but a **partial index**
(`CREATE INDEX ... WHERE status = 'PENDING'`) is tiny and perfect for "fetch
pending orders." Naming partial indexes is a strong Postgres signal.

## 2.2 Transactions & ACID — for real, not as a mnemonic

A **transaction** makes several statements one all-or-nothing unit:

```sql
BEGIN;
UPDATE orders SET status='ASSIGNED', rider_id=2 WHERE id=1;
UPDATE riders SET status='BUSY' WHERE id=2;
COMMIT;   -- both happen, or (ROLLBACK / crash) neither does
```

- **A — Atomicity:** all or nothing. Crash between the updates? Both undone.
  (Mechanism: the WAL → Level 4.6.)
- **C — Consistency:** constraints (FKs, NOT NULL, checks) hold before and
  after. The DB refuses a commit that breaks them.
- **I — Isolation:** concurrent transactions don't see each other's half-done
  work. The interesting one — it has *levels* (next section).
- **D — Durability:** once COMMIT returns, the data survives a crash — it's on
  disk (in the WAL) before the DB says yes.

**Soundbite:** "Assigning an order touches two rows — order and rider. A
transaction makes that atomic: no state where the order is assigned but the
rider isn't busy. Durability means a returned commit survives power loss,
because the WAL is flushed before the commit acknowledges."

**Gotcha (SQLAlchemy):** the Session opens a transaction implicitly at your
first query and holds it until `commit()`/`rollback()` — so *everything* between
first query and commit is one transaction already. Knowing where that boundary
sits is exactly what row-locking work (Day 29) depends on.

## 2.3 Isolation levels & the anomalies (memorize this table)

Isolation is a dial: stricter = safer = slower/more retries.

| Anomaly ↓ / Level →      | Read Uncommitted | **Read Committed** (PG default) | Repeatable Read | Serializable |
|--------------------------|------------------|-------------------------------|-----------------|--------------|
| Dirty read (see uncommitted data) | possible | ✅ prevented | ✅ | ✅ |
| Non-repeatable read (row changes between my two reads) | possible | possible | ✅ prevented | ✅ |
| Phantom read (new rows appear in my repeated query) | possible | possible | ✅ (in PG*) | ✅ |
| Lost update / write skew | possible | possible | partly | ✅ prevented |

\* Postgres implements Repeatable Read as **snapshot isolation** — you see a
frozen snapshot from transaction start; phantoms don't appear, but **write
skew** (two txns each read, then write based on stale reads of *different* rows)
still can. Serializable catches even that, at the cost of occasional
serialization-failure errors you must retry.

**Soundbite:** "Postgres defaults to Read Committed: each statement sees the
latest committed data, so no dirty reads — but two reads in one transaction can
disagree, and read-then-write races like a double dispatch are absolutely
possible. You fix those either by escalating isolation to Serializable and
retrying failures, or — usually better — by explicit locking on the rows that
contend."

## 2.4 The lost update — and the two locking philosophies ⭐

This is DeliverIQ's Day 29 bug, and the single most useful concurrency diagram
you can draw in an interview:

```
 TIME  INSTANCE A                        INSTANCE B
  │    BEGIN                             BEGIN
  │    SELECT ... WHERE status='PENDING' SELECT ... WHERE status='PENDING'
  │         → sees order 1                    → sees order 1  (same row!)
  │    picks order 1, rider 2            picks order 1, rider 9
  │    UPDATE order 1 → ASSIGNED, r=2
  │    COMMIT ✅
  │                                      UPDATE order 1 → ASSIGNED, r=9
  ▼                                      COMMIT ✅  ← silently overwrites A
 RESULT: order 1 assigned to rider 9; rider 2 is BUSY for nothing. No error
 was raised anywhere — that's what makes lost updates dangerous.
```

**Fix 1 — Pessimistic locking** ("assume conflict, take the lock first"):

```sql
SELECT * FROM orders
WHERE status = 'PENDING'
ORDER BY priority DESC
LIMIT 1
FOR UPDATE SKIP LOCKED;   -- lock the row; skip rows others hold
```

```
 A: locks order 1  ──────────► works ──► COMMIT (lock released)
 B: FOR UPDATE would WAIT on order 1…
    but SKIP LOCKED says: don't wait — take the next unlocked row
 B: locks order 2  ──────────► works ──► COMMIT
 → two instances drain the queue in parallel, zero double-dispatch
```

- `FOR UPDATE` = "lock the rows this SELECT returns until my commit."
- `SKIP LOCKED` = "rows someone else holds are invisible to me" — turns a table
  into a safe multi-consumer **job queue**. (`NOWAIT` = error instead of skip.)
- The lock lives **only inside an open transaction** — lock, update, commit must
  be one transaction or it's theater.

**Fix 2 — Optimistic locking** ("assume no conflict, detect it at write time"):

```sql
-- read: id=1, version=7 … compute … then:
UPDATE orders SET status='ASSIGNED', rider_id=2, version=8
WHERE id=1 AND version=7;
-- rows affected = 1 → you won.   = 0 → someone changed it first: reload+retry
```

No lock held; conflicts surface as a failed UPDATE you retry. (A cousin without
a version column: `UPDATE … WHERE id=1 AND status='PENDING'` — the *guard in
the WHERE* makes the write conditional. 0 rows = you lost the race.)

**When to use which:**

| | Pessimistic (FOR UPDATE) | Optimistic (version/guard) |
|---|---|---|
| Contention | high (everyone wants the *same* hot rows — a dispatch queue) | low (conflicts rare — user edits own profile) |
| Cost | holds locks → others wait/skip | retries on conflict |
| Failure mode | lock waits, deadlocks | wasted work when conflicts spike |

**Soundbite:** "Read-then-write with no guard is a lost update — two workers
read the same PENDING row, both commit, the second silently wins. For a dispatch
queue I go pessimistic: `SELECT … FOR UPDATE SKIP LOCKED` inside the
transaction, so each instance claims a disjoint row and skips, not waits on,
locked ones. For low-contention updates I'd go optimistic — a version column and
a conditional UPDATE, retrying on zero rows affected."

**Gotcha:** locking **all** pending rows (`.all()` with FOR UPDATE) defeats SKIP
LOCKED — instance A holds everything, B sees an empty queue. Lock exactly the
row(s) you claim (`LIMIT 1`, or re-select the chosen winner). And Redis-side
state (a rider index) isn't covered by a Postgres lock — every store needs its
own atomicity story (Lua → IP §31, or an atomic claim like `SREM` returning 1).

## 2.5 Deadlocks

Two transactions each hold a lock the other needs — a cycle; nobody can proceed.

```
 TXN A: locks order 1 ──── wants rider 2 (held by B) ──┐
 TXN B: locks rider 2 ──── wants order 1 (held by A) ──┘   cycle → deadlock
```

Postgres detects the cycle and **kills one** transaction (deadlock error); your
app must retry it. Prevention: **acquire locks in a globally consistent order**
(always order-then-rider, or always ascending id) so a cycle can't form; keep
transactions short.

**Soundbite:** "Deadlock is a lock cycle. Postgres breaks it by aborting a
victim, so the app needs retry logic — but the real fix is consistent lock
ordering across all code paths and short transactions."

## 2.6 Connection pooling

Opening a DB connection is expensive (TCP + auth + a Postgres process per
connection). A **pool** keeps N warm connections; requests borrow and return.

```
 500 concurrent requests ──► [ pool: 20 connections ] ──► Postgres
                              borrow → query → return      (~20 backends,
                              excess requests wait briefly    not 500)
```

Postgres caps at `max_connections` (~100 default); each one costs real memory.
3 app instances × pool 20 = 60 — do that arithmetic *before* the DB does it for
you. At scale add a server-side pooler (PgBouncer).

**Soundbite:** "SQLAlchemy's engine pools connections — requests share a small
set of warm connections rather than paying setup per request. Sizing is
instances × pool_size against Postgres's max_connections; overflow that and new
connections error out. PgBouncer is the next tier when many services share one
DB."

## 2.7 Caching — patterns, invalidation, stampede

Cache = a small fast store in front of a slow one, trading **freshness** for
**latency** (a Redis GET ~0.2 ms vs a complex Postgres query ~5–50 ms).

```
 CACHE-ASIDE (the default pattern)
                 ┌─── hit? return it  (fast path)
 request ──► Redis
                 └─ miss ──► Postgres ──► write result to Redis + TTL ──► return

 WRITE path: update Postgres, then INVALIDATE (delete) the cache key —
 delete, don't overwrite: the next read repopulates a guaranteed-fresh value.
```

- **Write-through** (write to cache+DB together) and **write-behind** (write
  cache now, flush to DB async — fast but risks loss) are the variants; name
  them, use cache-aside by default.
- **TTL** bounds staleness even when invalidation misses.
- **Stampede:** a hot key expires and 1000 concurrent requests all miss and all
  hit the DB at once. Fixes: a short lock so one request recomputes while others
  wait/serve-stale; or jittered TTLs so keys don't expire together.
- "There are two hard things in CS: cache invalidation and naming things" — the
  point is that a cache is a *copy*, and every copy can lie.

**Soundbite:** "Cache-aside with TTL, and on writes I invalidate rather than
update the key — deletion can't be stale. The two failure modes to design for
are staleness, bounded by TTL and invalidation, and stampede, bounded by
per-key recompute locks or TTL jitter." (Redis mechanics → IP §10; the
dual-write drift problem → IP §17.)

## 2.8 Processes, threads, async — where Python fits

```
 PROCESSES: own memory each; true parallelism; heavy.        (scale: workers)
 THREADS:   shared memory; light; in CPython the GIL lets    (I/O concurrency)
            only ONE thread run Python bytecode at a time.
 ASYNC:     ONE thread, an EVENT LOOP interleaving tasks     (huge I/O
            at await points — no GIL contention at all.       concurrency)

 EVENT LOOP: req A ──► await db query ─┐ (A parked, not blocking)
             req B ──► await redis ────┤ loop runs whoever is ready
             req A ◄── db replied ─────┘ resumes A
```

Key judgment: **I/O-bound** work (APIs waiting on DB/network — DeliverIQ) →
async or threads shine. **CPU-bound** work (crunching numbers) → the GIL chokes
threads; you need processes. FastAPI runs `async def` handlers on the loop and
`def` handlers on a threadpool — blocking calls inside `async def` freeze
*every* request on that loop.

**Soundbite:** "The GIL means Python threads don't parallelize CPU work, but an
API is I/O-bound — requests spend their time waiting on Postgres and Redis. The
async event loop interleaves thousands of waiting requests on one thread. The
cardinal sin is a blocking call inside an async handler: it stalls the whole
loop. CPU-heavy work goes to worker processes." (contextvars per-request
isolation → IP §25.)

## 2.9 Level 2 self-test

1. Draw a B-tree lookup vs a seq scan. Why might the planner *ignore* an index
   on `status`? What's a partial index?
2. Leftmost-prefix rule for `(a,b)` — which queries can use it?
3. Each ACID letter, concretely, using the order+rider assignment.
4. The isolation table: which anomaly does each level kill? What's Postgres's
   default and what does snapshot isolation still allow?
5. Draw the lost-update interleaving. Then fix it both ways: FOR UPDATE SKIP
   LOCKED and a version-guard UPDATE. When is each right?
6. Why must FOR UPDATE sit inside the transaction that also writes?
7. Deadlock: cause, what Postgres does, the prevention rule.
8. Pool sizing math for 3 instances; what breaks past max_connections?
9. Cache-aside read and write paths. Why delete instead of update on
   invalidation? What's a stampede and two fixes?
10. GIL: why threads still help an API but not a number-cruncher. What does one
    blocking call inside an async handler do?

---
---

# LEVEL 3 — Distributed Systems (senior SDE)

## 3.1 Queues vs event logs (RabbitMQ vs Kafka)

Two different shapes of "message broker" — know which is which:

```
 QUEUE (RabbitMQ/SQS):  producer ──► [ msg msg msg ] ──► one consumer GETS it,
                        message is CONSUMED — gone. Work distribution.

 LOG (Kafka):           producer ──► [0][1][2][3][4][5]...  append-only, KEPT
                                       ▲         ▲
                        consumer group A (offset 4)   group B (offset 2)
                        each group reads independently; nothing is deleted
                        by reading — replay = rewind your offset.
```

Kafka mechanics that interviews probe:

```
 TOPIC "order.events"
 ├── partition 0: [o1][o4][o7]...   ← ordering guaranteed ONLY within
 ├── partition 1: [o2][o5][o8]...     a partition; key → partition
 └── partition 2: [o3][o6][o9]...     (same key ⇒ same partition ⇒ in order)

 CONSUMER GROUP "notifications": 3 consumers ⇒ one per partition (max
 parallelism = partition count). Group "analytics" reads the same data
 independently at its own pace.
```

**Soundbite:** "A queue distributes work — a message is consumed once and gone.
Kafka is a durable log — consumers track offsets, many groups read the same
stream independently, and replay is just rewinding. Ordering is per-partition,
so I key by order_id to keep one order's events in sequence; parallelism is
capped by partition count." (Why Redis Pub/Sub loses messages → IP §21.)

## 3.2 Delivery semantics & idempotent consumers ⭐

What happens when a consumer crashes mid-message?

- **At-most-once:** ack *before* processing → crash = message lost.
- **At-least-once:** ack *after* processing → crash after work, before ack =
  message **redelivered** = possible duplicate. *This is the practical default.*
- **Exactly-once:** effectively a myth across arbitrary systems — what exists is
  at-least-once delivery + **idempotent processing**, so duplicates are harmless.

Making a consumer idempotent: natural idempotency (`SET status='DELIVERED'`
twice is fine), a **processed-message table** (`INSERT event_id` with a unique
constraint, skip if present — in the *same transaction* as the effect), or
conditional writes (`WHERE status='PENDING'`).

**Soundbite:** "I design for at-least-once and make consumers idempotent —
dedupe on event id inside the same transaction as the side effect. 'Exactly
once' in practice means at-least-once delivery plus idempotent handling, not a
magic broker guarantee."

## 3.3 The dual-write problem & the outbox pattern ⭐

Commit to Postgres **then** publish to Kafka = two systems, no shared
transaction. Crash between them → the DB changed but the event never fired
(or, publish-first → an event for a rollback: a phantom → IP §21).

```
 OUTBOX PATTERN
 ┌─ one Postgres transaction ─────────────────┐
 │ UPDATE orders SET status='ASSIGNED' ...    │   atomic: state change and
 │ INSERT INTO outbox (event_json)            │   event recorded TOGETHER
 └────────────────────────────────────────────┘
        │  a RELAY process polls outbox (or tails the WAL — CDC/Debezium)
        ▼
      Kafka ──► delete/mark the outbox row after publish
      (relay may retry ⇒ duplicates ⇒ consumers idempotent — see 3.2)
```

**Soundbite:** "You can't atomically commit to Postgres and publish to Kafka —
that's the dual-write problem. The outbox pattern writes the event into an
outbox table inside the business transaction, and a relay publishes from there.
The event is now exactly as durable as the state change; the price is
at-least-once publishing, which idempotent consumers absorb."

## 3.4 Replication — one DB becomes several

```
                     writes
   clients ─────────► LEADER ──── WAL stream ────► FOLLOWER 1  ─┐
                        │                        ► FOLLOWER 2  ─┤ reads
   clients ◄──────────── reads can go to followers ────────────┘
```

- **Why:** read scaling (fan reads out to replicas) and high availability
  (follower promoted if the leader dies).
- **Async replication** (default): fast writes, but a follower lags by
  milliseconds-to-seconds → **replication lag**. Classic bug: user writes, next
  request reads a replica, their write "disappears." Fix: **read-your-writes** —
  route that user's reads to the leader briefly, or stick post-write reads to
  the leader.
- **Sync replication:** leader waits for follower ack — no loss, slower writes.
  Durability vs latency, pick per table/business need.

**Soundbite:** "Leader takes writes, followers replay the WAL and serve reads.
Async replication means lag, so naive read-splitting breaks read-your-writes —
I route a user's reads to the leader right after their write. Sync replication
trades write latency for zero-loss failover."

## 3.5 Sharding & consistent hashing

Replication copies *all* data everywhere; **sharding** splits data so each node
holds a fraction — the answer when *writes* or data size outgrow one machine.

```
 shard by city:   orders[BLR] → shard 1    orders[DEL] → shard 2 ...
 shard by hash:   hash(order_id) % N  → shard        (even spread, but
                  cross-shard queries & JOINs get hard; transactions too)
```

Problem with `% N`: add one node and *almost every key remaps*. Fix:

```
 CONSISTENT HASHING — nodes and keys hash onto a ring; a key belongs to the
 next node clockwise. Adding node D moves ONLY the keys in the arc before D:

        A ●────────● B                 A ●───●D───● B
          │  ring  │        add D ⇒      │        │      keys between A→D
        C ●────────┘                   C ●────────┘      move; rest stay put
 (virtual nodes: each physical node appears many times on the ring for balance)
```

**Soundbite:** "Shard when a single primary can't take the write volume. The
shard key decides everything — you want queries to hit one shard, so DeliverIQ
would shard by city: dispatch is city-local anyway. Modulo hashing reshuffles
everything on resize; consistent hashing moves only 1/N of keys, which is why
caches and Kafka-like systems use ring placement."

**Gotcha:** cross-shard transactions and JOINs are the tax. Pick a shard key
that makes the hot path single-shard, and accept that global queries become
scatter-gather or move to an analytics store.

## 3.6 CAP — and what it actually means

```
            Consistency (every read sees the latest write)
               ▲
              CAP: when a network PARTITION happens (P is not optional —
               │   networks fail), you must choose:
               │     CP: refuse/stall some requests, stay correct
               │     AP: keep answering, possibly stale
               ▼
   Availability ◄───────────► Partition tolerance
```

- CAP only bites **during a partition**. **PACELC** extends it: *Else* (no
  partition) you still trade **L**atency vs **C**onsistency (e.g. async
  replication = faster but stale-able reads).
- Real systems choose per-feature: payments/dispatch = CP (never double-charge,
  never double-assign); rider location feed = AP (a 2-second-stale location is
  fine; unavailability is worse).

**Soundbite:** "CAP says under a partition you pick consistency or availability.
I answer it per-feature: dispatch and payments must be CP — I'd rather fail a
request than double-assign — while location tracking is AP, stale is acceptable.
PACELC is the grown-up version: even without partitions, replication trades
latency against consistency."

## 3.7 Horizontal scaling — the stateless checklist

```
                        ┌──► instance 1 ─┐
 clients ──► LOAD       ├──► instance 2 ─┼──► shared Postgres
             BALANCER   └──► instance 3 ─┘──► shared Redis
 (health checks; pulls a dead instance out of rotation)
```

Vertical scaling (bigger machine) is simple but has a ceiling and no
redundancy. Horizontal (more machines) is the real path — **if instances are
stateless**: any request served by any instance, all shared state pushed out to
Postgres/Redis/Kafka. The audit checklist for "can I run 3 of these?":

- ❌ in-memory caches/counters per instance (rate limiter must live in Redis →
  IP §31) — ❌ module-level mutable state — ❌ local file writes — ❌ in-process
  queues (a per-process heap = double dispatch; → the Day 29 locking work)
- ❌ cron inside the app (3 instances = 3 executions; needs a distributed lock
  or one dedicated scheduler)
- ✅ sticky sessions are a smell — fix statelessness instead.

**Soundbite:** "Horizontal scaling requires statelessness: every piece of
mutable state either moves to a shared store or gets a concurrency-safe claim
protocol. My audit found two single-instance assumptions — the in-process
dispatch pick and pre-commit Redis writes — which is exactly what the
SKIP LOCKED work fixes."

## 3.8 Resilience — timeouts, retries, circuit breakers

Calls to other services fail; the pattern stack, in order:

1. **Timeout everything.** A missing timeout turns a slow dependency into your
   own outage (threads/connections pile up waiting).
2. **Retry with exponential backoff + jitter** — only idempotent operations!
   Backoff: 1s, 2s, 4s… Jitter (randomness) prevents every client retrying in
   lockstep and re-stampeding the recovering service.
3. **Circuit breaker** — stop hammering something that's down:

```
        failures ≥ threshold                    trial succeeds
 CLOSED ────────────────────► OPEN ──cooldown──► HALF-OPEN ──────► CLOSED
 (normal: calls flow)   (fail fast, don't call)  (let a few through)
                                                   trial fails ──► OPEN
```

4. **Graceful degradation:** Redis down ≠ API down — e.g. rate limiter
   fail-open (allow requests, log loudly) vs fail-closed for a security check.

**Soundbite:** "Timeouts first — an un-timeouted call is an outage amplifier.
Retries with backoff and jitter, only on idempotent ops. A circuit breaker fails
fast when a dependency is clearly down and probes it half-open. And I decide
fail-open versus fail-closed per dependency: rate limiter open, auth closed."

## 3.9 Observability — the three pillars

- **Logs** = discrete events, queryable JSON with a request_id (→ IP §25).
- **Metrics** = cheap aggregated numbers over time (Prometheus): the **RED**
  method per service — **R**ate, **E**rrors, **D**uration (as percentiles).
- **Traces** = one request's timeline *across services*, spans showing where the
  time went (request_id is the poor man's version).

**Percentiles, not averages:** p50 = median, p99 = the worst 1%. Averages hide
the tail; the tail is what users feel (→ IP §38). Alert on symptoms users feel
(error rate, p99), not causes (CPU%).

**Soundbite:** "Logs for events, metrics for trends, traces for where a request
spent its time. I dashboard RED — rate, errors, duration — and alert on p99 and
error rate, because an average is a lie about your slowest users."

## 3.10 Level 3 self-test

1. Queue vs log — the consumption model difference. Where does each fit?
2. Kafka: what guarantees ordering, what caps parallelism, how does replay work?
3. Derive at-least-once from "when do I ack?" Why is exactly-once a myth, and
   what's the real recipe?
4. Draw the outbox pattern. What problem, what price?
5. Replication lag: the read-your-writes bug and the fix. Sync vs async trade.
6. Why does `% N` sharding hurt? Draw the consistent-hashing fix. What's the
   cross-shard tax?
7. CP vs AP for: dispatch, payments, rider locations — and defend each.
8. The stateless checklist — name 4 things that break at 3 instances.
9. Order the resilience stack. Why jitter? Draw the breaker states.
10. RED method; why p99 over average; symptom vs cause alerts.

---
---

# LEVEL 4 — Master (staff-level signal)

## 4.1 The system design answer framework

Never jump to boxes-and-arrows. The framework interviewers grade against:

```
 1. REQUIREMENTS (5 min)   functional: what must it do?
    ask, don't assume      non-functional: scale? latency SLO? consistency?
                           "How many orders/day? Cities? Peak factor?"
 2. ESTIMATE (2 min)       QPS, storage, hot paths — envelope math (§4.2)
 3. API + DATA MODEL       core endpoints, tables, the ids everything hangs on
 4. HIGH-LEVEL DIAGRAM     client → LB → services → stores → async pipeline
 5. DEEP DIVE              the interviewer picks (or you offer) 1–2 bottlenecks;
    THE BOTTLENECK         this is where Levels 2–3 knowledge gets spent
 6. WRAP                   failure modes, monitoring, what you'd build first
```

Every choice stated as a **trade-off** ("X buys me A at the cost of B; here A
matters more because…") — that habit *is* the senior signal.

## 4.2 Envelope math — the numbers to carry in your head

```
 LATENCY (orders of magnitude)          THROUGHPUT MATH
 ─────────────────────────────          ────────────────────────────
 RAM access            ~100 ns          1M requests/day ≈ 12 rps avg
 SSD random read       ~100 µs          peak ≈ 3–10× avg  → plan ~50–100 rps
 same-DC round trip    ~0.5 ms          1 Postgres node: ~1k–10k simple qps
 Redis op (w/ network) ~0.5 ms          1 API instance: ~100s of rps (I/O bound)
 Postgres indexed read ~1–5 ms
 HDD seek              ~10 ms           STORAGE: 1M orders × ~1 KB ≈ 1 GB/day
 cross-region RTT      ~50–150 ms                → ~365 GB/yr — one node is fine
```

The point isn't precision — it's catching absurdities ("that's 12 rps, we don't
need Kafka for intake" or "100M location pings/day can't hit Postgres raw").

## 4.3 Idempotency keys — end-to-end

The client-side dual of §3.2: make **POST** retry-safe.

```
 client generates key K (uuid) ──► POST /orders  Idempotency-Key: K
 server: INSERT INTO idempotency(key K, ...) — unique constraint
   ├─ insert wins → process, store the response against K
   └─ duplicate  → return the STORED response (same status, same body)
 client timeout? retry with the SAME K → gets the original result, no dup order
```

The dedupe record and the business effect must commit **in one transaction**,
or you've just moved the race. Keys get a TTL (e.g. 24h).

**Soundbite:** "A timeout is ambiguous, so clients retry POSTs with an
idempotency key; the server deduplicates on a unique constraint and replays the
stored response. Uniqueness check and side effect share one transaction —
otherwise the race just moved."

## 4.4 Distributed transactions — sagas over 2PC

A checkout spans services (order, payment, dispatch) — no shared transaction.
**2PC** (two-phase commit — a coordinator asks everyone to prepare, then
commit) blocks everything on the slowest/dead participant; avoided in practice.
The workhorse is the **saga**: a chain of local transactions, each with a
**compensating action** to undo it if a later step fails.

```
 create order ──► charge payment ──► assign rider ──► done ✅
      │                │                  ✗ fails
      │                ◄── REFUND payment (compensate)
      ◄── CANCEL order (compensate)                       eventual consistency
```

Choreography (each service reacts to events) vs orchestration (one coordinator
drives) — orchestration is easier to reason about. Note compensation isn't
rollback: the charge *happened*, then a refund happened; intermediate states are
visible. Design them to be safe to see (PENDING_PAYMENT, etc.).

**Soundbite:** "Across services I use a saga: local transactions plus
compensations — refund, cancel — instead of 2PC, which blocks on a dead
coordinator. It's eventual consistency, so intermediate states are modeled
explicitly and every step and compensation is idempotent, because the saga
itself retries."

## 4.5 Event sourcing vs CRUD (know it, one paragraph)

CRUD stores *current state* (`status='DELIVERED'`); event sourcing stores the
*sequence of facts* (`OrderCreated, Assigned, PickedUp, Delivered`) and derives
state by replay. Buys a perfect audit log, time travel, natural Kafka fit; costs
complexity (projections, snapshots, event versioning). Middle path most teams
take: CRUD tables **plus** an append-only events/outbox table — current state
fast, history kept.

## 4.6 Postgres internals — WAL & MVCC (the "how does it actually work")

- **WAL (write-ahead log):** every change is appended to a sequential log and
  **fsynced before COMMIT returns** — that's Durability. Crash recovery =
  replay the WAL; replication = stream it (§3.4); data pages update lazily
  afterward. Sequential appends are why commits are fast.
- **MVCC (multi-version concurrency control):** an UPDATE doesn't overwrite —
  it writes a **new row version**; each transaction reads the versions visible
  to *its snapshot*. Hence: **readers never block writers, writers never block
  readers** — only writer-vs-writer conflicts need locks (§2.4). Dead versions
  pile up until **VACUUM** reclaims them (why update-heavy tables bloat).

**Soundbite:** "Commit means the WAL hit disk — data pages catch up later, and
replicas are just WAL consumers. MVCC gives every transaction a snapshot over
row versions, so reads and writes don't block each other; the costs are vacuum
debt and the fact that MVCC doesn't prevent write-write races — that's what
explicit locks are still for."

## 4.7 Security essentials (the checklist interviewers expect)

- **SQL injection:** never concatenate SQL with user input — parameterized
  queries (the ORM does this; know *why*: the value can never be parsed as SQL).
- **Secrets:** env vars/secret managers, never in git (→ IP §27); hash
  passwords (bcrypt/argon2, §1.4); sign tokens, short expiry.
- **Transport:** TLS everywhere; cookies `HttpOnly` (JS can't read → XSS can't
  steal) + `Secure` + `SameSite` (CSRF).
- **Don't leak internals:** stack traces stay in logs; clients get the error
  envelope (→ IP §29). Rate-limit auth endpoints (→ IP §11).
- **AuthZ on every request** server-side: role + *ownership* (rider can only
  advance their own order — the actor check, IP §19).

## 4.8 Worked example — "Design a food delivery dispatch system" ⭐

(Your project *is* the seed — this is you scaling it up in an interview.)

**1. Requirements:** create orders, track riders' live locations, assign the
best rider fast (< ~5 s), order lifecycle, notifications. Scale: say 1M
orders/day, 100k riders, 20 cities. Consistency: an order is assigned to
**exactly one** rider (CP); locations may be stale (AP).

**2. Envelope:** 1M/day ≈ 12 rps orders (peak ~100). Locations: 100k riders ×
1 ping/5s ≈ **20k writes/s — the real hot path is locations, not orders.**

**3. Data model:** `orders(id, status, value, pickup/drop, rider_id, version)`,
`riders(id, status, city)` in Postgres, sharded/partitioned **by city** (§3.5 —
dispatch is city-local). Locations in **Redis geo/geohash** (→ IP §14), not
Postgres — 20k writes/s of ephemeral data is exactly what Redis is for.

**4. Architecture:**

```
 customer app ──► LB ──► ORDER SVC ──► Postgres (orders, by city)
                            │ outbox → Kafka "order.events"
 rider app ──► LB ──► LOCATION SVC ──► Redis geohash cells (TTL'd)
                                        (no DB write per ping; optional
                                         Kafka → S3 for history/analytics)
                     DISPATCH WORKERS (per city, N instances)
                       loop: SELECT … FROM orders WHERE status='PENDING'
                             ORDER BY priority LIMIT 1
                             FOR UPDATE SKIP LOCKED            ← §2.4
                             → query Redis for nearby riders   ← IP §14–15
                             → claim rider (atomic SREM / conditional write)
                             → commit → outbox event
        Kafka ──► notification svc │ analytics (own consumer groups) ← §3.1
```

**5. Deep dives you can offer:** the assignment race (SKIP LOCKED + atomic
rider claim — §2.4); location write volume (Redis, TTL as liveness — a rider
whose key expires stops being matchable); fairness vs ETA (banded dispatch →
IP §15); surge/backpressure (priority aging → IP §12); failure of a dispatch
worker (locks die with its transaction — another worker just picks the row up).

**6. Wrap:** monitor assignment latency p99 + unassigned-order age (RED, §3.9);
replicas for reads (§3.4); first thing built = the single-city monolith, shard
when a city's write volume demands it.

## 4.9 Level 4 self-test

1. Recite the 6-step design framework. What are you doing in minute one?
2. 5M requests/day → peak rps? 100k riders pinging every 5 s → writes/s, and
   where do they go?
3. Idempotency keys: why, the unique-constraint mechanics, the one-transaction
   rule.
4. Saga vs 2PC. Why must steps *and compensations* be idempotent? What's
   visible mid-saga?
5. What exactly does "COMMIT returned" guarantee, mechanically?
6. MVCC: why don't readers block writers? What's vacuum debt? What race does
   MVCC *not* solve?
7. Whiteboard the dispatch design end-to-end in 5 minutes, naming the trade-off
   at every arrow.

---
---

# INTERVIEW EXECUTION

## E.1 How to answer anything

- **Clarify → structure → answer → trade-off.** Restate the question, give the
  shape of your answer ("two parts: the mechanism, then when it breaks"), then
  fill it in, then name the alternative you rejected and why.
- **The trade-off habit:** no tool is "better," it's better *for something*.
  "Redis over Memcached *because* sorted sets and pub/sub" beats "Redis is
  fast." Every soundbite in both docs is built this shape — that's deliberate.
- **Say "it depends," then immediately say on what.** "Pessimistic or
  optimistic? Depends on contention: hot dispatch queue → locks; rare profile
  edits → versions."
- **Project stories (behavioral-technical):** Situation → the constraint →
  your decision *and the alternative* → measurable result → what you'd change.
  You have these pre-built: every "Gotcha (the one I hit)" in Interview_prep.md
  is a story — the boundary-cell bug (IP §14), the localhost-in-Docker bug
  (IP §36), the stale-server port bug (IP §11).
- **When you don't know:** reason out loud from what you do know. "I haven't
  used Cassandra, but it's AP and write-optimized, so I'd expect…" is worth
  more than a memorized fact.

## E.2 DeliverIQ → interview-topic map

| You built | It demonstrates | Deep dive |
|---|---|---|
| Token-bucket limiter + Lua | atomicity, race conditions, distributed counters | IP §11, §31 · here §2.4 |
| heapq dispatch + aging | scheduling, starvation, priority queues | IP §12 |
| Geohash + haversine + band | spatial indexing, constrained assignment | IP §14–15 |
| Order state machine | state modeling, error semantics (400 vs 500) | IP §19 |
| Postgres↔Redis dual write | cache consistency, reconciliation | IP §17 · here §2.7, §3.3 |
| Commit-then-publish | event ordering, phantom events → outbox | IP §21 · here §3.3 |
| FOR UPDATE SKIP LOCKED (Day 29) | lost updates, pessimistic locking, multi-instance | here §2.4, §3.7 |
| Alembic, Compose, healthchecks | migrations, environment-as-code, readiness | IP §9, §40–42 |
| Structured logs + request_id | observability, async context | IP §25 · here §3.9 |
| Locust runs | percentiles, capacity honesty | IP §38 · here §4.2 |

## E.3 Master checklist — can you, without notes…

- [ ] narrate the URL journey and name a failure mode at each hop (§0.2)
- [ ] fill the verb safety/idempotency table and justify POST for /dispatch (§1.1)
- [ ] draw orders⋈riders and both JOIN results (§1.2)
- [ ] explain N+1 and two fixes (§1.3)
- [ ] argue sessions vs JWT for a 3-instance API (§1.4)
- [ ] draw a B-tree, explain leftmost-prefix, name a partial index use (§2.1)
- [ ] fill the isolation/anomaly table from memory (§2.3)
- [ ] draw the lost update and fix it both ways (§2.4) ← **your Day 29 story**
- [ ] explain cache-aside + stampede (§2.7) and the GIL/event-loop split (§2.8)
- [ ] contrast queue vs log; derive at-least-once; sketch the outbox (§3.1–3.3)
- [ ] explain replication lag + read-your-writes; consistent hashing (§3.4–3.5)
- [ ] answer CAP per-feature, not in the abstract (§3.6)
- [ ] recite the stateless checklist and the resilience stack (§3.7–3.8)
- [ ] run the 6-step framework on a fresh prompt with envelope math (§4.1–4.2)
- [ ] whiteboard the dispatch system with a trade-off at every arrow (§4.8)

*Every unchecked box is your next review target.*
