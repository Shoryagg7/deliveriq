# Day 29 — Independent Verification & Follow-up Fixes

> **What this file is:** a sync report from a Claude Code session that
> independently verified the committed Day 29 work (`b0f8873 "The Distributed
> Claim"`), found two issues, and fixed them. Uploaded to the DeliverIQ project
> so both chats share the same state. The fixes below are **in the working tree,
> not yet committed.**

---

## 1. Verification of the committed Day 29 work — PASSED ✅

Method: full code review of `dispatch.py` / `geohash_service.py` /
`docker-compose.yml`, then live testing against `docker compose up --build -d
--scale api=3`.

| Check | Result |
|---|---|
| Unit/integration suite (`python -m pytest`) | 9/9 passed |
| `migrate` one-shot job | Exited(0) once; 3 api replicas serve-only |
| Race test: 15 **simultaneous** dispatches across 3 instances, 10 riders + 10 orders seeded | **Zero double-assignment** (no duplicate order_id or rider_id) |
| `SELECT rider_id ... HAVING COUNT(*) > 1` verdict query | 0 rows |
| Postgres↔Redis consistency after the burst | exact: BUSY riders SREM'd from geohash index, `orders_today`=1 for winners only |
| Failed dispatches (409) retryable? | yes — sequential retries drained all remaining orders cleanly |

Confirmed properties of the 2-phase claim loop:
- Status re-check inside the locked SELECT is correct under Read Committed
  (`SKIP LOCKED` covers the still-locked case; the `status='PENDING'` filter
  covers the already-committed case).
- Claim-all-before-mutate holds — the §45 unit-of-work trap stays fixed.
- **Deadlock-free by construction:** `SKIP LOCKED` never waits, so dispatch can
  never participate in a lock cycle. (Good interview line.)

---

## 2. Finding 1 — thundering herd: losing a rider lost the whole order

### Symptom (measured, not theoretical)
In the concurrent burst, only **5 of 15** calls succeeded while **5 riders sat
AVAILABLE** — 10 calls returned 409 `RIDER_UNAVAILABLE`. Correctness held;
throughput under contention did not.

### Root cause
On a failed rider claim the loop did `continue` — abandoning the **order** and
moving to the next one. And every concurrent caller picks the **same**
top-ranked rider, because all differentiating state lands post-commit: the
fairness scores `(orders_today, dist)` are identical during the race, the
winner's `SREM`/`INCR` haven't happened yet. So all losers chase the same rider
down the entire order heap and exhaust → 409 despite available riders.

### Fix — rider-level retry (claim loop inside the claim loop)
`select_rider()` gained an `exclude` parameter; dispatch retries the **same
order** with the next-best rider until a claim lands or the band is empty:

```python
# app/services/dispatch.py — CLAIM 2 replaced with:
tried: set[int] = set()
rider = None
while True:
    rider_id = select_rider(
        winner.pickup_lat, winner.pickup_lon, exclude=tried
    )
    if rider_id is None:
        break  # band exhausted — genuinely nobody for this order

    rider = (
        db.query(Rider)
        .filter(Rider.id == rider_id, Rider.status == "AVAILABLE")
        .with_for_update(skip_locked=True)
        .first()
    )
    if rider is not None:
        break  # rider row locked — exclusively ours until commit
    tried.add(rider_id)  # claim lost — next-best rider, same order

if rider is None:
    continue  # no claimable rider — next order (nothing mutated)
```

```python
# app/services/geohash_service.py — select_rider signature:
def select_rider(order_lat, order_lon, band_m: float = 500,
                 exclude: set[int] | None = None) -> int | None:
    candidates = find_nearby_riders(order_lat, order_lon)
    if exclude:
        candidates = [rid for rid in candidates if rid not in exclude]
    ...
```

Design notes:
- **Terminates:** every failed claim adds to `tried`; candidates (3×3 geohash
  cells) are finite.
