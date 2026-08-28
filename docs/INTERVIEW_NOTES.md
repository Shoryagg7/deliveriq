# DeliverIQ — Interview Notes

> **What this is.** The fundamentals, one term at a time — my resume decoded,
> the stack choices behind it, and deep passes on **rate limiting**, **Redis**,
> **Postgres**, **auth/JWT** and **Kafka**, the topics every follow-up has landed
> on so far.
>
> Its companion, [`INTERVIEW_PREP.md`](INTERVIEW_PREP.md), is the *project*
> story: the design decisions and the audit. This file is the theory those
> decisions are made of.
>
> Aimed at SDE-1 depth: what a backend engineer is expected to explain, draw, and
> write pseudocode for on a whiteboard — including **how each dependency is
> actually wired up**, which gets asked more often than any theory question.

---

# Part 0 — Your resume, decoded

**The drill: an interviewer picks one word off your resume and asks "what does
that mean?"** Every term below is on the page, so every term is fair game. One
line each — the depth is in Parts 2 and 3.

## Bullet 1 — concurrency

> *Eliminated a double-dispatch race across 3 API replicas with a two-phase
> `SELECT FOR UPDATE SKIP LOCKED` claim; re-measured under burst, found it
> correct but not live — half the orders stalling with riders idle — and added
> bounded rider-level retry to drain every order with zero duplicates*

| Term | What it means | How we handle it |
|---|---|---|
| **Double-dispatch race** | Two replicas read the same PENDING order at the same time and both assign it — one order, two riders | Lock the row before touching it, so the second reader can't see it as available |
| **3 API replicas** | Three copies of the app behind a load balancer, sharing one database | Nothing lives in process memory; all shared state is in Postgres or Redis |
| **`SELECT … FOR UPDATE`** | Read a row *and* take an exclusive lock on it until the transaction ends | Whoever locks the order owns it — nobody else can read-to-modify it |
| **`SKIP LOCKED`** | Don't wait for a locked row; **skip it and take the next one** | A contested dispatch becomes "take a different order" instead of blocking in a queue |
| **Two-phase claim** | Lock **both** the order *and* the rider before mutating *either* | Prevents assigning an order to a rider another replica just took. If the rider claim fails, we re-select the next-best rider for the **same** order rather than dropping the order |
| **Zero duplicate assignments** | Every `order_id` and every `rider_id` appears at most once | `scripts/race_test.py`: 15 simultaneous dispatches, 3 replicas, asserts both sets are unique |

### Correct is not the same as live ⭐ (lead with this half)

Plenty of people can say they fixed a race with row locks. Almost nobody can say
they then **measured it again, found it still behaved badly, and redesigned.**
That is the rarer signal, and it is the same harness — no extra work.

**The measurement that changed the design.** Locking was correct — zero
double-assignments — and the system was still bad. 15 simultaneous dispatches, 10
orders, 10 riders, 3 replicas: only **5 succeeded**. Ten calls got 409 **while
five riders sat AVAILABLE.**

**Why.** Every concurrent caller ranks riders *identically*, because the state
that would differentiate them — the winner removing that rider from the geohash
index and bumping their `orders_today` — only lands **after commit**. So all the
losers pick the same top-ranked rider, fail the claim, and then moved on to the
**next order** — chasing that same contested rider down the entire pending queue
until they ran out. **Losing a rider lost the whole order.**

**The fix — retry the rider, keep the order.** On a failed rider claim, add that
rider to an `exclude` set and re-select the next-best **for the same order**.

- **Bounded** — the 3×3 cell ring is finite and every failure shrinks it.
- **Mutation-free** — nothing is written during the retry, so the
  claim-everything-before-you-mutate invariant survives.
- **Subtlety worth volunteering:** exclusion runs *before* the nearest-rider
  distance is computed, so the fairness band re-centres on the nearest
  **eligible** rider. The SLA bound stays relative to riders you can actually get.

**Same test after the fix: every order dispatched in one burst, still zero
doubles.**

> **Say "full drain", not "10 of 15".** 10 successes out of 15 calls sounds like
> 67% — it is actually optimal: there were only 10 orders, and the other 5 calls
> correctly returned "no pending orders". Losing a race now costs one candidate,
> not the whole request.

**A bonus it bought for free:** a stale BUSY rider left in the geohash index —
crash after commit, before the index cleanup — used to poison every order's
selection. Now it costs one failed claim and gets excluded. Self-healing.

**Soundbite:** "My locking was correct but not live. Under a burst every replica
chases the same top-ranked rider, because the state that would differentiate them
only lands post-commit — I measured 5 of 15 succeeding with riders sitting idle.
The fix is a bounded rider-level retry: exclude the contested rider and re-select
for the same order. After that, full drain, still zero doubles. Correctness and
liveness are separate properties and you have to measure both."

**The general lesson, and the best line in it:** a test that only asserts "no
duplicate assignments" **passes a system that assigns nothing at all.** Zero
throughput has zero duplicates. That is why the second measurement existed.

**If they ask "why not just a lock/mutex?"** — a mutex is per-process; three
replicas have three of them. The lock must live where the shared state is, which
is the database.

**"Why not optimistic locking?"** — optimistic assumes conflicts are rare and
retries when wrong. Here contention is the normal case, so it would thrash.

## Bullet 2 — the algorithm

> *Built the dispatch core: aging-weighted priority scheduler preventing
> starvation, and geohash matching with a fairness band that spreads work across
> idle riders*

| Term | What it means | How we handle it |
|---|---|---|
| **Priority scheduler** | Serve the most important order first, not the oldest | A max-heap ordered by score |
| **Starvation** | A low-priority item that **never** gets served because better ones keep arriving | Real risk: a cheap order behind an endless stream of expensive ones |
| **Aging** | Priority **grows with waiting time** | `score = value + minutes_waited × weight`. A cheap order that has waited long enough eventually outranks a fresh expensive one — starvation becomes impossible |
| **Geohash** | Encodes lat/lon into a short string; nearby points share a prefix | Precision 6 ≈ 1.2 km × 0.61 km cells. Riders are indexed into their cell in Redis |
| **Cell + 8 neighbours** | Search the order's cell plus the ring around it | Bounds the candidate set to 9 cells instead of scanning the whole fleet. Trade-off: a rider two cells out is not considered |
| **Fairness band** | Among riders **within 500 m of the closest one**, pick whoever has done fewest orders today | Greedy-nearest lets one rider take everything while others idle. The band trades a little distance for even distribution |

**"Why was it O(n log n), not O(log n)?"** — volunteer this; the fix is the
interesting half. `heappop` is O(log n), but every dispatch **rebuilt** the heap
from all pending orders and the build dominates. Two problems, not one: the cost
scaled with the backlog, and three API replicas each held their own heap, so no
two agreed on "the" best order. The ordering moved into SQL — `ORDER BY priority
LIMIT 1 FOR UPDATE SKIP LOCKED` — which makes Postgres the single arbiter and
stops at the first lockable row. Then load-testing the *claim* path found the
scan was still unbounded when no rider was free (1,730 orders walked to answer
"nobody is available", p99 11s), so it is capped at the top 20 — p99 2.8s.

## Bullet 3 — Kafka ⭐ (the most-probed one)

> *Streamed events to 3 Kafka consumer groups with manual offset commits for
> at-least-once delivery, idempotent consumption on `(partition, offset)`, and a
> dead-letter queue for poison messages*

