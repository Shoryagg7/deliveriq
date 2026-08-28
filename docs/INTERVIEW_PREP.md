# DeliverIQ — What I Built, and Why

> **What this is.** The project story: what the system does, the decisions
> behind it, what was wrong and how I fixed it. Read it to answer *"tell me
> about your project"* and everything that follows from it.
>
> **What this is not.** A textbook. Theory — rate limiting, Redis, Postgres
> wiring, JWT, Kafka — lives in [`INTERVIEW_NOTES.md`](INTERVIEW_NOTES.md),
> which is organised the way interviewers actually ask: one term at a time.
>
> Two files, one job each. This one is *my* system; that one is the
> *fundamentals* it's built from.

---

## The opener — 20 seconds, delivered cold

> "I built a distributed order-dispatch service where three stateless API
> replicas contend for shared state. The interesting parts were concurrency
> correctness — a double-dispatch race I fixed with `SELECT … FOR UPDATE SKIP
> LOCKED` — and the consistency gap between my database and my event log, which
> is the dual-write problem."

It names a **race** and a **named problem** in fifteen seconds, and hands over
two threads to pull. The softer version, when the room isn't systems-flavoured:

> "A REST API that dispatches food-delivery orders to riders using priority
> queues, geohashing, rate limiting and event streaming — FastAPI, Postgres,
> Redis, Kafka, Docker."

**Frame it honestly, once, early:** "It's a portfolio project where I went deep
on the engineering and the trade-offs — not production experience. I can defend
every design decision and tell you what I'd change at scale."

---

## What the system does

An order comes in. Dispatch has to pick **which order** to serve next and
**which rider** gets it — while two other identical replicas are trying to do
the same thing with the same rows.

```
POST /orders          → order is PENDING
POST /orders/dispatch → pick the best order, pick the best rider,
                        claim both, assign, emit an event
PATCH /orders/{id}/status → PENDING → ASSIGNED → PICKED_UP → DELIVERED
```

Around that: JWT auth with three roles, a Redis token-bucket rate limiter,
idempotency keys, Kafka events consumed by three independent groups, Prometheus
metrics, and a React console that makes the invariants visible.

---

## The stack, and what I rejected

Interviewers ask "why X?" to find out whether you **decided** or copied a
tutorial. The answer always names a trade-off and a credible alternative.

| Choice | Why | Rejected |
|---|---|---|
| **FastAPI** | async-first, Pydantic validation, free OpenAPI | Flask (rebuild validation/docs); Django+DRF (heavy for API-only) |
| **PostgreSQL** | ACID, and the whole race fix depends on **row locks** | Mongo — no multi-row locking of the kind `SKIP LOCKED` gives, and my data is relational |
| **Redis** | shared sub-ms state across replicas | in-process memory — dies the moment there are 3 instances; Memcached — no sets or geo |
| **Kafka** | a durable, replayable **log** with independent consumers | RabbitMQ — a queue, consumption deletes, no replay; Redis Pub/Sub — fire-and-forget |
| **Docker Compose** | environment as code, one command | bare venv — not reproducible |

**The honest meta-answer:** "Kafka and Prometheus are more than a project this
size strictly needs. I added them deliberately to learn the production patterns,
and I can defend each one's trade-off rather than just list it."

---

# The five decisions worth defending

## 1. Dispatch under concurrency ⭐ — the strongest story

Three replicas, one order, one rider. This is the part of the project that has
real depth, and it took **three passes** to get right.

### Pass 1 — the lost update

Read-then-write with no lock: two replicas both read the same PENDING order,
both assign it, one order goes to two riders. The fix is pessimistic locking —
`SELECT … FOR UPDATE SKIP LOCKED`.

- `FOR UPDATE` — lock these rows until my transaction ends.
- `SKIP LOCKED` — rows someone else holds are **invisible** to me, rather than
  something I wait behind. A contested dispatch becomes "take a different order"
  instead of a queue.
