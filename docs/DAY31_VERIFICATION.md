# Day 31 — Independent Verification Report

**Verified:** 2026-07-18 · re-ran every claim against a live broker, not the notes.

**Verdict: the Kafka work is correct.** Every technical claim in the Day 31 plan
reproduced exactly. Six issues found — one is a genuine environment hazard, one
is a factually wrong explanation in PLAN.md that would hurt in an interview, one
was 3264 rows of stale load-test data (traced and cleaned, §6), and the rest are
hygiene.

---

## ✅ Confirmed correct (reproduced live)

| Claim | Evidence |
|---|---|
| Config resolves to host default | `settings.kafka_bootstrap` → `localhost:9092` |
| Listener split is right | compose: `PLAINTEXT://kafka:19092`, `PLAINTEXT_HOST://localhost:9092`; api overrides to `kafka:19092` |
| **murmur2 partitioning** | 10 keys → **p0:{1,5,7,8} p1:{4,6,10} p2:{2,3,9}** — exact match to the Java table |
| `produce()` does no I/O | returned in **0.0021s** against a dead broker, no exception |
| Delivery callbacks fire with real offsets | `topic=... partition=N offset=N` on all 10 |
| `flush_producer` surfaces loss | `kafka flush timed out — 1 messages UNDELIVERED` |
| Post-commit placement, keyed by `order_id` | [dispatch.py:94-98](app/services/dispatch.py#L94-L98) |
| Lifespan replaces deprecated `on_event` | [main.py:21-27](app/main.py#L21-L27) |
| Redis-publish version preserved in history | commit `b1e132e` — the "felt the flaw, then upgraded" story is intact |
| Test suite | 9 passed |

The partitioner pin is the strongest piece of work here and it holds up perfectly.

---

## 🔴 1. Postgres split-brain (highest impact, not a Kafka bug)

`docker-compose.yml` remapped the db to `5433:5432`, but `.env` still says
`localhost:5432`. Both ports are live and **both hold a fully migrated schema**:

| Port | Server | `orders` rows | Who writes to it |
|---|---|---|---|
| 5432 | PostgreSQL 18.4 **(Ubuntu — host install)** | **3267** → 3 after cleanup (§6) | host app + pytest (hybrid dev mode) |
| 5433 | PostgreSQL 18.4 **(Debian — compose)** | **2** | containerized `api` |

Nothing errors, which is what makes it dangerous — the environment silently
forked in two. Whichever side you verify a change on, the other is stale. The two
row counts show this has been true for a while.

The port bump was almost certainly a fix for a bind conflict with the host
Postgres, and it is bundled into the Day 31 diff without being part of Day 31.

**Fix:** decide which DB is canonical. For hybrid dev mode, point `.env` at the
compose one — `DATABASE_URL=...@localhost:5433/deliveriq_db` — and update
`.env.example` to match, or stop the host Postgres and restore `5432:5432`.

## 🟠 2. Tests give false confidence about Kafka

`tests/` has no Kafka mocking or fixture. With the broker dead:

```
KAFKA_BOOTSTRAP=localhost:9099 pytest -q   →  9 passed  (25.72s)
healthy broker                             →  9 passed  ( 1.13s)
```

Green either way. The 22× slowdown is the producer's teardown blocking on a
buffer that will never drain — the only visible symptom, and it's easy to miss.
Add an autouse fixture that monkeypatches `publish_event` and asserts it was
called with the right topic/key; that turns a silent hole into a real assertion.

## 🟠 3. PLAN.md's dual-write explanation names the wrong error

The notes say the outage event *"died on `UNKNOWN_TOPIC_OR_PART` on reconnect."*
Reproduced directly — that is not the mechanism:

```
Producer({'message.timeout.ms': 3000}) → dead broker
CALLBACK err = KafkaError{code=_MSG_TIMED_OUT, "Local: Message timed out"}
```

What actually happens: the message sits in the local queue and **keeps retrying**
for `message.timeout.ms`, then is dropped as `_MSG_TIMED_OUT`. That's why the
6-second flush earlier reported it as *undelivered-but-still-buffered* rather
than failed.

This matters for the interview answer — the honest version is stronger:

> The 200 is returned before any I/O happens, so the API cannot know. The event
> survives in an in-process buffer and retries, so a *short* outage is invisibly
> survived. It's lost when either the retry window expires or the process exits —
> and the buffer is memory, so a deploy or crash during the outage loses it with
> no trace. Postgres says ASSIGNED, Kafka has nothing, and nothing rolled back.

That "the durability window is a memory buffer" framing is the actual argument
for the outbox, and it's a better one than a topic-metadata error.
---

## 🧹 4. Load-test data in the host DB — traced and cleaned

Follow-up to §1: the host DB's 3267 orders were **not** real dev data.

**Provenance.** 3263 of them were created on **2026-07-06**, and 2640 landed in a
single minute:

| Minute | Orders |
|---|---|
| 05:25 | **2640** |
| 05:24 | 451 |
| 05:21 | 170 |

That is [locustfile.py](locustfile.py) — the Day 27 load test, 50 virtual users
POSTing `/orders` (file last modified Jul 6 **05:13**, eight minutes before the
burst). It ran with `RATE_LIMIT_ENABLED=false`, which is why ~44/s sailed past the
limiter's 100/min cap — matching the "~123 RPS, p99 220ms" run recorded in
[Interview_prep.md:1721](docs/Interview_prep.md#L1721).

**Why it wasn't harmless.** [dispatch.py:24](app/services/dispatch.py#L24) loads
every `PENDING` row into memory and heapifies it, so **all 3264 rows were scanned
on every single dispatch call** — including the Day 31 Kafka dispatches. It also
meant any manual dispatch picked a random Locust order instead of one you'd just
created. Invisible on the 2-row compose DB; that asymmetry is exactly what §1
warns about.

**The cleanup.** Locust hardcodes `pickup_lat=28.61, pickup_lon=77.20`
([locustfile.py:15-16](locustfile.py#L15-L16)), giving an exact fingerprint —
3264 rows, all `PENDING`, all `rider_id NULL`, zero FK dependents:

```bash
# 1. back up first — this is what makes the rest safe
PGPASSWORD=password pg_dump -h localhost -p 5432 -U deliveriq_user \
  -d deliveriq_db -t orders --data-only -f orders_backup.sql

# 2. dry run — same predicate you're about to delete with
SELECT count(*) FILTER (WHERE pickup_lat=28.61 AND pickup_lon=77.20) AS will_delete,
       count(*) FILTER (WHERE NOT (pickup_lat=28.61 AND pickup_lon=77.20)) AS will_keep
FROM orders;                                    -- 3264 / 3

# 3. delete in an explicit transaction
BEGIN;
DELETE FROM orders WHERE pickup_lat = 28.61 AND pickup_lon = 77.20;
SELECT count(*) FROM orders;                    -- sanity check, still rollback-able
COMMIT;

# 4. reset the sequence (DELETE never rolls one back)
ALTER SEQUENCE orders_id_seq RESTART WITH 4;
```

Step 2 is the one people skip. Running the count with the *same* predicate catches
a typo'd or over-broad `WHERE` while it's still free.

**Result:** 3264 deleted; orders 1–3 and all 3 riders intact; sequence restarted so
the next order is id 4 (verified via `pg_sequences.last_value IS NULL`).

> Anomaly worth recording: the pre-reset read of `orders_id_seq.last_value`
> returned `4`, contradicting the backup's `setval('orders_id_seq', 3267, true)`.
> The dump is authoritative — the sequence really was at 3267. The intermediate
> reading is unexplained; the end state was confirmed twice independently.

**The structural fix is isolation, not cleanup.** Cleaning up *after* a load test
is easy to forget — this sat for 12 days. Point load tests at the **compose**
Postgres, where the reset button already exists (`docker compose down -v`). The
host Postgres has no such reset, which is precisely why junk accumulated there and
nowhere else. If load tests must stay on the host DB, make the run self-cleaning:
the `28.61/77.20` coords already work as a marker, so add a teardown step to the
Day 27 notes.

Related: with the table back to 3 rows, `pick_next_order`'s full-scan-and-heapify
stops being visible. It's still there. A `LIMIT` plus an index on `status`, or
moving the priority calc into SQL, is the real fix — worth doing before the next
benchmark rather than after the next pile-up.

---

## Design notes (not bugs — worth having an answer ready)

- **`produce()` post-commit can still raise.** On local queue-full it throws
  `BufferError` *after* the DB commit, so the request 500s while the order is
  already `ASSIGNED`. Same divergence as the outage case, opposite symptom. The
  no-try/except choice is right for Day 31 — just know this is the second face of
  the same hole.
- **`flush_producer(5.0)` drops on timeout.** On SIGTERM it logs the loss and
  exits. Correct and honest for now; the outbox is what actually fixes it.
- `acks=all` with RF=1 is a no-op today but the right default to carry forward.
- `Topic.ORDER_DELIVERED` is pre-added for Day 33 — unused, fine.

---

## Ready for Day 32

Yes — the producer side is solid. Fix #1 before the consumer work, or you'll
debug a consumer against orders that live in the other database. `order.dispatched`
is the only real topic on the broker (my probe topic was deleted).

> Infra left running (kafka, db, redis) — all were stopped before this check.