| Term | What it means | How we handle it |
|---|---|---|
| **Consumer group** | A set of consumers sharing a `group.id`. **Same** id → members split the partitions (work queue). **Different** id → each group gets every message (fan-out) | Three groups — `notifications`, `analytics`, `audit` — so each gets its own full copy with its own progress |
| **Offset** | A message's position in a partition; "how far this group has read" | Stored per group, so one consumer being down doesn't affect the others |
| **Manual offset commit** | *We* decide when to record progress, rather than a background timer | `enable.auto.commit=false`. Auto-commit fires on a timer whether or not the handler finished — that silently turns at-least-once into at-most-once |
| **At-least-once** | Every message is processed **one or more** times; never lost, sometimes duplicated | Comes from commit **placement**: `poll → process → commit`. Crash before the commit and the message is redelivered |
| **Idempotent consumption** | Processing the same message twice has the same effect as once | Required, because at-least-once *guarantees* duplicates will happen |
| **`(partition, offset)`** | A message's unique coordinates in the log | Unique constraint on that pair + `ON CONFLICT DO NOTHING` — a redelivery inserts **zero rows**. Delivery stays at-least-once; the **effect** becomes exactly-once |
| **Poison message** | A message that can **never** be processed successfully — malformed JSON, a missing field, a schema change | See below |
| **Dead-letter queue (DLQ)** | A separate topic where unprocessable messages are parked with their context | `order.dispatched.dlq` |

**Poison messages and the DLQ get the full treatment in §5.6** — it is the
follow-up this bullet invites most often, so know it cold.

## Bullet 4 — security

> *Hardened after a self-audit: closed 4 unauthenticated endpoints, a forgeable
> admin JWT, and a cross-tenant idempotency leak; extended RBAC across every
> route and re-keyed Lua-atomic rate limiting to verified identity, backed by
> 71 tests*

**"71 tests", never "71 integration tests"** — the split is 47 integration
(real Postgres and Redis over HTTP) and 19 unit (config validation, middleware
key derivation), collecting as 71 because one test is parametrised over six
banned secrets. Verify it yourself:
`grep -c "^def test_" tests/*.py` and `pytest tests/ -q`.

| Term | What it means | How we handle it |
|---|---|---|
| **Unauthenticated endpoint** | Reachable with no token at all | Four of them. The worst — `PATCH /riders/{id}/location` — writes to the geohash index, so anyone could move the fleet and steer every dispatch |
| **Forgeable JWT** | The signing secret was a default published in the repo, so anyone could mint an `ops` token | Removed the default entirely: no boot without a real secret, placeholders rejected, 32-byte minimum |
| **Cross-tenant leak** | One user receiving another user's data | The idempotency key was global, so two users sending `Idempotency-Key: retry-1` collided and the second got the first's response body. Now namespaced per verified subject |
| **RBAC** | Role-Based Access Control — permissions attach to a role, not a person | `ops` / `rider` / `customer`. Roles can't be self-assigned: registration always creates a customer. **Note the verb — the audit *extended* RBAC, it didn't add it.** The role model and the status-transition actor guard already existed; the audit applied them to the routes that had no guard at all |
| **Re-keyed rate limiting** | Changed *what* the limiter counts per | Was `X-API-Key or IP` — a header the caller controls, so rotating it minted a fresh bucket. Now the verified token subject. Again **re-keyed, not added**: the atomic Lua token bucket predates the audit; the flaw was the key, not the algorithm |

**"Why 404 in one place and 403 in another?"** — a deliberate pair worth
volunteering. `GET /orders/{id}` returns **404** for an order you may not see,
because 403 would confirm the id exists and let you enumerate. But
`PATCH /riders/{id}/location` authorises **before** checking existence, because
there the id isn't secret and checking existence first would leak the fleet the
same way. **The deciding question is which fact is worth hiding.**

---

# Part 1 — Skills, and why each one

The rule for every row: **name the alternative you rejected and why.** "I used
Redis" is a fact. "I used Redis instead of an in-process dict because three
replicas each with their own counter means the real limit is 3× what I
configured" is an engineering answer.

> The **AI Engineering** line on the resume (LangGraph, RAG, embeddings, vector
> search, LLM APIs) belongs to **DocMind** and is deliberately not covered here —
> this file is DeliverIQ.

## Languages

| Skill | What it is | Where it shows | Why, and the alternative |
|---|---|---|---|
| **Python** | Interpreted, dynamically typed, huge ecosystem | The whole backend | Fastest path to a correct async web service with mature Postgres/Redis/Kafka clients. **Rejected Go** — better raw concurrency, but I'd spend the time on plumbing instead of on the dispatch algorithm |
| **C++** | Compiled, manual memory, zero-cost abstractions | Competitive programming (Codeforces Expert) | Where predictable performance and STL data structures matter. This is my DSA language, not my systems language |
| **SQL** | Declarative query language for relational data | Every read/write, plus the locking protocol | The `FOR UPDATE SKIP LOCKED` claim is *pure SQL* — the concurrency fix lives in the query, not in application code |

## Backend

| Skill | What it is | Where it shows | Why, and the alternative |
|---|---|---|---|
| **FastAPI** | Async Python web framework; generates OpenAPI from type hints | Every route | Validation and docs come from the same type annotations, so they can't drift. **Rejected Flask** (no async, no built-in validation) and **Django** (batteries I don't need — no admin, no templates, no ORM opinion) |
| **REST APIs** | Resources as nouns, HTTP verbs as actions, status codes as the contract | `/orders`, `/riders`, `/auth` | Correct status codes *are* the API: 401 vs 403, 404 vs 403, 409 for a conflict. **Rejected GraphQL** — one client, no over-fetching problem to solve |
| **SQLAlchemy** | Python ORM + query builder | All models and queries | Objects for CRUD, raw control when needed — `.with_for_update(skip_locked=True)` is ORM syntax over exact SQL. **Rejected raw psycopg2** (hand-written SQL everywhere) and **Django ORM** (comes with Django) |
| **Alembic** | Versioned, reversible schema migrations | 6 migrations in `alembic/versions/` | `create_all()` cannot alter an existing table or run in a rollback. Migrations are ordered, reviewable, and run as a **one-shot job** before the API starts — never on app boot, because 3 replicas booting = 3 concurrent migrations |
| **Pydantic** | Runtime validation from type hints | Request/response schemas | Bad input is rejected at the boundary with a 422 before it reaches business logic. Removing `customer_id` from `OrderCreate` is a *security* fix expressed as a schema change |
| **Async Python** | `async`/`await` — one thread interleaves many I/O waits | Middleware, `redis.asyncio` | I/O-bound work (DB, Redis, Kafka) spends its life waiting, so one thread can serve many requests. **The trap I hit:** a *blocking* call inside `async def` stalls every in-flight request — sync routes are fine (threadpool), sync middleware is not |
| **pytest** | Test framework — plain functions, fixtures for setup | 71 tests | Fixtures compose (`client` → `ops_client`), so setup isn't copy-pasted. **Rejected unittest** — class boilerplate for no gain |

## Data Stores

| Skill | What it is | Where it shows | Why, and the alternative |
|---|---|---|---|
| **PostgreSQL** | Relational DB, ACID, MVCC | Source of truth: orders, riders, users | I need **transactions and row locks** — the entire double-dispatch fix depends on them. **Rejected MongoDB**: no multi-row locking of the kind `SKIP LOCKED` gives, and my data is deeply relational |
| **Redis** | In-memory key-value store, single-threaded, rich data types | Rate limiter, geohash index, idempotency cache | Sub-millisecond reads for data that is *derived and rebuildable*. Nothing lives only in Redis — losing it costs a rebuild, not data |
| **pgvector** | Postgres extension for vector similarity search | **DocMind, not this project** | Vectors live next to relational data — one backup, one transaction, one connection. **Rejected Pinecone/Weaviate**: a second datastore to run and sync. Depth lives with DocMind; out of scope here |

## Distributed Systems