- **What it costs:** with `SKIP LOCKED` you are no longer guaranteed to get the
  globally-best row — you get the best row *available to you*. That's the right
  trade for a work queue and the wrong one for, say, a ledger.

### Pass 2 — the phantom assignments (the bug was not the lock)

The lock was correct the whole time. **The mutation ordering was wrong.** The
loop set `order.status = ASSIGNED` *before* locking the rider; when the rider
turned out to be taken it did `continue` — but those mutations were still
pending in the SQLAlchemy **session**. A session is a *unit of work*, so the
next successful `commit()` flushed **everything**, including the abandoned
order's changes.

The tell: the database held more ASSIGNED orders than the API returned success
responses.

**The rule that came out of it — claim everything before mutating anything:**

```
CLAIM 1  lock the order row   (FOR UPDATE SKIP LOCKED)  → miss? next order
CLAIM 2  lock the rider row                             → miss? next rider
         ── both rows exclusively mine ──
MUTATE   status, rider_id, rider → BUSY
COMMIT
THEN     Redis (index + counter), and the outbox row is already in the commit
```

Redis writes happen **after** the commit, so a rolled-back dispatch never leaves
a bumped counter or a stale index entry. Postgres is the source of truth; Redis
only ever mirrors committed reality.

### Pass 3 — correct is not the same as live ⭐

The fixed loop had **zero** double-assignments and still behaved badly. I
measured it: 15 simultaneous dispatches, 10 orders, 10 riders, 3 replicas →
only **5 succeeded**. Ten got 409 while five riders sat AVAILABLE.

**Why.** Every caller ranks riders *identically*, because the state that would
differentiate them — the winner removing that rider from the index and bumping
their count — only lands **post-commit**. So all the losers picked the same top
rider, failed, and moved to the **next order**, chasing that same contested
rider down the queue until they ran out. **Losing a rider lost the whole order.**

**The fix — retry the rider, keep the order.** On a failed rider claim, add that
rider to an `exclude` set and re-select the next-best **for the same order**.
Bounded (candidates are finite and every failure shrinks the set) and
mutation-free, so claim-before-mutate survives.

**Same test after: 10/15 — every order dispatched, still zero duplicates.**

> **Soundbite:** "My locking was correct but not live. Under a burst every
> instance chases the same top-ranked rider, because the differentiating state
> only lands post-commit — I measured 5 of 15 succeeding with riders idle. The
> fix is a bounded rider-level retry: exclude the contested rider, re-select for
> the same order. 10 of 15 after, zero doubles. Correctness and liveness are
> separate properties and you have to measure both."

**A bonus it bought free:** a stale BUSY rider left in the index by a crash
between commit and cleanup used to poison every selection. Now it costs one
failed claim and gets excluded. Self-healing.

## 2. Matching — a cheap filter, then a precise sort

Two independent filters **in sequence**, not one step.

1. **Geohash — who is even considered.** Encode (lat, lon) into a base-32 string
   where nearby points share a prefix. Read the home cell **plus its 8
   neighbours** — a set union, constant work regardless of fleet size, instead
   of a distance calculation against every rider. At precision 6 a cell is
   ~1.2 km × 0.61 km, so the 3×3 ring reaches ~3.6 km.
2. **Haversine — how far, exactly.** Cells are approximate; haversine gives real
   great-circle distance to rank the survivors. Euclidean is wrong on a sphere.

**The boundary bug I hit live:** an order at a cell *edge* can have its nearest
rider just across the line, in a cell with a completely different geohash
string. Checking only the home cell made a rider **10 m away invisible**. That
is why it's nine cells, not one.

**Range ≠ band.** The fairness band only filters riders geohash already found. A
rider 13 km away is outside the ring, so no band size pulls them in.

## 3. The fairness band — the differentiator