- **Invariant preserved:** nothing is mutated inside the retry loop —
  claim-all-first, mutate-last survives.
- **Band re-centering (deliberate):** exclusion happens *before* `d_min` is
  computed, so the fairness band recalculates around the nearest *eligible*
  rider — the SLA bound stays relative to riders you can actually get.
- **Bonus self-heal:** a stale BUSY rider stuck in the geohash index (crash
  after commit, before SREM) previously poisoned every order's selection
  (always ranked first, claim always fails, order abandoned). Now they cost
  one failed claim and get excluded.

### Post-fix result (same test, rebuilt containers)
**10/15 succeeded — every order dispatched in a single concurrent burst**, all
10 riders used exactly once, zero doubles. The 5 failures are the 5 surplus
calls (15 calls, 10 orders), correctly 409.

**Soundbite:** "Under a concurrent burst all instances chase the same
top-ranked rider, because the state that would differentiate them only lands
post-commit. My first version abandoned the whole order on a lost rider claim —
measured 5/15 success with riders idle. The fix is a bounded rider-level retry:
exclude the contested rider and re-select for the same order. Same test after:
10/15, every order dispatched in one burst. Losing a race now costs one
candidate, not the whole request."

**Gotcha:** the retry loop must stay mutation-free — mutate only after BOTH
claims are locked, or the §45 unit-of-work trap comes back.

---

## 3. Finding 2 — `/riders/match` silently lost its side effect

### Root cause
Day 29 split `select_rider()` into a pure read + `record_rider_assignment()`
(post-commit INCR). Dispatch got both halves; **the `/riders/match` endpoint
only got the read** — so its fairness counter never bumped, repeated calls
returned the same rider forever, and Interview_prep §15's justification
("match is POST *because* it increments the winner's count") became false.

### Fix
```python
# app/routers/riders.py — match_rider:
rider_id = select_rider(req.lat, req.lon)
if rider_id is None:
    raise RiderUnavailable("No available rider nearby")
record_rider_assignment(rider_id)  # fairness counter — the side effect that makes this a POST
return {"assigned_rider_id": rider_id}
```

The endpoint now explicitly owns its side effect (an improvement over the old
design, where the mutation hid inside a function named "select"). §15 is true
again — no doc change needed.

### Post-fix result
3 fresh riders at one location, 3 consecutive `/riders/match` calls → riders
**23 → 21 → 22** (rotation via the fairness counter). Pre-fix this returned the
same rider 3 times.

**Gotcha (the general lesson):** when refactoring a function's side effects
out, grep for **every** caller — dispatch was updated, match was forgotten.
A pure-read `select_rider` changed match's semantics silently: no error, no
failing test, just quietly wrong fairness.

---

## 4. Files changed (uncommitted)

| File | Change |
|---|---|
| `app/services/dispatch.py` | CLAIM 2 → bounded rider-retry loop (`tried` exclude-set) |
| `app/services/geohash_service.py` | `select_rider(..., exclude=None)` — filters before band computation |
| `app/routers/riders.py` | `record_rider_assignment()` after successful match + import |
| `scripts/race_test.py` | **new** — repeatable concurrency proof (seed 10+10, 15 parallel dispatches, assert zero doubles) |
| `docs/Day29_Verification_Report.md` | **new** — this file |

Repeat the proof anytime with:
`docker compose up --build -d --scale api=3 && python scripts/race_test.py`

---

## 5. Known gaps deliberately NOT fixed (tracked for later)

1. **`PATCH /orders/{id}/status` race** — reads the order with no lock; a
   concurrent cancel during dispatch can overwrite ASSIGNED and leak a BUSY
   rider. Fix shape: `with_for_update()` on the order read + transition check
   against the locked row. Natural home: Day 35 (endpoint gets touched for
   authz anyway) or the Day 41–45 sweep.
2. **Lock accumulation while walking the heap** — orders claimed but skipped
   (no rider anywhere) stay locked until the request ends. Bounded and
   harmless; optional `db.rollback()` before that `continue` (safe — nothing
   mutated) would release them earlier.
