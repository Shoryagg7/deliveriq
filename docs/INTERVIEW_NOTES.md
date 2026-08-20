# DeliverIQ — Interview Notes

> **What this is.** A refined companion to `INTERVIEW_PREP.md`. That file is the
> deep study ladder; this one is the two things interviews actually spend time
> on: **the skills on my resume** (what each is, why I chose it, what I rejected)
> and **Redis + Kafka in depth**, because that is where every follow-up has gone
> so far.
>
> Written to be read cold the night before. Short definitions, one table per
> idea, one soundbite each.
>
> **Start at Part 0.** It decodes every technical term on the resume bullets —
> if a word is on the page, an interviewer can ask what it means.

---

# Part 0 — Your resume, decoded

**The drill: an interviewer picks one word off your resume and asks "what does
that mean?"** Every term below is on the page, so every term is fair game. One
line each — the depth is in Parts 2 and 3.

## Bullet 1 — concurrency

> *Eliminated a double-dispatch race across 3 API replicas with a two-phase
> `SELECT FOR UPDATE SKIP LOCKED` claim protocol; verified zero duplicate
> assignments under concurrent load*

| Term | What it means | How we handle it |
|---|---|---|
| **Double-dispatch race** | Two replicas read the same PENDING order at the same time and both assign it — one order, two riders | Lock the row before touching it, so the second reader can't see it as available |
| **3 API replicas** | Three copies of the app behind a load balancer, sharing one database | Nothing lives in process memory; all shared state is in Postgres or Redis |
| **`SELECT … FOR UPDATE`** | Read a row *and* take an exclusive lock on it until the transaction ends | Whoever locks the order owns it — nobody else can read-to-modify it |
| **`SKIP LOCKED`** | Don't wait for a locked row; **skip it and take the next one** | A contested dispatch becomes "take a different order" instead of blocking in a queue |
| **Two-phase claim** | Lock **both** the order *and* the rider before mutating *either* | Prevents assigning an order to a rider another replica just took. If the rider claim fails, we re-select the next-best rider for the **same** order rather than dropping the order |
| **Zero duplicate assignments** | Every `order_id` and every `rider_id` appears at most once | `scripts/race_test.py`: 15 simultaneous dispatches, 3 replicas, asserts both sets are unique |

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

**"Why is it O(n log n), not O(log n)?"** — volunteer this before they find it.
The `heappop` is O(log n), but every dispatch **rebuilds** the heap from all
pending orders, and the build dominates. The fix is to push the ordering into
SQL: `ORDER BY priority LIMIT 1 FOR UPDATE SKIP LOCKED`.

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

### Poison messages, in full ⭐

**The problem.** A consumer reads a bad message, the handler throws, the process
dies. It restarts, reads *the same message*, throws again. Forever. The partition
is **wedged**, and every valid event queued behind it is never delivered.

**The part that makes it nasty:** monitoring won't catch it. Lag is
`latest offset − committed offset`, and a partition that has **never committed**
has no lag row at all. The system looks fine while a third of your traffic is
frozen.

**How we handle it — three steps, and the order matters:**

1. **Catch every exception** in the handler. Never let one message kill the loop.
2. **Publish to the DLQ** with full context: original topic, partition, offset,
   key, raw payload, the error, and a timestamp — enough to replay or debug it
   later without the original message.
3. **Block until the DLQ publish is acknowledged, and only then commit.**

Step 3 is the subtle one and the best thing to say out loud: *committing on an
unacknowledged DLQ publish would advance past the message with no copy of it
anywhere.* That is the one way this design can lose data. If the DLQ publish
isn't confirmed, we stop **without** committing, so the message is redelivered
rather than lost.

**Soundbite:** "A poison message is one that can never succeed, so a naive
consumer crash-loops on it and wedges the partition — invisibly, because a
partition with no committed offset reports no lag. I catch it, publish it to a
dead-letter topic with its coordinates and payload, block until the broker acks
that publish, and only then commit. If the DLQ publish isn't confirmed I don't
commit at all — I'd rather redeliver than advance past a message I have no copy
of."

**Likely follow-up — "what gets into the DLQ, and then what?"** In practice:
schema changes, a producer bug, or a field a consumer assumed was always present.
You alert on DLQ depth, inspect the payloads, fix the consumer, and replay the
topic from a saved offset. A DLQ nobody monitors is just a slower way to lose
messages.

## Bullet 4 — security

> *Audited and hardened the API: closed 4 unauthenticated endpoints, a forgeable
> admin JWT, and a cross-tenant idempotency-cache leak; extended RBAC across
> every route and re-keyed rate limiting to verified identity, backed by 71 tests*