```
d_min    = nearest candidate's distance
feasible = riders within d_min + Δ        (Δ = 500 m)
winner   = min(feasible) on (orders_today, distance)
```

Among riders within 500 m of the closest one, assign the one who has done the
**fewest orders today**.

**Why a hard band and not a blended score.** `α·distance + β·load` can always be
outvoted: a heavily-loaded rider who is slightly closer still wins if the
weights drift, and a badly-tuned α sends someone across the city for fairness.
The band makes the SLA a **constraint**, not a term — nobody outside Δ can win,
ever, so delivery time has a hard bound and fairness operates strictly inside
it.

**Versus the real thing:** "Swiggy optimises pure ETA. I added a bounded
fairness constraint — greedy-nearest reframed as a constrained assignment
problem. Naive nearest starves some riders and overloads others."

## 4. Scheduling — priority with aging

```
priority = value + minutes_waited × AGING_WEIGHT
```

FIFO is wrong — a ₹2000 order shouldn't wait behind a just-arrived ₹150 one. But
value-only priority **starves** the cheap order forever. Aging is the fix, and
it's the OS technique for exactly this: the longer something waits the higher it
climbs, until it outranks fresh expensive ones. Starvation becomes impossible
rather than unlikely.

**I built it as a heap first, and moving off it is the better story.** Know
`heapq` for the DSA question — min-heap, push negated keys for max behaviour.
But a per-request heap reloaded every pending order and rebuilt itself on each
call: **O(n log n)**, where the rebuild dominates the O(log n) pop and `n` is
your backlog. And it couldn't be shared — three replicas meant three heaps, none
of which agreed on "the" best order.

The ordering now lives in SQL:

```sql
ORDER BY value + minutes_waited * weight DESC
LIMIT 1 FOR UPDATE SKIP LOCKED
```

Postgres stops at the first row it can lock. One arbiter, no per-replica copies,
and the work no longer scales with how far behind you are.

**Worth volunteering:** it's `timezone('UTC', now())`, not `now()`. `created_at`
is stored naive-UTC, and subtracting a tz-aware value from a naive column is a
silent one-hour priority skew — no error, just wrong ordering.

## 5. Events — the dual write, and the outbox

**The hole.** Dispatch committed the order, then published to Kafka. Two systems,
no shared transaction: a crash in the gap leaves the order assigned and the
event **gone forever**. Post-commit publishing doesn't fix it, it just shrinks
the window.

**The fix.** The event is a **row in an `outbox` table, written inside the same
transaction** as the order and the rider. One commit, three facts, atomic. A
relay polls for unpublished rows, publishes them, marks them done.

**The ordering inside the relay is the design**, and it mirrors the consumer's
commit placement exactly: `publish → wait for the broker's ack → then mark
published`. Marking first loses the event on a crash in the gap — the same hole,
moved down a layer. Publishing first means a crash before the mark **republishes**
it: at-least-once, which consumers already dedupe on `(partition, offset)`.

**The honest trade:** the event is no longer lost, but it is no longer instant.
It's delayed by the relay's poll interval. **You buy durability with latency.**

