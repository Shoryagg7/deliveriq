# Day 32 — Independent Verification Report

**Verified:** 2026-07-26 · re-run end-to-end on a quiet, exclusive environment.
Supersedes the earlier draft, which was taken while a parallel terminal session was
mutating the broker.

**Verdict: the consumer is correct and the at-least-once claim holds — now proven
properly.** Your honest-scope list is accurate as far as it goes, but it misses the
one gap that actually bites, and the commit labelled `day 32` contains no Day 32 code.

---

## ✅ Confirmed correct (each with a working control)

| Claim | Evidence |
|---|---|
| End-to-end API → Kafka → consumer | `POST /orders/dispatch` → `{"dispatched":{"order_id":4,"rider_id":4}}` → `[notify] order 4 → rider 4 (partition 1, offset 0)` |
| **At-least-once redelivery** | crash injected *between* PROCESS and COMMIT → restart **re-delivered** order 99/222 → next restart **silent** |
| Read ≠ committed | event sat in the log with no committed offset; after commit `CURRENT-OFFSET 1 / LOG-END-OFFSET 1 / LAG 0` |
| `commit(message=msg)` commits `offset+1` | describe shows `1` after consuming offset `0` |
| Manual commit config | [notification_consumer.py:30](app/workers/notification_consumer.py#L30), [:68](app/workers/notification_consumer.py#L68) |
| Ctrl-C path shuts down cleanly | SIGINT → `Consumer stopping (Ctrl-C).` + `Consumer closed cleanly.` |
| Cross-partition order not preserved | 7001/7002/7003 → 7002 (p0) consumed **before** 7001 (p2) — correct Kafka semantics, worth saying out loud |
| `kafka-init` + broker healthcheck | both `exited 0`; topic `PartitionCount: 3` |
| Redis Pub/Sub worker kept as "before" | `app/workers/notification_worker.py` present |

**The at-least-once proof is now real.** My first attempt patched
`Consumer.commit`, which silently failed (`cimpl.Consumer` is an immutable
extension type) — so the "redelivery" I saw was actually a first delivery. Redone
with a delegating proxy that kills the process the instant the handler finishes:

```
RUN A   [notify] order 99 → rider 7 (partition 0, offset 0)
        >>> CRASH: died after PROCESS, before COMMIT landed
RUN B   [notify] order 99 → rider 7 (partition 0, offset 0)   ← RE-DELIVERED
RUN C   (silent)                                              ← offset now committed
```

Same message twice, then never again. That is at-least-once, demonstrated rather
than assumed.

**The compose change is a real upgrade, not just plumbing.** Day 31 shipped
`kafka: service_started` with no healthcheck, flagged as a known compromise. Day 32
replaced it with a healthcheck plus `kafka-init: service_completed_successfully`,
making the topic *declared infrastructure* instead of an auto-create side effect —
closing the phantom-topic risk Day 31 wrote about.

---

## 🔴 1. Poison pill — one bad message blocks a partition permanently

**This is the gap the scope check missed, and it's the one that matters.**

The `try` catches only `KeyboardInterrupt`. Any exception from the PROCESS step —
malformed JSON, a missing `order_id`, a future DB call failing — propagates out of
the loop and kills the process **before** `consumer.commit()`. The offset never
advances, so restart re-reads the same message and dies again. Verified with the
real `main()` loop, three consecutive runs:

```
RUN 1  [notify] order 1 → rider 1 (partition 2, offset 0)   ← good, committed
       json.decoder.JSONDecodeError: Expecting value        ← poison, crash
RUN 2  json.decoder.JSONDecodeError: Expecting value        ← same message
RUN 3  json.decoder.JSONDecodeError: Expecting value        ← forever
```

The blast radius is wider than the bad message:

| Partition | Offset | Message | Fate |
|---|---|---|---|
| 2 | 0 | valid (order 1) | processed, committed |
| 1 | 0 | **POISON** | crashes the worker on every restart |
| 1 | 1 | **valid (order 3)** | **never processed — permanently unreachable** |

A perfectly good notification sat behind the poison and was never delivered. With
3 partitions keyed by `order_id`, one malformed event kills roughly a third of all
notifications.

**And your lag monitoring will not catch it.** `--describe` on the stuck group:

```
GROUP               TOPIC         PARTITION  CURRENT-OFFSET  LOG-END-OFFSET  LAG
poison-probe-group  poison.probe  2          1               1               0
```

Partition 1 — the blocked one — **has no row at all**, because a partition with no
committed offset isn't displayed. The dashboard reads "LAG 0, healthy" while a
partition is permanently wedged. (Same effect seen in normal operation: a dispatched
event sat unconsumed on p1 and `--describe` showed only p0 and p2 at LAG 0.)

**This is not a bug in your design — it's the missing half of it.** At-least-once
plus commit-after *necessarily* means an unprocessable message can never be skipped.
Choosing that trade-off is right; having no answer for it is the gap. Fix: wrap
PROCESS in `try/except`, then either log-and-commit (skip) or produce to a
dead-letter topic and commit — the DLQ version being worth building, since it makes
the failure inspectable rather than discarded.

Home: Day 34 idempotency, where "what happens on redelivery" and "what happens when
processing can never succeed" are two halves of one conversation.

## 🟠 2. SIGTERM is unhandled — and it costs a measured 45 seconds

Only `KeyboardInterrupt` (SIGINT) is caught. `docker compose stop`, `docker stop`,
and Kubernetes all send **SIGTERM**, which Python does not convert to
`KeyboardInterrupt`. Clean foreground comparison:

```
SIGINT  (Ctrl-C)       → "Consumer stopping (Ctrl-C)."  +  "Consumer closed cleanly."
SIGTERM (docker stop)  → (nothing — finally never runs, consumer.close() never called)
```

Because the member never leaves the group, its partition assignment is held until
`session.timeout.ms` expires. **Measured, from the consumer's own log timestamps:**

```
joined   : 01:01:18.2
delivered: 01:02:02.9
GAP = 44.7s   (subscribe → redelivery, after a hard kill)
```

44.7s against librdkafka's 45s default — the replacement instance sat idle doing
nothing for three quarters of a minute. Once containerised, that is every restart:
the worker looks hung on each deploy, and you'd debug it as a Kafka problem rather
than a signal-handling one.

Fix is a `signal.signal(SIGTERM, …)` handler flipping a `running` flag so the loop
exits through `finally`. **Do it as part of open thread #1, not after** —
containerising first means shipping the stall and then discovering it.

## 🟡 3. Topic literal — the exact trap Day 31 added the enum to prevent

[notification_consumer.py:21](app/workers/notification_consumer.py#L21) hardcodes
`TOPIC = "order.dispatched"`. Day 31 added `Topic.ORDER_DISPATCHED` to
`core/enums.py` for precisely this reason, verbatim from PLAN.md:

> A typo'd literal auto-creates a silent phantom topic; the consumer then waits
> forever on the wrong log.

The consumer is the half of the system that warning was written *about*, and it's
the half using a literal. The producer does it right
([dispatch.py:95](app/services/dispatch.py#L95)). One-line fix:
`TOPIC = Topic.ORDER_DISPATCHED.value`.

## 🟡 4. The `_PARTITION_EOF` branch is dead code as configured

`enable.partition.eof` defaults to **false** in librdkafka, so that branch never
executes. Measured with a control:

```
DEFAULT (consumer's cfg)     msgs=3  EOF_events=0
enable.partition.eof=True    msgs=3  EOF_events=3
```

Harmless, but PLAN.md presents it as a live guard ("a non-None return can be an
event (partition EOF), not data"). The *outer* `msg.error()` check is genuinely
necessary and live; only the EOF sub-branch is unreachable. Better interview
framing: "I guard it even though it's off by default, because enabling it is a
one-line config change" — rather than implying you watched it fire.

## 🟡 5. The commit labelled `day 32` contains no Day 32 code

```
7be69d7 "day 32"  →  2 screenshots + deletion of 3 python_and_oops practice files
                     (5 files changed, 525 deletions)
```

The actual deliverable, `app/workers/notification_consumer.py`, is **still
untracked**. This matters more here than in most projects: Day 31 deliberately used
git history as a narrative device ("Redis publish kept in git history — felt the
flaw, then upgraded"). A history where `day 32` contains none of Day 32 undermines
that device exactly when you'd want to walk someone through it.

---

## Notes on method (what changed since the first draft)

Three of my own measurements were wrong the first time and were redone:

1. **The at-least-once proof** — `Consumer.commit` patch failed silently; the
   "redelivery" was a first delivery. Redone with a proxy. Finding unchanged, but it
   is now actually proven.
2. **The SIGINT contrast** — a backgrounded process inherits `SIGINT` ignored, so
   "Ctrl-C doesn't work either" was an artifact. Redone in the foreground; the
   Ctrl-C path is clean. Only SIGTERM is broken.
3. **The recovery-delay number** — a first attempt measured the pipe timeout (91s),
   not the event. Redone from the log's own timestamps: 44.7s.

The environment was also stable this time (no concurrent `down -v`), so the broker
state under each test is known rather than assumed. Every finding below reproduced
on the quiet environment; none rests on the earlier session.

**Left behind:** infra running (db, redis, kafka, api on :8000). Probe topics and
groups deleted; `order.dispatched` and `notifications` are the only ones left, at
LAG 0 across all three partitions.

---

## Recommended order (answering "what to do here")

Your two threads are correctly identified and correctly deferred. Sequence:

1. **Commit the consumer** (§5) — 30 seconds, and the history currently lies.
2. **Fix §3** (enum) — one line, and it's the trap you already documented.
3. **Add a third open thread: poison-pill / DLQ** (§1) — higher impact than either
   thread you listed. Home: Day 34 idempotency.
4. **Fold SIGTERM (§2) into thread #1** as an explicit sub-task.
5. Then write all of it into PLAN.md's upcoming section.

The producer-test gap (Day 31 report §2) is still open and correctly tracked — it
has now slipped one day, which is fine, but it has slipped once. Worth a concrete
home rather than "Day 33 or Day 34."

**Ready for Day 33?** Yes — nothing here blocks multiple consumer groups. §1 is the
one that would embarrass a live demo: a single malformed event crash-loops the
worker while the lag dashboard still reads healthy.