| Term | What it means | How we handle it |
|---|---|---|
| **Unauthenticated endpoint** | Reachable with no token at all | Four of them. The worst — `PATCH /riders/{id}/location` — writes to the geohash index, so anyone could move the fleet and steer every dispatch |
| **Forgeable JWT** | The signing secret was a default published in the repo, so anyone could mint an `ops` token | Removed the default entirely: no boot without a real secret, placeholders rejected, 32-byte minimum |
| **Cross-tenant leak** | One user receiving another user's data | The idempotency key was global, so two users sending `Idempotency-Key: retry-1` collided and the second got the first's response body. Now namespaced per verified subject |
| **RBAC** | Role-Based Access Control — permissions attach to a role, not a person | `ops` / `rider` / `customer`. Roles can't be self-assigned: registration always creates a customer |
| **Re-keyed rate limiting** | Changed *what* the limiter counts per | Was `X-API-Key or IP` — a header the caller controls, so rotating it minted a fresh bucket. Now the verified token subject |

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

# Part 2 — Redis deep dive

## 2.1 What Redis actually is

An **in-memory**, **single-threaded** key-value store with real data structures
(strings, hashes, lists, sets, sorted sets).

Two consequences that explain most interview answers:

- **In-memory** → microsecond operations, but RAM is the limit and it is *not*
  your source of truth.
- **Single-threaded** → every command is atomic on its own. No two commands
  interleave. This is why Redis is a good place to coordinate.

**In DeliverIQ:** rate-limit buckets, the geohash rider index, and the
idempotency cache. All three are **derived** — `scripts/reindex_riders.py`
rebuilds the index from Postgres, so a flushed Redis costs a rebuild, not data.

## 2.2 Rate limiting — the four algorithms ⭐

**This is the most-asked topic. Know all four and why you picked yours.**

### Fixed window

Count requests per fixed clock bucket. Reset at the boundary.

```
INCR  rate:user1:12:00      -> 1, 2, 3 ...
EXPIRE rate:user1:12:00 60
```

- ✅ Simplest. One counter, one command.
- ❌ **The boundary burst.** Limit 100/min: 100 requests at `11:59:59` and 100 at
  `12:00:00` = **200 requests in one second**, and both windows are "within
  limit". This is the flaw the interviewer is fishing for.

### Sliding window log

Store a timestamp for **every** request in a sorted set; count what's left in the
window.

```
ZREMRANGEBYSCORE key 0 (now-60)    # drop what aged out
ZADD  key now now
ZCARD key                          # how many remain
```

- ✅ Perfectly accurate. No boundary problem at all.
- ❌ **Memory scales with traffic.** 1000 req/min × 10k users = 10M entries held.

### Sliding window counter

The compromise: keep the current window's counter *and* the previous one, then
weight the previous by how far into the current window you are.

```
estimate = prev_count * (1 - elapsed_fraction) + curr_count
```

- ✅ Two counters, near-accurate. This is what Cloudflare uses.
- ❌ An approximation — assumes the previous window's traffic was evenly spread.

### Token bucket ⭐ (what DeliverIQ uses)

A bucket holds up to `capacity` tokens and refills at a steady rate. Each request
spends one. Empty bucket = 429.

```
tokens = min(capacity, tokens + elapsed_seconds * refill_rate)
if tokens < 1: reject
tokens -= 1
```

- ✅ **Allows bursts up to capacity, then settles to the refill rate.**
- ✅ Constant memory: two fields (`tokens`, `last_refill`) no matter the traffic.
- ✅ **Lazy refill** — no background timer or cron. The refill is *computed* from
  elapsed time on the next access. Nothing runs when nobody calls.

### Which to pick

| | Memory | Accuracy | Bursts | Complexity |
|---|---|---|---|---|
| Fixed window | Tiny | Poor (boundary) | Accidental, at boundaries | Trivial |
| Sliding log | **Grows with traffic** | Exact | None | Medium |
| Sliding counter | Tiny | Good | Smoothed | Medium |
| **Token bucket** | Tiny | Good | **Deliberate, bounded** | Low |
| Leaky bucket | Tiny | Exact output rate | **None — fully smoothed** | Medium |

**Leaky bucket** is the one people forget: requests queue and drain at a constant
rate, so output is perfectly smooth and *no* burst gets through. That's the
difference — **token bucket allows bursts, leaky bucket forbids them.** Use leaky
when the thing downstream genuinely cannot absorb a spike.

**Why token bucket here:** real clients are bursty and then idle — a page load
fires 10 calls at once, then nothing for a minute. Fixed window would reject that
legitimate burst; token bucket absorbs it and still caps the sustained rate.

**Soundbite:** "Token bucket, because API traffic is bursty by nature and it lets
me allow a bounded burst while capping the sustained rate. Fixed window is
cheaper but has the boundary problem — double the limit across a window edge.
Sliding log fixes that exactly but its memory grows with request volume. Token
bucket is two fields per user regardless of traffic, and the refill is computed
lazily from elapsed time, so there's no timer anywhere."

## 2.3 Why the script has to be atomic ⭐

The operation is **read → modify → write**. Three separate commands are three
chances to interleave:

```
Request A: reads tokens = 1
Request B: reads tokens = 1      <- before A wrote back
Request A: writes tokens = 0, allows
Request B: writes tokens = 0, allows      <- limit breached
```

That's a classic **race condition**. Redis being single-threaded doesn't save
you: each command is atomic, but the *sequence* isn't.

The fix: send the whole read-modify-write as **one Lua script**. Redis executes
it start to finish with nothing interleaved.