Downstream: three consumer groups read the same topic with independent offsets
(a log, not a queue — consumption doesn't delete). Commit *after* processing
makes it at-least-once. Poison messages go to a DLQ, and the offset is only
committed once that DLQ publish is acked — otherwise you advance past a message
no copy of which exists anywhere.

---

# The audit — what was wrong, and what I did

I went through the project looking for things I'd claimed but not verified. This
section is the answer to *"how would you make this production-ready?"* — because
it's what I actually did.

### The four auth holes ⭐ (lead with this one)

`POST /orders`, `GET /orders`, `GET /riders` and `PATCH /riders/{id}/location`
were all reachable **unauthenticated**. The location one is the worst: anyone
could teleport a rider into any neighbourhood and farm every dispatch in it.

Fixed with two **orthogonal** guards, and the distinction matters:

- **Role** — "are you an operator?" Dispatch and rider onboarding are ops-only.
- **Ownership** — "is this *your* row?" A rider may advance only the order
  assigned to them, and a customer sees only their own orders.

Role alone is not enough: every rider passing a role check could still move
every *other* rider. **401 = who are you; 403 = I know who you are, and no.**

### The signing key had a working default

`jwt_secret` had a default value in config. Anyone with the repo could mint an
ops token for any deployment that forgot to override it. Now it has **no
default**, there's a banned-values list, a 32-byte minimum, and the app
**refuses to boot** without one. `verify.sh` proves it by forging a token with
the old shipped secret and asserting a 401.

The test that caught my own mistake here: my first "missing secret" test passed
vacuously, because `_env_file=None` doesn't suppress `os.environ`. **Always run
the control.**

### Durability theatre → real replication

One broker, RF=1, `acks=all`. "All" was one replica — theatre. Now **three
brokers, RF=3, `min.insync.replicas=2`**, including the internal
`__consumer_offsets` topic (a group whose offsets live on one broker loses its
place when that broker dies).

**Why 2 and not 3:** `min.insync=3` refuses writes the moment any broker blinks;
`min.insync=1` silently accepts a write only one replica has — theatre again.
RF=3 with min.insync=2 survives one broker down and still accepts writes. **The
producer config was always right; the topology was the gap.**

### Token revocation

Every token now carries a **`jti`**, and `POST /auth/logout` puts it on a Redis
denylist with TTL = the token's remaining life — bounded and self-cleaning, so
it isn't a session store by the back door.

**The interesting part is the failure direction.** `is_revoked` **fails CLOSED**:
if Redis is unreachable, the token is rejected. That's the exact opposite of the
rate limiter, which fails **open**. The limiter protects capacity, and
unthrottled traffic beats an outage; revocation guards a *stolen* token, and
failing open would reopen that hole precisely when the system is degraded.
**Being able to argue both directions is the whole lesson.**

The console demonstrates it rather than claiming it: after logging out it
replays the same token against `/auth/me` and reports the 401. Without that,
real revocation and a purely local `localStorage` clear look identical.

### The foreign key

`orders.customer_id` is now a real FK to `users.id`, `ON DELETE RESTRICT`.
Ownership was already enforced in the handler; this makes the **database**
enforce it, because handler-level invariants get bypassed by scripts, fixtures,
and the next endpoint someone adds. RESTRICT not CASCADE: deleting a customer
should fail loudly, not silently vaporise their order history.

### The benchmark, and the defect it found ⭐

The old headline measured unauthenticated `POST /orders` — a plain INSERT, no
auth, no matching, no locks. The number was real and the claim attached to it
was not. Pointing the load profile at the **claim** path found a real defect in
one run:

**With a large backlog and no free riders, every dispatch walked the *entire*
pending set to answer "nobody is available"** — 1,730 orders scanned, holding
row locks the whole way. Dispatch p99: **11 seconds**.

**The fix:** `MAX_ORDERS_SCANNED = 20`. If the top 20 by priority have no
claimable rider, that's a **supply** problem and scanning further cannot conjure
one. The cost is a rare false 409 when the only free rider is far down the
queue — cheap, because the caller just dispatches again.

*50 users, 60 s, limiter off, 3 replicas, same machine:*

| dispatch claim | RPS | p50 | p95 | p99 | max |
|---|---|---|---|---|---|
| **before** | 9.3 | 1700 ms | 8200 ms | **11000 ms** | 17000 ms |
| **after** | 14.3 | 1600 ms | 2300 ms | **2800 ms** | 3100 ms |

Aggregate went 39.0 → 57.6 RPS.

**How to quote this honestly.** API, Postgres, Redis and three Kafka brokers all
share one laptop, so **the absolute numbers characterise my machine, not the
design** — never present them as capacity. What *is* valid is the comparison:
same host, same load, one variable changed, p99 down 4×. **A single-host
benchmark is near-worthless for capacity and excellent for regression.** Saying
that says something true about benchmarking instead of something flattering
about the project.

### The concurrency proof, in CI

`scripts/race_test.py` was a script someone had to remember to run — not
regression protection. It's now a CI job that boots the stack with
`--scale api=3` and fails the build on any duplicate. One test also produces and
consumes against a **real broker**, because everything else patches the
publisher — the suite could have stayed green while serialisation or the
partitioner was broken.

**A wrinkle worth telling:** that test builds a real producer, which is a module
global, so every test after it tripped the "no real producer" control and errored
in teardown — 51 errors from one new test. The fixture now resets it. **A
test-isolation control is itself something that can break.**

---

## What's still open, honestly

None of it is load-bearing for the demo, and volunteering it is worth more than
hiding it.

- **Revoking every session for a user** — one token at a time today. Needs a
  `sub`-keyed denylist plus an issued-after timestamp.
- **No refresh tokens.** A 60-minute access token is the whole session.
- **The relay is single-instance in practice.** Written to be safe with several
  (`SKIP LOCKED`), but only one runs, and nothing alerts on outbox depth.
- **`MAX_ORDERS_SCANNED = 20` is a chosen constant, not a tuned value.**
- **Numbers are single-host.** Valid for regression, not capacity.

## Deliberate, not missing

State these as choices: the fairness band Δ is a fixed constant rather than
per-city-tuned; `orders_today` resets at **UTC** midnight rather than the
business timezone; there's no rider-penalty tracking (order state and rider
penalties are deliberately independent state spaces); and there's no circuit
breaker — timeouts plus a bounded retry cover the failures this system has.