| Skill | What it is | Where it shows | Why |
|---|---|---|---|
| **Apache Kafka** | Distributed, partitioned, replayable **log** | `order.dispatched` + DLQ | Three consumers need the same event with independent progress. **Rejected Redis Pub/Sub** (fire-and-forget — a subscriber that's down misses the message forever) and **RabbitMQ** (a queue: once consumed, it's gone; replay isn't a feature) |
| **Event-Driven Architecture** | Services announce facts; consumers react independently | Dispatch publishes, 3 groups consume | Adding a consumer requires **zero changes** to the producer. Before this, every new side effect meant editing the dispatch function |
| **Concurrency Control** | Keeping parallel work correct | Two-phase `SKIP LOCKED` claim | Pessimistic locking, because a contested dispatch is *common*, not rare — optimistic retry would thrash |
| **Idempotency** | Same operation twice = same result as once | `Idempotency-Key` middleware, consumer dedupe | A timed-out client cannot know if its write landed. Without this, every retry double-books |
| **Rate Limiting** | Capping request rate per caller | Token bucket in Lua | Protects the service from one noisy client. See Part 2 — this is the most-probed topic |

## DevOps

| Skill | What it is | Where it shows | Why |
|---|---|---|---|
| **Docker** | Package app + deps into a portable image | Multi-stage `Dockerfile` | Node builds the React bundle in stage 1; only the built `dist/` crosses to the Python image — no Node in production |
| **Docker Compose** | Declare a multi-container stack in one file | 12 services | Healthchecks + `depends_on: condition:` mean start order is *declared*, not slept-on. One-shot `migrate` and `kafka-init` jobs gate the API |
| **GitHub Actions / CI** | Run checks automatically on every push | `.github/workflows/ci.yml` | Infra comes from the **real** `docker-compose.yml`, not a CI-only copy — so the two can't drift and a broken compose file fails CI |
| **Prometheus** | Pull-based metrics; scrapes `/metrics` | Custom app metrics | Pull means the app doesn't need to know where the monitoring lives |
| **Grafana** | Dashboards over Prometheus | Provisioned from the repo | In version control, so `docker compose down -v` can't lose it |
| **Linux / Git** | Shell, processes, signals; version control | SIGTERM handling in workers | `docker compose stop` sends SIGTERM — Python doesn't convert it to `KeyboardInterrupt`, so it needs an explicit handler |

---

# Part 2 — Rate limiting, in depth ⭐

The most-asked topic so far. Be able to do four things for each algorithm:
**draw it, write the pseudocode, name its limitation, say where it's used.**

## 2.1 Why rate limit at all

Three separate goals people conflate:

| Goal | Example |
|---|---|
| **Protect capacity** | One client's retry loop must not exhaust the DB pool |
| **Fair sharing** | One tenant must not starve the others |
| **Abuse / cost control** | Brute-force logins, scraping, LLM API spend |

They want different limits. Login gets a *strict, exact* limit; a read endpoint
gets a *generous, bursty* one. That's why you pick the algorithm per use case.

## 2.2 Fixed window

**Idea.** Chop time into fixed buckets (12:00–12:01, 12:01–12:02). Count per
bucket. Reset at the boundary.

```
limit = 5 per minute

 12:00:00                12:01:00                12:02:00
 |───────────────────────|───────────────────────|
 | ■ ■ ■ ■ ■  ✗ ✗ ✗      | ■ ■                   |
 |  count=5, then reject | counter resets to 0   |
```

**Pseudocode**

```
function allow(user, limit, window):
    now    = current_time()
    bucket = floor(now / window)          # which window we're in
    key    = "rl:" + user + ":" + bucket

    count = INCR key                      # atomic, creates at 1
    if count == 1:
        EXPIRE key window                 # only on first write

    return count <= limit
```

One command in the common case. Nothing to clean up — the key expires itself.

**Limitations**

1. **The boundary burst — the flaw interviewers fish for.** You can push **2×
   the limit** through in an instant by straddling the edge:

```
        window A               window B
 |──────────────────────|──────────────────────|
                  ■■■■■ | ■■■■■
                11:59:59  12:00:00
                  5 reqs   5 reqs   =  10 requests in ~1 second
                                       with a limit of 5/min
```

2. **Synchronised reset.** Every user's window resets at the same instant, so
   clients that poll on the minute all stampede together.
3. No smoothing at all within the window.

**Where it's genuinely used**

- Quotas that are naturally calendar-aligned: *"10,000 API calls this month"*.
  The boundary burst doesn't matter when the window is a month.
- **GitHub's REST API** uses hourly fixed windows.
- Anywhere "roughly N per period" is the actual business rule.

## 2.3 Sliding window log

**Idea.** Store a timestamp for **every** request. To decide, drop anything older
than the window and count what's left.

```
window = 60s, limit = 5, now = 12:00:30
cutoff = 11:59:30   -> anything older is evicted

sorted set (score = timestamp)
 [11:59:10]  [11:59:40] [11:59:55] [12:00:10] [12:00:25]
   evict         keep       keep       keep       keep
                        count = 4  ->  allow, then add 12:00:30
```

The window **slides continuously** — there is no edge to straddle.

**Pseudocode**

```
function allow(user, limit, window):
    now    = current_time()
    key    = "rl:" + user
    cutoff = now - window

    ZREMRANGEBYSCORE key 0 cutoff       # evict what aged out
    count = ZCARD key                   # how many still in window

    if count >= limit:
        return false                    # note: do NOT record rejects

    ZADD   key now now                  # score = value = timestamp
    EXPIRE key window
    return true
```

> **The bug to avoid:** if you `ZADD` *before* checking, a rejected request still
> occupies a slot, and a client hammering you keeps itself permanently blocked.
> Check first, or remove your own entry on reject.

**Limitations**

1. **Memory grows with traffic**, not with users. 10k users × 1000 req/min =
   10M sorted-set members held for a minute.
2. Every request does multiple writes — expensive at high volume.
3. Needs the multi-command sequence to be atomic (MULTI or Lua), or two
   concurrent requests both read `count = limit - 1` and both pass.

**Where it's genuinely used**

- **Low-volume, high-stakes endpoints** where the limit must be *exact*: login
  attempts, password reset, OTP send, payment submission.
- Compliance rules — *"no more than 3 OTPs per hour"* has to be exactly 3.
- Small volume makes the memory cost irrelevant, and exactness is the point.

## 2.4 Sliding window counter

**Idea.** The compromise. Keep only two counters — current window and previous —
and estimate the sliding count by weighting the previous one by how much of the
current window has elapsed.

```
limit = 100/min.  now = 30s into the current window (50% elapsed)

    previous window            current window
 |────────────────────────|─────────●──────────────|
        count = 80              count = 30
                             30s of 60s elapsed

 estimate = 80 × (1 − 0.5)  +  30
          = 40              +  30   =  70    ->  allow (70 < 100)
```

**Pseudocode**

```
function allow(user, limit, window):
    now      = current_time()
    curr_win = floor(now / window)
    prev_win = curr_win - 1
    elapsed  = (now mod window) / window          # 0.0 .. 1.0

    curr = GET("rl:" + user + ":" + curr_win) or 0
    prev = GET("rl:" + user + ":" + prev_win) or 0

    estimate = prev * (1 - elapsed) + curr

    if estimate >= limit:
        return false

    INCR   "rl:" + user + ":" + curr_win
    EXPIRE "rl:" + user + ":" + curr_win, 2 * window
    return true
```

**Limitations**

1. **It's an approximation.** It assumes the previous window's traffic was spread
   evenly. If all 80 requests came in that window's final second, the estimate
   *under*-counts and lets too many through.
2. Can also be slightly over-strict, rejecting a request that a true sliding
   window would allow.
3. Slightly more logic than fixed window for a benefit you must be able to
   justify.

In practice the error is tiny — **Cloudflare reported roughly 0.003% of requests
wrongly handled** at very large scale, which is why they use it.

**Where it's genuinely used**

- **High-volume public APIs and CDN edges** — Cloudflare's rate limiter.
- Anywhere fixed window's boundary burst is unacceptable but sliding log's memory
  is unaffordable. That's most large-scale HTTP rate limiting.

## 2.5 Token bucket ⭐ (what DeliverIQ uses)

**Idea.** A bucket holds up to `capacity` tokens and refills at a constant rate.
Each request spends one token. No tokens, no service.

```
capacity = 10, refill = 1 token/sec

        refill 1/sec (up to capacity)
              │
              ▼
        ┌───────────┐
        │ ● ● ● ● ● │  5 tokens   -> request takes 1 -> 4 left, ALLOW
        └───────────┘
        ┌───────────┐
        │           │  0 tokens   -> REJECT 429, Retry-After: 1
        └───────────┘

burst behaviour — the whole point:
   idle 10s   -> bucket refills to 10  -> 10 requests served instantly
   sustained  -> settles to exactly 1 req/sec
```

**Pseudocode** (this is our Lua script in plain language)

```
function allow(user, capacity, refill_rate):
    now = current_time()
    key = "rl:" + user

    (tokens, last_refill) = HMGET key, "tokens", "last_refill"

    if tokens is null:                          # first request ever
        tokens      = capacity
        last_refill = now
    else:
        elapsed = now - last_refill
        tokens  = min(capacity, tokens + elapsed * refill_rate)   # LAZY refill

    if tokens < 1:
        return false                            # 429

    tokens = tokens - 1
    HSET   key, "tokens", tokens, "last_refill", now
    EXPIRE key, ttl
    return true
```

**Two things to point out unprompted:**

- **Lazy refill.** Nothing runs in the background. Tokens are *computed* from
  elapsed time on the next request. No cron, no timer, no scheduler — a bucket
  nobody touches costs nothing.
- **This is read-modify-write**, so it must be atomic. See §3.1.

**Limitations**

1. **Needs atomicity.** Can't be a single `INCR`; requires Lua or a
   `WATCH`/`MULTI` retry loop.
2. **Allows a full burst by design** — if downstream genuinely cannot absorb
   `capacity` at once, this is the wrong choice.
3. **Two fields written per request**, versus one `INCR`.
4. **Clock skew.** Ours passes `now` from the application server. Two app servers
   with drifting clocks compute different refills for the same bucket. Using
   Redis's own `TIME` command inside the script would make one clock authoritative
   — a real improvement I'd name if asked how to harden it.

**Where it's genuinely used**

- **General-purpose API rate limiting** — AWS API Gateway, Stripe, and most
  cloud APIs are token-bucket-shaped.
- Any client that is **naturally bursty**: a web page load fires 10 calls at
  once, then idles. Fixed window rejects that legitimate burst; token bucket
  absorbs it.
- Network traffic shaping and QoS.

## 2.6 Leaky bucket

**Idea.** The mirror image. Requests enter a queue that drains at a **constant**
rate. Output is perfectly smooth; a full bucket overflows and drops.

```
   bursty in            queue (capacity)        constant out
  ■ ■■■  ■   ──────>  ┌──────────────────┐ ──────>  ■ ─ ■ ─ ■ ─ ■
                      │ ■ ■ ■ ■          │          exactly 1 per 100ms
                      └────────┬─────────┘
                               │ full? overflow -> drop (429)
```

**Pseudocode** (meter variant — no real queue, tracks the level)

```
function allow(user, capacity, leak_rate):
    now = current_time()
    (level, last_leak) = HMGET key, "level", "last_leak"

    elapsed = now - last_leak
    level   = max(0, level - elapsed * leak_rate)     # drains over time

    if level + 1 > capacity:
        return false                                  # overflow

    HSET key, "level", level + 1, "last_leak", now
    return true
```

**Token bucket vs leaky bucket — the one-liner they want:**
**token bucket allows bursts, leaky bucket forbids them.** Token bucket caps the
*average* rate while permitting a spike; leaky bucket caps the *instantaneous*
output rate, always.

**Limitations**

1. **No bursts at all** — a legitimate spike is delayed or dropped.
2. The true queue variant **adds latency** and needs memory plus a scheduler.
3. Worse user experience for interactive traffic.

**Where it's genuinely used**

- **Shaping traffic to a downstream with a hard ceiling**: a payment provider
  contractually capped at 10 TPS, or a legacy system that falls over on a spike.
- **Outbound** calls to third-party APIs with strict per-second contracts.
- Network QoS, video streaming, packet shaping.

## 2.7 Choosing — the decision table

| | Memory | Accuracy | Bursts | Cost/req | Pick it when |
|---|---|---|---|---|---|
| **Fixed window** | O(1) | Poor (2× at edges) | Accidental | 1 op | Quota is calendar-shaped; simplicity wins |
| **Sliding log** | **O(requests)** | Exact | None | Several ops | Low volume, must be exact — login, OTP, payment |
| **Sliding counter** | O(1) | ~99.997% | Smoothed | 2–3 ops | High volume, edges matter, memory doesn't allow logs |
| **Token bucket** | O(1) | Good | **Bounded, deliberate** | 1 script | General API limiting; bursty clients |
| **Leaky bucket** | O(1) | Exact output rate | **Forbidden** | 1 script | Downstream cannot absorb any spike |

**Rule of thumb to say out loud:** *"Exactness at low volume → sliding log.
Scale with edges that matter → sliding counter. Bursty clients → token bucket.
Fragile downstream → leaky bucket. Calendar quota → fixed window."*

**Why token bucket here:** DeliverIQ's callers are ordinary API clients — bursty
then idle. I wanted a bounded burst with a capped sustained rate, at O(1) memory
per user regardless of traffic.

## 2.8 The parts that aren't the algorithm

Interviewers often move here once you've named the algorithm.

**What do you key on?** Most trustworthy identifier available:
verified user id → API key → proxy-verified IP → peer address.
**Never a raw client-supplied header** — see §3.3, a real bug I shipped.

**What do you return?** `429 Too Many Requests`, plus headers so a good client
can behave:

```
HTTP/1.1 429 Too Many Requests
Retry-After: 3
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1735689600
```

Without `Retry-After` clients just retry immediately and make it worse.

**Where does it run?** Layered, cheapest first: CDN/edge → API gateway →
application. The application layer is the only one that knows *who* the user is,
which is why identity-keyed limiting lives there.

**Multiple limits at once** is normal: 10/sec **and** 1000/hour **and**
100k/month. Check all; the strictest wins.

**Fail open or closed?** If the limiter's own store is down: DeliverIQ **fails
open**, because a protective control must not cause the outage it exists to
prevent. For an auth or payment control, invert it and fail closed.

---

# Part 3 — Redis

## 3.0 What Redis actually is

An **in-memory**, **single-threaded** key-value store with real data structures
(strings, hashes, lists, sets, sorted sets).

- **In-memory** → microsecond operations, but RAM is the ceiling and it is *not*
  your source of truth.
- **Single-threaded** → each command is atomic on its own, and no two commands
  interleave. That is what makes Redis a good coordination point.

**In DeliverIQ:** rate-limit buckets, the geohash rider index, the idempotency
cache. All three are **derived** — `scripts/reindex_riders.py` rebuilds the index
from Postgres, so a flushed Redis costs a rebuild, not data.

## 3.0b How Redis is actually connected

```
REDIS_URL              redis://host:6379/0        (db 15 in tests — isolation)
      │
      ▼
redis.Redis.from_url(...)      module-level singleton, holds a CONNECTION POOL
      │                        (not one socket — the client pools internally)
      ├── redis_client          SYNC  — services, workers, /ready
      └── async_redis_client    ASYNC — middleware only
```

**Two clients, deliberately.** Routes are sync `def`, so FastAPI runs them in a
threadpool and a blocking Redis call there costs one worker thread. Middleware
runs on the **event loop**, where the same blocking call stalls every in-flight
request on the process. So middleware awaits, services don't.

**Both carry timeouts**, and this is the part people miss:

```python
socket_connect_timeout=2, socket_timeout=2, retry_on_timeout=True,
health_check_interval=30
```

The middleware's fail-open catches `redis.RedisError`. Without a socket timeout
that only fires on a **refused** connection — a Redis that accepts and then
*hangs* raises nothing and blocks forever. **The timeout is what makes the
fallback reachable.**

**No explicit connect call, and none needed:** `from_url` is lazy, so importing
this module never touches the network. The first command opens a socket.

## 3.1 Why the rate-limit script has to be atomic ⭐


The operation is **read → modify → write**. Three separate commands are three
chances to interleave:

```
Request A: reads tokens = 1
Request B: reads tokens = 1      <- before A wrote back
Request A: writes tokens = 0, allows
Request B: writes tokens = 0, allows      <- limit breached
```

A classic **race condition**. Redis being single-threaded doesn't save you: each
command is atomic, but the *sequence* isn't. The fix is to send the whole
read-modify-write as **one Lua script**, which Redis runs start to finish with
nothing interleaved.

| Option | Trade-off |
|---|---|
| **Lua script** ✅ | One round trip, atomic, no retries |
| `WATCH`/`MULTI` | Optimistic — needs a retry loop; under contention it spins |
| `INCR` alone | Atomic, but can't express "refill based on elapsed time" |

**Bonus:** `register_script()` uses `EVALSHA` — it sends the script's *hash*
rather than its body on every call, and only uploads the source if the server
doesn't know it yet.

## 3.2 Why Redis and not a variable

With 3 API replicas, an in-process counter means each replica allows the full
limit independently — **the real limit becomes 3× what you configured**, and it
changes whenever you scale. Shared state must live in a store all replicas see.
This is the single clearest example of the statelessness rule.

## 3.3 What to key on ⭐ (a real bug I shipped)

The limiter originally keyed on `X-API-Key or client.host`. A caller controls
that header, so **rotating it minted a fresh bucket every request** — a rate
limiter anyone could opt out of.

Priority order now, most trustworthy first:

1. **Verified JWT subject** — unforgeable without the signing key, and it follows
   the user across IP addresses, which is what you actually want to limit.
2. **`X-Forwarded-For`, only behind a trusted proxy.** Trusting it blindly is the
   same bypass in a different header.
3. **Peer address** — the client cannot choose it.

The key is hashed so an email never lands in a Redis key or a log line.

**Live proof:** 110 requests on one token → `101 × 200, 9 × 429`. Twenty requests
rotating `X-API-Key` → `20 × 429`. Before the fix that was `20 × 200`.

## 3.4 Redis structures used here

| Structure | Used for | Commands |
|---|---|---|
| **Hash** | Rate bucket (`tokens`, `last_refill`); rider location | `HSET`, `HMGET`, `HGETALL` |
| **Set** | Riders in a geohash cell | `SADD`, `SREM`, `SMEMBERS` |
| **String** | Idempotency cache, per-rider daily counter | `SET NX EX`, `GET`, `INCR` |

**`SET key val NX EX 30`** deserves its own note: `NX` = set only if absent,
which makes "claim this key if nobody else has" a *single atomic operation*. That
is the idempotency lock, and it's also the simplest distributed lock primitive.

**Pipelining** — matching used to issue 2 round trips per candidate rider, inside
the dispatch hot path *while holding a Postgres row lock*, so every round trip
was lock-hold time. One pipeline now: all commands sent together, all replies
read together. **Pipelining is not a transaction** — it batches network round
trips; it does not make the batch atomic.

## 3.5 TTL and expiry

Every key here expires: rate buckets 120s, idempotency 24h, daily counters 48h.
Redis expires keys **lazily** (on access) *plus* by random sampling — so a key
past its TTL may still occupy memory briefly. TTL is also the safety net for
cache correctness: even if invalidation is missed, staleness is bounded.

## 3.6 Likely follow-ups

- **"What if Redis goes down?"** The limiter **fails open** — a protective
  control must not cause the outage it prevents. For a payment or auth control
  the trade-off inverts and you fail closed.
- **"How do you know it fails open?"** Because it has socket timeouts. Without
  them the fallback only fires on a *refused* connection; a Redis that accepts
  and then hangs blocks forever. That was a real bug I fixed.
- **"Cache invalidation strategy?"** Cache-aside, and on writes I **delete**
  rather than update — a deletion can't be stale.
- **"Redis vs Memcached?"** Memcached is strings only. I need hashes, sets, TTLs
  and Lua.
- **"Is Redis persistent?"** It can be (RDB snapshots, AOF log), but I treat it
  as a cache. Everything in it is rebuildable from Postgres.

---

# Part 3b — PostgreSQL: how it's actually connected

Interviewers ask "how do you connect to the database?" far more often than they
ask about CAP. Know the wiring, not just the theory.

## 3b.1 The chain, top to bottom

```
DATABASE_URL              postgresql://user:pass@host:5432/dbname
      │                   read from .env by pydantic-settings
      ▼
create_engine(...)        ONE engine per process. Owns the connection POOL.
      │                   Not a connection — a factory with a pool behind it.
      ▼
sessionmaker(bind=engine) A factory for Sessions.
      │
      ▼
get_db()  (FastAPI dep)   ONE Session per request, closed in `finally`.
      │
      ▼
db.query(Order)...        Session borrows a connection from the pool,
                          returns it on close.
```

**The one-liner:** *"An engine per process holding a pool, a session per request
borrowing from it."*

## 3b.2 The pool, and the arithmetic

```python
engine = create_engine(
    settings.database_url,
    pool_size=20,        # kept open permanently
    max_overflow=10,     # burst above pool_size, closed when returned
    pool_pre_ping=True,  # cheap SELECT 1 before handing one out
    pool_recycle=1800,   # retire a connection before any idle timeout kills it
)
```

- **Why a pool at all** — a new Postgres connection is a TCP handshake, auth,
  *and a forked backend process* on the server. Tens of milliseconds. Reuse them.
- **The sizing** — `instances × pool_size` against `max_connections` (~100 by
  default). 3 replicas × 20 = 60, leaving room for migrations and `psql`. Do that
  arithmetic before the DB does it for you; **PgBouncer** is the next tier when
  you outgrow it.
- **`pool_pre_ping`** — without it, every Postgres restart hands out dead
  connections until each fails a real query. A self-inflicted error spike after
  routine maintenance.

## 3b.3 Session per request — and why `finally`

```python
def get_db():
    db = SessionLocal()
    try:
        yield db          # the request runs here
    finally:
        db.close()        # returns the connection to the pool, ALWAYS
```

`yield`, not `return`, makes this a FastAPI dependency with teardown. If `close()`
were skipped on an exception path, the pool would leak a connection per failed
request and the app would deadlock on the 31st. **The `finally` is the whole
point of the pattern.**

## 3b.4 Transactions

A Session opens a transaction lazily on first query and holds it until
`commit()` or `rollback()`. In DeliverIQ dispatch, that boundary *is* the
correctness mechanism: `FOR UPDATE` locks live until commit, so "claim both rows,
then mutate, then commit" is one atomic unit — and the outbox row rides the same
commit.

**Gotcha worth knowing:** after `commit()`, SQLAlchemy expires loaded attributes,
so touching `rider.current_lat` afterwards silently re-queries. Dispatch captures
what it needs into plain variables *before* committing.

## 3b.5 Migrations, not `create_all`

`Base.metadata.create_all()` only ever *creates* — it cannot add a column, change
a type, or roll back. Alembic gives ordered, reviewable, reversible revisions.

**They run as a one-shot job before the API starts**, never on app boot: three
replicas booting means three concurrent migrations racing the same DDL.

```bash
alembic revision --autogenerate -m "add outbox"   # generate, then READ it
alembic upgrade head                              # apply
alembic downgrade -1                              # step back
```

Autogenerate is a first draft, not an answer — it misses renames (it sees a drop
plus an add) and never writes your data migrations.

## 3b.6 Likely follow-ups

- **"Connection vs session vs engine?"** Engine = pool owner, one per process.
  Connection = a socket from the pool. Session = a unit of work with an identity
  map and a transaction, borrowing a connection.
- **"What if the DB goes down mid-request?"** The query raises, the dependency's
  `finally` returns the connection, and `/ready` starts reporting 503 so the load
  balancer stops routing here. `/health` stays 200 — restarting the app would not
  fix Postgres.
- **"N+1 queries?"** The classic ORM trap: one query for the list, one per row for
  a relationship. Fix with `joinedload`/`selectinload`, or measure with echoed SQL.
- **"Why not async SQLAlchemy?"** The routes are sync `def`, so FastAPI runs them
  in a threadpool and blocking there costs one worker thread, not the loop. Async
  would help under much higher concurrency; it was not the bottleneck.

---

# Part 4 — Auth: JWT, RBAC, passwords ⭐

Core SDE-1 backend territory, and the part of this project that changed most.

## 4.1 The two words, and the two status codes

**Authentication = who are you. Authorization = what may you do.**
Mixing the codes is an instant red flag.

| Code | Means | Example here |
|---|---|---|
| **401** Unauthorized | *Unauthenticated* — no token, bad token, expired token | `POST /orders` with no header |
| **403** Forbidden | Authenticated, but not allowed | A customer calling `POST /orders/dispatch` |

(The name "401 Unauthorized" is a historical misnomer — it means *unauthenticated*.)

## 4.2 What a JWT actually is

Three base64url segments joined by dots:

```
   header  .  payload  .  signature
   ▲          ▲           ▲
   {"alg":    {"sub":     HMAC-SHA256(
    "HS256",   "u@x.io",    base64(header) + "." + base64(payload),
    "typ":     "exp":       SECRET
    "JWT"}     1735…}     )
```

**The single most important fact: the payload is base64-encoded, not encrypted.**
Anyone holding the token can read every claim. The signature doesn't hide it —
it proves it hasn't been *changed*.

Two consequences:

- **Never put secrets in a JWT.** No passwords, no card numbers, no PII you
  wouldn't hand the client.
- **Never trust a decoded payload without verifying the signature.** That is the
  classic JWT hole — and the reason `jwt.decode()` in our code always passes the
  key and algorithm.

**Standard claims worth naming:** `sub` (subject/user), `exp` (expiry), `iat`
(issued at), `iss` (issuer), `aud` (audience), `jti` (unique token id, used for
revocation).

Ours carries `sub` (email), `is_admin`, `iat`, `exp`, expiring in 60 minutes.

## 4.3 Sessions vs JWT — the trade

```
 SESSIONS (stateful)                  JWT (stateless)
 login  -> server stores {sid: 7}     login  -> server SIGNS {sub, exp}
 request + cookie                     request + Bearer header
   -> DB/Redis lookup every request     -> verify signature, no lookup
 revoke = delete the session   ✅     revoke = hard              ❌
 needs shared session store    ❌     any replica verifies alone ✅
```

**Why JWT here:** three API replicas, and any of them must authenticate a caller
with no shared session store. That's the whole argument.

**The honest cost:** you cannot easily revoke. A stolen token stays valid until
`exp`.

## 4.4 The one deliberate deviation ⭐

`get_current_user` **loads the user row from Postgres** rather than trusting the
token's claims wholesale — so this isn't purely stateless, by choice.

**Why:** a token stays valid until it expires. Without the lookup, a user deleted
or demoted from `ops` a minute ago keeps full admin access for the rest of the
hour. The role that matters is the one in the database *now*, not the one signed
into the token 59 minutes ago.

That's a DB read per request, consciously paid for.

**Say it like this:** "I use JWT for stateless verification across replicas, but I
still load the user, because authorization should reflect current state. It costs
a lookup and it closes the demoted-admin window."

## 4.5 JWT vulnerabilities — the checklist

| Attack | What it is | Our answer |
|---|---|---|
| **`alg: none`** | Attacker sets the algorithm to `none` and strips the signature; a naive library accepts it | We pass `algorithms=["HS256"]` explicitly — never read the algorithm from the token |
| **Weak / leaked secret** | HS256 is only as strong as the key. Ours was `dev-only-change-me`, **published in the repo** | No default at all; boot fails without a real secret; placeholders rejected; 32-byte minimum |
| **No expiry check** | Token valid forever | `exp` is verified by the library, not by us |
| **Algorithm confusion** | Server expects RS256 (public key) but attacker signs with HS256 *using the public key as the HMAC secret* | Only HS256 is accepted here, so there's nothing to confuse |
| **Sensitive data in payload** | It's readable base64 | Payload holds an email and a boolean, nothing more |
| **Token stored in `localStorage`** | Any XSS can read it | **True of our console** — the honest answer is below |

**On storage — the trade to be able to argue:**

| | `localStorage` | `httpOnly` cookie |
|---|---|---|
| XSS can read it | **Yes** | No |
| CSRF risk | No | **Yes** — needs SameSite / CSRF tokens |
| Works cross-origin | Easy | Needs CORS + credentials |

Our React console uses `localStorage`, which is the common SPA choice and is
XSS-exposed. The stronger option is an `httpOnly`, `Secure`, `SameSite=Strict`
cookie — you trade an XSS exposure for a CSRF one, and CSRF has cleaner defences.

## 4.6 HS256 vs RS256

- **HS256** — symmetric. One secret both signs and verifies. Simple; everyone who
  can *verify* can also *forge*.
- **RS256** — asymmetric. Private key signs, public key verifies. Use it when a
  **different service** must verify tokens it should not be able to mint.

One issuer and one verifier here, so HS256 is right. If DeliverIQ split into
several services, RS256 would be the move.

## 4.7 Revocation, and the refresh-token gap

Short access token + long refresh token is the standard pattern:

```
access token   15 min, sent on every request  -> small stolen-token window
refresh token  7 days, sent only to /refresh  -> stored server-side, revocable
```

**Revocation is implemented.** Every token carries a **`jti`**, and
`POST /auth/logout` puts it on a Redis denylist with a TTL equal to the token's
*remaining* life — so the set is bounded and self-cleaning, not a session store
by the back door. Verification stays local to each replica; only the "was this
revoked" check is shared.

**The interesting part is the failure direction ⭐.** `is_revoked` **fails
CLOSED** — Redis unreachable means the token is rejected. That is the exact
opposite of the rate limiter, which fails **open**. The limiter protects
capacity, and unthrottled traffic beats an outage. This protects against a
*stolen* token, so failing open would reopen that hole precisely when the system
is already degraded. **Being able to argue both directions is the whole lesson.**

It revokes **one token, not the user** — logging out a phone should not log out a
laptop; that is what a per-token `jti` buys. Revoking every session for a user
needs a second denylist keyed on `sub` plus an issued-after timestamp.

**Still open, and worth volunteering:** no **refresh tokens**. A 60-minute access
token is the whole session. The standard split is a short access token plus a
long, revocable refresh token, which shrinks the stolen-token window.

## 4.8 RBAC, concretely

Permissions attach to a **role**, not a person.

| Role | May |
|---|---|
| `ops` | Everything — dispatch, onboard riders, any status change, `/admin/stats` |
| `rider` | Advance **only** orders assigned to them; never cancel |
| `customer` | Place orders; read only their own; never touch status |

Three rules worth stating:

1. **Roles cannot be self-assigned.** `/auth/register` always creates a customer;
   promotion is an operator action. An API that lets a caller declare itself
   `ops` is not an authorization system.
2. **The guard sits on the router, not each handler** for `/admin` — so a new
   endpoint added there is protected by default. Per-handler guards are one
   forgotten decorator away from an open route.
3. **Two orthogonal guards on status changes.** `transition()` asks *is this move
   legal?* (`PENDING → DELIVERED` is not). `assert_may_change_status()` asks *may
   this caller make it?* A customer marking their own order delivered is a
   **legal move by the wrong actor** — a state machine alone can never catch that.

## 4.9 Password hashing

**Never store passwords. Never encrypt them — hash them.** Encryption is
reversible; that's the wrong property.

- **bcrypt**, not SHA-256. Slowness is the *feature*: SHA-256 is built to be fast,
  which is exactly what an attacker with a leaked table wants. bcrypt has a
  tunable work factor.
- **Salt** — a random value per password, stored alongside the hash. Without it,
  identical passwords produce identical hashes and one rainbow table cracks
  everybody. bcrypt generates and embeds the salt automatically.
- **Constant-time comparison** — `bcrypt.checkpw` takes the same time for a wrong
  password as a right one, leaking no timing signal.
- **The 72-byte gotcha:** bcrypt silently truncates past 72 **bytes**, so two
  different long passwords can hash identically. We **reject** rather than
  truncate, so the limit is visible instead of a silent downgrade. (Bytes, not
  characters — an emoji is four.)
- **Alternatives:** Argon2id is the current recommendation (memory-hard, resists
  GPU cracking); scrypt and PBKDF2 are also acceptable. bcrypt remains fine.

**One more:** login returns **one generic message** for both "no such user" and
"wrong password". Distinguishing them turns the endpoint into an
account-enumeration oracle.

## 4.10 Likely follow-ups

- **"How do you log someone out?"** Plain JWT can't — the token stays valid until
  `exp`. I mint a `jti` per token and deny it in Redis until it would have
  expired anyway. The check fails closed, unlike the rate limiter.
- **"Why not just check `is_admin` from the token?"** Because it's a snapshot
  from issue time. I read the role from the database so a demotion takes effect
  immediately.
- **"How do you protect against brute force on login?"** Rate limiting — and
  login is exactly the case where I'd use a **sliding window log** (§2.3) rather
  than token bucket: the limit must be exact and bursts are precisely what you're
  trying to stop.
- **"What if the secret leaks?"** Rotate it. Every existing token becomes invalid
  — which is also the crude, universal revocation mechanism.
- **"HTTPS?"** Mandatory. A bearer token in plaintext over HTTP is a credential
  anyone on the path can copy and replay.

---

# Part 5 — Kafka

## 5.1 The one sentence that reframes everything ⭐

**Kafka is a log, not a queue.**

A queue *deletes* on consume. A log **appends**, retains for a period, and lets
each consumer track its own position — so three consumers can read the same
message at three different times, and re-read it tomorrow.

That is why Redis Pub/Sub wasn't enough: it is broadcast-and-forget, so a
subscriber that is down **misses the message forever**.

| | Queue (RabbitMQ) | Log (Kafka) |
|---|---|---|
| After consumption | Message gone | Message stays until retention |
| Multiple consumers | Compete for messages | Each group gets a full copy |
| Replay | Not a feature | Reset the offset |
| Ordering | Per queue | Per **partition** |

## 5.1b How Kafka is actually connected

```
KAFKA_BOOTSTRAP   kafka-1:19092,kafka-2:19092,kafka-3:19092
      │           a HANDSHAKE address list, not where you end up
      ▼
Producer({...})   one per process, lazy, background delivery thread
Consumer({...})   one per worker, subscribes, polls in a loop
```

**The bootstrap/advertised distinction — the config bug everyone hits once.**
Bootstrap is only the *first* address you dial. The broker replies with its
**advertised listener**, and the client reconnects to *that*. Get it wrong and
the client connects, then hangs forever on a healthy-looking cluster.

```
from the host       localhost:9092    (PLAINTEXT_HOST listener)
inside Compose      kafka-1:19092     (PLAINTEXT listener)
```

Same broker, two listeners, because "localhost" means different machines to a
container and to your shell. `settings.kafka_bootstrap` switches by environment —
never hardcoded.

**Producer config that matters:**

```python
"acks": "all",                    # every in-sync replica, not just the leader
"enable.idempotence": True,       # dedupe the producer's own retries
"partitioner": "murmur2_random",  # match the Java client (librdkafka defaults
                                  # to CRC32 — same key, different partition,
                                  # per-key ordering silently broken)
```

**Producing is asynchronous.** `produce()` only *enqueues*; it does no I/O and
cannot fail on a dead broker. Delivery happens on a background thread and
reports via callback. That is why anything that must be durable calls
`flush()` and checks the count of still-undelivered messages — the outbox relay
does exactly this before marking a row published.

**Consumers are a poll loop**, and `poll()` has a **three-way** return: `None`
(no message), an error, or a message. Calling `.value()` on an error object
crashes the worker — that check is not optional.

## 5.2 Topics, partitions, offsets

- **Topic** — a named stream (`order.dispatched`).
- **Partition** — an ordered, append-only sequence. A topic has N of them.
- **Offset** — a message's position within its partition. Monotonic, per
  partition.

```
order.dispatched
  partition 0:  [0][1][2][3]
  partition 1:  [0][1][2]
  partition 2:  [0][1][2][3][4]
                              ^ committed offset per consumer group
```

## 5.3 Partitions: ordering and parallelism are the same knob ⭐

**Ordering is guaranteed within a partition only — never across partitions.**

The partition is chosen by the message **key**:

```
partition = hash(key) % partition_count
```

DeliverIQ keys by `order_id`, so **every event for one order lands in the same
partition and stays ordered**. Ordering across *different* orders doesn't matter
and isn't promised.

No key → round-robin → maximum spread, **zero ordering**.

The trade-off, in one line: **more partitions = more parallelism = smaller
ordering scope.** They're the same dial.

Also: **a partition is the unit of parallelism.** 3 partitions means at most 3
consumers in a group do work. A 4th sits idle.

### The partition problems interviewers push on

| Problem | What happens | Fix |
|---|---|---|
| **Hot partition / key skew** | One key (a huge customer) dominates one partition | Better key, or composite key |
| **Head-of-line blocking** | One slow message delays everything behind it *in that partition* | Faster handler, or move slow work off the consumer |
| **Can't shrink** | Partition count can increase, never decrease | Over-provision a little at design time |
| **Increasing breaks mapping** | `hash(key) % N` changes when N changes, so a key moves to a new partition and **ordering breaks across the change** | Plan capacity up front |

## 5.4 Consumer groups: one string picks the architecture ⭐

`group.id` is the whole switch:

- **Same `group.id`** → members **split** the partitions. A work queue. Scaling
  out means adding consumers.
- **Different `group.id`** → each group gets **every** message. Fan-out.

DeliverIQ runs three groups on one topic:

| Group | Does | Independence |
|---|---|---|
| `notifications` | Sends a push | — |
| `analytics` | Writes Postgres | Can be down an hour and catch up |
| `audit` | Appends a file | No DB, so it survives a DB outage |

Three groups, **three independent failure domains, one event**. That is the
payoff of the log model, and adding a fourth consumer requires no producer change
at all.

## 5.5 Delivery semantics are a commit *placement* ⭐

Not a setting — **where you put the commit relative to the work.**

```
poll() → process() → commit()      at-least-once   (crash = redeliver)
poll() → commit() → process()      at-most-once    (crash = lost)
```

DeliverIQ commits **after** processing → at-least-once → **duplicates are
possible and must be handled.**

**Auto-commit is the trap:** `enable.auto.commit=true` fires on a *timer*,
regardless of whether your handler finished. That silently degrades
at-least-once into at-most-once. We set it to `false`.

**Exactly-once, honestly:** true end-to-end exactly-once needs Kafka
transactions. The practical version is **at-least-once delivery + an idempotent
consumer**. The analytics consumer inserts with
`ON CONFLICT DO NOTHING` on a unique constraint over `(partition, offset)` — the
message's own coordinates, guaranteed unique — so a redelivery inserts zero rows.
**Delivery stays at-least-once; the effect becomes exactly-once.**

Doing it in *one* statement matters: a `SELECT` then `INSERT` would race a second
worker and both would decide the row was absent.

## 5.6 The problems nobody mentions until asked ⭐

### Poison pill
A message that can *never* be processed — malformed payload, missing field.
Without handling, the consumer crashes, restarts, re-reads the same message, and
**wedges the partition forever**. Every valid event behind it never gets
delivered. Worse: **lag monitoring won't show it**, because a partition with no
committed offset has no lag row at all.

**Fix:** catch, publish to a **dead-letter queue** with full context, then commit.
The subtlety: **block until the DLQ publish is acknowledged before committing.**
Committing on an unacked DLQ publish advances past the message with no copy
anywhere — the one way this design can lose data.

### The dual-write problem — and the outbox that closes it ⭐
`db.commit()` and a Kafka publish are two systems with **no shared transaction**.
Crash in between and the DB has the order while the event is gone forever.
Publishing *after* commit is right as far as it goes — never announce a fact that
isn't durable — but it does not close the window.

**Fixed with a transactional outbox.** The event is written as a **row in an
`outbox` table inside the same transaction** as the order and the rider. One
commit, three facts, atomic. A relay then publishes those rows and marks them
done.

**The relay's ordering is the design, and it mirrors the consumer's commit
placement exactly:**

```
publish  ->  wait for the broker's ack  ->  THEN mark published
```

Mark first and a crash in the gap loses the event — the same hole, moved one
layer down. Publish first and a crash republishes it: at-least-once, which the
consumers already dedupe on `(partition, offset)`. Rows are claimed with
`FOR UPDATE SKIP LOCKED`, so several relays can run — the same protocol dispatch
uses on orders.

**The honest trade:** the event is no longer lost, but it is no longer instant —
it is delayed by the relay's poll interval. **You buy durability with latency.**

### Consumer lag
`lag = latest offset − committed offset`. The single best health metric: it says
"how far behind are we". Rising lag means consumers can't keep up.

### Rebalancing
When a member joins or leaves, partitions are reassigned and consumption
**pauses**. Two ways to trigger it accidentally:

- **Ungraceful exit.** `docker compose stop` sends SIGTERM, and Python does *not*
  turn that into `KeyboardInterrupt` — without a handler the process dies, the
  group holds the dead member's partitions until `session.timeout.ms` expires
  (~45s measured here), and the replacement sits idle. Hence the explicit SIGTERM
  handler and `consumer.close()`.
- **Slow processing.** Exceed `max.poll.interval.ms` and the broker assumes
  you're dead, kicks you, rebalances — and the restart is slow too, so it
  repeats. That's a **rebalance storm**.

### Retention
Messages are kept by time or size, not until consumption. A consumer down longer
than retention **loses data permanently**. Retention is a data-loss window.

## 5.7 Durability: acks and replication

| `acks` | Means | Risk |
|---|---|---|
| `0` | Don't wait | Fire and forget |
| `1` | Leader wrote it | Leader dies before replication = lost |
| `all` | All in-sync replicas have it | Slowest, safest |

DeliverIQ uses `acks=all` + `enable.idempotence=true` (dedupes producer retries).

**The story worth telling:** this used to be theatre. With a **single broker at
RF=1, "all" is one replica** — `acks=all` bought nothing, and a single disk loss
lost the log. The producer config was always right; the **topology** was the gap.

Now: **3 brokers, RF=3, `min.insync.replicas=2`** — including the internal
`__consumer_offsets` topic, because a group whose offsets live on one broker
loses its place when that broker dies.

**Why 2 and not 3:** `min.insync=3` refuses writes the moment any broker blinks;
`min.insync=1` silently accepts a write only one replica holds — the theatre
again. RF=3 with min.insync=2 survives one broker down and still takes writes.

## 5.8 One real config gotcha

librdkafka (the C/Python client) defaults to **CRC32** partitioning; the Java
client uses **murmur2**. Same key, different partition, depending on which client
wrote it — so per-key ordering silently breaks in a mixed-language shop. We pin
`partitioner=murmur2_random` to match the ecosystem default.

## 5.9 Likely follow-ups

- **"Why not RabbitMQ?"** I need replay and multiple independent readers of the
  same event. A queue deletes on consume.
- **"How do you handle duplicates?"** I assume them. At-least-once plus a unique
  constraint on `(partition, offset)`.
- **"How do you add a new consumer?"** New `group.id`, `auto.offset.reset =
  earliest`. It backfills the whole retained history with no producer change.
- **"What if a consumer is slow?"** Watch lag. Add consumers up to the partition
  count; beyond that, add partitions.
- **"How many partitions?"** Start with expected peak parallelism plus headroom.
  You can add but never remove, and adding breaks key→partition mapping.
- **"Is ordering guaranteed?"** Within a partition, yes. Across a topic, no — and
  I key by `order_id` so the ordering I actually need is the ordering I get.

---

# Part 6 — Two-minute recap

Say these out loud until they're fluent.

**Rate limiting.** Token bucket, because API clients are bursty then idle and I
wanted a bounded burst with a capped sustained rate at O(1) memory per user.
Fixed window is cheaper but lets 2× the limit through across a boundary. Sliding
log is exact but its memory grows with request volume — I'd use it for login,
where the limit has to be exact. Sliding counter is the large-scale compromise.
Leaky bucket forbids bursts entirely, which is what you want in front of a
fragile downstream. The read-modify-write runs as one Lua script because three
separate commands would race.

**Redis.** In-memory, single-threaded, holding three *derived* things: rate
buckets, the geohash index, the idempotency cache — all rebuildable from
Postgres. The limiter lives here rather than in process memory because three
replicas with local counters give you 3× your configured limit. It keys on the
verified token subject; keying on a client-supplied header let anyone mint a
fresh bucket, which was a real bug I shipped and fixed.

**Auth.** JWT over sessions because three replicas must verify with no shared
session store. The payload is base64, not encrypted — so nothing secret goes in
it and nothing is trusted without verifying the signature. One deliberate
deviation: I load the user row per request, so a demoted admin loses access
immediately instead of at token expiry. The signing secret has no default, and
the app refuses to boot without one. Revocation is a `jti` per token plus a
Redis denylist with TTL = the token's remaining life — bounded and
self-cleaning, so statelessness survives. That check **fails closed**, the
opposite of the rate limiter: the limiter protects capacity, so unthrottled
traffic beats an outage, while revocation guards a *stolen* token and failing
open would reopen the hole exactly when things are degraded. Still open: no
refresh tokens, and it revokes one token rather than every session for a user.

**Kafka.** A log, not a queue: consumption doesn't delete, so three groups read
the same event with independent offsets and a new consumer backfills history.
Keyed by `order_id`, so per-order ordering holds within a partition — ordering
and parallelism being the same dial. Commit *after* processing makes it
at-least-once, so the analytics consumer dedupes on `(partition, offset)`:
delivery stays at-least-once, the effect becomes exactly-once. Poison messages go
to a DLQ, and I only commit once that publish is acked — otherwise I'd advance
past a message with no copy of it anywhere.

**The story I volunteer.** I had the dual-write problem: dispatch committed the
order, then published to Kafka, so a crash in the gap lost the event forever. I
closed it with a transactional outbox — the event is a row written inside the
same transaction, and a relay publishes it and marks it done, in that order,
because marking first just moves the hole down a layer. You buy durability with
latency: the event is no longer lost, but it is no longer instant.

**And the one I'd lead with if they ask about measurement.** My original
benchmark hit unauthenticated `POST /orders` — a plain INSERT, no matching, no
locking, no Kafka. Pointing it at the dispatch claim instead found a real defect
in one run: with a backlog and no free riders, every call scanned the entire
pending set to answer "nobody is available" — 1,730 orders, p99 of 11 seconds.
Bounding the scan to the top 20 by priority took p99 to 2.8 s on the same
machine. **The absolute numbers describe my laptop; the comparison is the real
result — a single-host benchmark is near-worthless for capacity and excellent
for regression.**

**Still open, honestly:** no refresh tokens, revocation is per-token rather than
per-user, and the outbox relay has no depth alerting if it dies.