3. **Tie randomization in `select_rider`** — optional optimization: jitter
   equal-score ties so concurrent bursts spread across riders instead of
   colliding on one. The retry loop makes this unnecessary for correctness;
   it would only shave failed-claim round-trips.
4. ~~Commit `b0f8873` also deleted `docs/All_Resources_in_One_Place.md`~~ —
   confirmed intentional by Shorya.

---

## 6. Follow-up decision: `POST /riders/match` REMOVED

After Fix 2 restored the endpoint's fairness side effect, review concluded the
endpoint itself no longer deserves to exist. It was the **Day 18 demo** of
banded matching, from before dispatch existed. Post-Day-29 it did nothing
except distort state: it charged the chosen rider an `orders_today` fairness
point for an order that never existed, without marking them BUSY or touching
the index. Dead code with a live side effect is a latent bug, not a feature.
Decision (Shorya): remove rather than keep as demo or convert to a read-only
preview.

**Removed from `app/routers/riders.py`:** the `match_rider` endpoint, its
`MatchRequest` model, and the now-dead imports (`select_rider`,
`record_rider_assignment`, `RiderUnavailable` — the latter still used by
dispatch). `select_rider`/`record_rider_assignment` now have exactly one
consumer: dispatch.

**Docs updated (Interview_prep.md):** §3's POST examples and verb soundbite
now cite `/orders/dispatch` only; §15's endpoint subsection replaced with the
removal story + soundbite ("dead code with a live side effect is worse than
dead code"); §16 Q11 reworded to ask why keeping it was worse than ordinary
dead code. **PLAN.md Day 18 left untouched** — it is the historical build log;
history doesn't get rewritten.

**Verified:** rebuilt containers; `POST /riders/match` now returns **405** —
not 404, a routing subtlety worth knowing: the literal path `/riders/match`
still *matches the pattern* `GET /riders/{rider_id}` (with `rider_id="match"`),
so the path "exists" but not for POST → 405 Method Not Allowed. Dispatch
unaffected; 9/9 tests pass.

**Grep-the-callers check** (the Finding-2 lesson applied): no references to
the endpoint existed in tests, locustfile, or other code — only the two docs.

---

## 7. Docs & diagrams sync (so both chats match)

**PLAN.md** — Day 29 section now ends with a "Day 29 follow-up" block:
finding C (thundering herd → rider-level retry, 5/15 → 10/15), finding D
(match regression → removal), `scripts/race_test.py`. Diagram links added
(see below). Day 18 history untouched.

**Interview_prep.md** — Part 15 gained **§48 "The Thundering Herd &
Rider-Level Retry"** (correct-vs-live distinction, the herd mechanism, the
bounded exclude-retry, band re-centering, CQS + grep-every-caller lesson);
self-test renumbered to **§49** with four new questions (9–12). Earlier
match-removal edits: §3 verb examples, §15 removal story, §16 Q11.

**New folder `docs/diagrams/`** — self-contained HTML diagrams (no CDN, open
directly in a browser, light/dark aware, validated palette):
- `day20_flow.html` — replaces the old inline mermaid in PLAN.md (kept as the
  labeled *historical* Day-20 snapshot: pre-locking, INCR-in-select_rider,
  pre-commit SREM — each marked with a "fixed later" note).
- `day29_workflow.html` — current architecture: compose infra strip
  (migrate one-shot, api ×3, ports 8000-8002), the 5-phase dispatch pipeline
  (scan → claim order → claim rider w/ retry → mutate → commit → Redis
  catch-up), a two-instance race timeline, verified stats, known gaps.

PLAN.md links: the Day-20 mermaid block is replaced by a link to
`diagrams/day20_flow.html`; a "Current end-to-end flow (as of Day 29)" link
to `diagrams/day29_workflow.html` sits at the end of the Day 29 section.
Both rendered and visually checked via headless Chrome.