| Option | Trade-off |
|---|---|
| **Lua script** ✅ | One round trip, atomic, no retries |
| `WATCH`/`MULTI` | Optimistic — needs a retry loop; under contention it spins |
| `INCR` alone | Atomic, but can't express "refill based on elapsed time" |

**Bonus:** `register_script()` uses `EVALSHA` — it sends the script's *hash*
rather than its body on every call, and only uploads the source if the server
doesn't know it yet.

## 2.4 Why Redis and not a variable

With 3 API replicas, an in-process counter means each replica allows the full
limit independently — **the real limit becomes 3× what you configured**, and it
changes whenever you scale. Shared state must live in a store all replicas see.
This is the single clearest example of the statelessness rule.

## 2.5 What to key on ⭐ (a real bug I fixed)

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

## 2.6 Redis structures used here

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

## 2.7 TTL and expiry

Every key here expires: rate buckets 120s, idempotency 24h, daily counters 48h.
Redis expires keys **lazily** (on access) *plus* by random sampling — so a key
past its TTL may still occupy memory briefly. TTL is also the safety net for
cache correctness: even if invalidation is missed, staleness is bounded.

## 2.8 Likely follow-ups

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

# Part 3 — Kafka deep dive

## 3.1 The one sentence that reframes everything ⭐

**Kafka is a log, not a queue.**

A queue *deletes* a message when it is consumed. A log **appends**, keeps
messages for a retention period, and lets each consumer track its own position.
So the same message can be read by three different consumers at three different
times — and re-read tomorrow.

That is exactly why Redis Pub/Sub wasn't enough: Pub/Sub is
broadcast-and-forget, so a subscriber that is down **misses the message forever**.

| | Queue (RabbitMQ) | Log (Kafka) |
|---|---|---|
| After consumption | Message gone | Message stays until retention |
| Multiple consumers | Compete for messages | Each group gets a full copy |
| Replay | Not a feature | Reset the offset |
| Ordering | Per queue | Per **partition** |

## 3.2 Topics, partitions, offsets

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

## 3.3 Partitions: ordering and parallelism are the same knob ⭐

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

## 3.4 Consumer groups: one string picks the architecture ⭐

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

## 3.5 Delivery semantics are a commit *placement* ⭐

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

## 3.6 The problems nobody mentions until asked ⭐

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

### The dual-write problem (my honest open gap)
`db.commit()` and the Kafka publish are two systems with **no shared
transaction**. Crash in between and the DB has the order while the event is lost
forever.

Publishing *after* commit is correct as far as it goes — never announce a fact
that isn't durable — but it doesn't close the window.

**Fix: transactional outbox.** Write the event to an `outbox` table *inside the
same DB transaction*, then a relay process reads that table and publishes. One
atomic write, at-least-once publishing, which the idempotent consumers already
absorb. **This is the thing I'd build next.**

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

## 3.7 Durability: acks and replication

| `acks` | Means | Risk |
|---|---|---|
| `0` | Don't wait | Fire and forget |
| `1` | Leader wrote it | Leader dies before replication = lost |
| `all` | All in-sync replicas have it | Slowest, safest |

DeliverIQ uses `acks=all` + `enable.idempotence=true` (dedupes producer retries).

**The honest caveat, worth volunteering:** with a **single broker and
replication-factor 1, "all" is one replica** — so `acks=all` provides no real
durability. The producer config is right; the *topology* isn't. Production needs
3 brokers, RF=3, `min.insync.replicas=2`.

## 3.8 One real config gotcha

librdkafka (the C/Python client) defaults to **CRC32** partitioning; the Java
client uses **murmur2**. Same key, different partition, depending on which client
wrote it — so per-key ordering silently breaks in a mixed-language shop. We pin
`partitioner=murmur2_random` to match the ecosystem default.

## 3.9 Likely follow-ups

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

# Part 4 — Two-minute recap

**Redis.** In-memory, single-threaded, used for three derived things: rate
limiting, the geohash index, idempotency. Token bucket over fixed/sliding window
because API traffic is bursty and I wanted a bounded burst with a capped
sustained rate. The read-modify-write is a Lua script so it's atomic — three
separate commands would race. It lives in Redis rather than memory because three
replicas with local counters give you 3× your configured limit. It keys on the
verified token subject, because keying on a client-supplied header let anyone
mint a fresh bucket — a real bug I found and fixed.

**Kafka.** A log, not a queue: consumption doesn't delete, so three groups read
the same event with independent offsets and a new consumer backfills history.
Keyed by `order_id`, so per-order ordering holds within a partition — ordering
and parallelism being the same dial. Commit *after* processing, which makes it
at-least-once, so the analytics consumer dedupes on `(partition, offset)`:
delivery stays at-least-once, the effect becomes exactly-once. Unprocessable
messages go to a DLQ, and I only commit once that publish is acked — otherwise
I'd advance past a message with no copy of it anywhere.

**The gap I volunteer:** no transactional outbox. A crash between the DB commit
and the Kafka publish loses the event. That's the dual-write problem, and the fix
is an outbox table written inside the order's transaction with a relay publishing
from it.