---

# The six stories to have ready

Every one is: situation → decision *and the alternative* → measured result →
what I'd change.

1. **The phantom assignments** — the lock was right, the mutation ordering was
   wrong; a session commits the whole unit of work.
2. **Correct but not live** — zero doubles and still only 5 of 15 dispatching;
   measured, diagnosed, fixed, re-measured to 10 of 15.
3. **The boundary cell** — a rider 10 m away invisible because I checked one
   geohash cell instead of nine.
4. **The 200 with the broker down** — `produce()` does no I/O, so it cannot
   fail; the event died in a memory buffer.
5. **The benchmark that found a bug** — measuring the right endpoint turned a
   vanity number into an 11 s p99 and a fix.
6. **The test that proved nothing** — a patch that silently didn't apply, and
   why you always run the control.

## How to answer anything

- **Clarify → structure → answer → trade-off.** Restate the question, say the
  shape ("two parts: the mechanism, then when it breaks"), fill it in, then name
  the alternative you rejected and why.
- **No tool is "better", it's better *for* something.** "Redis over Memcached
  because sorted sets and geo" beats "Redis is fast."
- **Say "it depends", then immediately say on what.** "Pessimistic or
  optimistic? Depends on contention: hot dispatch queue → locks; rare profile
  edits → versions."
- **When you don't know, reason out loud from what you do know.** "I haven't
  used Cassandra, but it's AP and write-optimised, so I'd expect…" beats a
  memorised fact.

## Can you, without notes…

- [ ] deliver the opener in under twenty seconds
- [ ] tell the three passes of the concurrency story, with the numbers
- [ ] explain `SKIP LOCKED` **including what it costs**
- [ ] argue the fairness band against a blended score
- [ ] sketch the outbox and say exactly which window it closes
- [ ] give both fail directions — limiter open, revocation closed — and why
- [ ] quote the benchmark *with* the single-host caveat
- [ ] name the five open gaps and their fixes

*Depth on any term above — Redis, Kafka, JWT, rate limiting, Postgres wiring —
is in [`INTERVIEW_NOTES.md`](INTERVIEW_NOTES.md).*
