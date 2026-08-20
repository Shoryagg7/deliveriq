# DeliverIQ — Daily Commands (v4: Kafka, auth-hardened API, verify.sh)

> Two questions before any command: **which MODE am I in** (dev vs proof), and
> **which curl mode do I need** (A happy-path vs B debugging).

---

## 0. The two run modes

| | DEV MODE (daily) | PROOF MODE (replays, demos) |
|---|---|---|
| What runs in Docker | db + redis (**+ kafka from Day 31**) | everything (migrate, api ×N, db, redis, kafka, kafka-ui) |
| Your code runs | `uvicorn --reload` on host, port 8000 fixed | baked into image at `--build` |
| Code change costs | ~1s auto-reload | full `up --build` |
| Logs | uvicorn terminal | `docker compose logs api` |
| Kafka bootstrap | `localhost:9092` (PLAINTEXT_HOST listener) | `kafka:19092` (internal listener) |
| Use for | Days 30+ building, pytest, curling | `race_test.py`, load tests, resume demos |

Never both at once — they fight over port 8000. Ctrl-C uvicorn before a proof run.

> **The Kafka bootstrap row is the Day-31 config story:** host code dials the
> published listener; containers dial the internal one. `settings.kafka_bootstrap`
> switches via env — never hardcoded. Same address in the wrong place = client
> connects, then hangs.

---

## 1. DEV MODE

**Morning start:**
```bash
source venv/bin/activate
docker compose up -d db redis kafka      # kafka-ui optional
uvicorn app.main:app --reload            # terminal 1 — leave running, this is your log stream
```
> **Won't start? Check `.env` first.** `JWT_SECRET` has no default — the app
> refuses to import without one and says so with the fix attached. Generate:
> `sed -i "s|^JWT_SECRET=.*|JWT_SECRET=$(python3 -c 'import secrets; print(secrets.token_urlsafe(48))')|" .env`
> Compose interpolates it when the **file** is parsed, so even
> `docker compose up db` fails without it. That is the guard working.

**Daily loop (terminal 2):**
```bash
curl -siS http://localhost:8000/...      # Mode B on first request of the session
python -m pytest                         # after every meaningful change
./scripts/verify.sh                      # before any commit — adds lint + live auth checks
```

**Installing a package:**
```bash
pip install <pkg> && pip freeze > requirements.txt
```
Plain `pip` is correct — venv active, so no `--break-system-packages` (that flag
is for system Python only). Freeze immediately or the image build (proof mode)
won't have it.

### Alembic — migrations (dev mode authors them; proof mode's `migrate` job runs them)
```bash
alembic revision --autogenerate -m "add penalty_count to riders"   # generate
alembic upgrade head                     # apply to dev DB
alembic current                          # where am I
alembic history                          # all revisions
alembic downgrade -1                     # step back one (dev only, destructive)
```
- **Read the generated file before upgrading.** Autogenerate diffs models vs DB —
  it misses column *renames* (sees drop+add → data loss) and server defaults.
- `alembic/env.py` reads `DATABASE_URL` from env (permanent fix, all
  environments) — that's why the same migration works on host, in the container,
  and in CI.
- Migration is **single-writer**: in proof mode only the one-shot `migrate`
  service runs it (Day-29 race: 3 replicas all migrating → duplicate
  `alembic_version` → `api-2 Exited(1)`).

### Git dailies
```bash
git status
git diff                                 # unstaged changes
git log --oneline -10
git restore <file>                       # discard uncommitted changes to a file
```

**End of day:**
```bash
# Ctrl-C uvicorn, then:
docker compose stop                      # containers pause, data stays; morning = up -d ...
git add -A && git commit -m "day NN: <what>"
```

**After a `down -v` (fresh volumes) — extra steps before uvicorn:**
```bash
docker compose exec db psql -U deliveriq_user -d deliveriq_db -c "CREATE DATABASE deliveriq_test_db;"
alembic upgrade head                     # host runs migrations; infra-only up has no migrate job
```
> `down -v` **now also wipes `kafkadata`** — every message AND every consumer
> group offset. The topic auto-recreates on first use (3 partitions via
> `KAFKA_NUM_PARTITIONS`), but groups start with no committed offsets, so
> `auto.offset.reset` applies again. Don't debug "missing events" after a `-v`.

---

## 2. PROOF MODE

**Full replay (the Day-29 proof):**
```bash
# Ctrl-C uvicorn first
docker compose down
API_PORTS="8000-8002:8000" docker compose up --build -d --scale api=3
docker compose ps -a                 # migrate Exited(0) once; api ×3 Up
python scripts/race_test.py          # expects exactly ports 8000-8002 → scale=3 only
```
> Since Day 30 a bare `up` also starts kafka + kafka-ui — harmless; api doesn't
> depend on them (deliberately, until Day 31).

**Single-instance full-Docker (rare — e.g. testing the image itself):**
```bash
docker compose up --build -d         # API_PORTS unset → fixed 8000:8000
```

**Back to dev mode:**
```bash
docker compose down && docker compose up -d db redis   # +kafka from Day 31
```

Port rule: `${API_PORTS:-8000:8000}` in compose.yml. Unset = deterministic 8000.
Scale runs set it inline. The yml file is never edited to switch modes.

### Load test — Locust
```bash
pip install locust                       # once
API_PORTS=8000-8002:8000 docker compose up -d --scale api=3   # contention needs replicas
docker compose exec api python -m scripts.seed_users
RATE_LIMIT_ENABLED=false locust -f locustfile.py --host http://localhost:8000
# browser → http://localhost:8089 → users 50, ramp 10, Start
```
**There is no baseline number any more, deliberately.** The old
"~123 RPS · p99 220 ms" came from a profile that only hit *unauthenticated*
`POST /orders` — it measured a plain INSERT: no auth, no matching, no row locks,
no Kafka. The figure was real; the claim attached to it wasn't, so it was retired
rather than restated.

`locustfile.py` now logs in as ops and mixes two tasks:
- `/orders [create]` — supply side, keeps the pending queue non-empty
- `/orders/dispatch [claim]` — **the measurement**: matching under row-lock
  contention across replicas

**Report the two separately.** A blended RPS across both is meaningless — one is
an INSERT, the other is the whole system. `409` on dispatch means no rider was
free, which is a real outcome under load, not an error; the file marks it as a
success so the run doesn't report a fake error rate.

**Run it twice, and name which run a number came from:**
- Limiter ON → mostly 429s. That's the limiter *working*, not capacity.
- Limiter OFF → the honest number. Say the endpoint *and* the replica count.

### Standalone Docker (Day 27 — dormant, Compose supersedes; kept for the story)
```bash
docker build -t deliveriq .
docker run --rm --name deliveriq -p 8000:8000 \
  --add-host=host.docker.internal:host-gateway \
  -e DATABASE_URL="postgresql://deliveriq_user:password@host.docker.internal:5432/deliveriq_db" \
  -e REDIS_URL="redis://host.docker.internal:6379/0" \
  deliveriq:latest
docker ps                                # list running
docker stop deliveriq                    # stop by NAME (the whole point of --name)
docker images                            # deliveriq:latest → 606MB
docker system prune                      # reclaim dangling images/layers — read the prompt
```

---

## 3. curl — two modes, one rule

**First request after any startup = Mode B. Switch to Mode A after one raw `200 OK`.**

| Mode | Form | When |
|---|---|---|
| B — debug | `curl -siS URL` | first request, anything unexpected |
| A — happy | `curl -s URL \| python -m json.tool` | endpoint already proven this session |
| status only | `curl -s -o /dev/null -w "%{http_code}\n" URL` | scripting |

Flags: `-s` silent (hides progress AND errors) · `-S` re-show errors · `-i` status line + headers · `-X` method · `-H` header · `-d` body.
Chain with plain `;` — never `\;`. If zsh shows `dquote>`: Ctrl-C, you left a quote open.

Mode B bonus: `curl -siS URL | grep -i request` shows the request-id correlation
header (Day 22) — paste that id into the logs to trace one request end-to-end.

**Error ladder when Mode A prints `Expecting value: line 1 column 0`:**
`curl -siS` → `docker compose ps -a` (proof mode) or read uvicorn terminal (dev mode) → logs.

### Get a token first — nothing below works without one

**Every endpoint except `/auth/*` and the probes now needs a bearer token.**
If a curl that used to work returns `401`, that is the fix working, not a
regression.

```bash
# ops token — dispatch, rider onboarding, admin, sees everything
OPS=$(curl -s -X POST http://localhost:8000/auth/login -H "Content-Type: application/json" \
  -d '{"email":"ops@deliveriq.io","password":"opspassword123"}' \
  | python -c 'import json,sys; print(json.load(sys.stdin)["access_token"])')

# customer token — places orders, sees only their own
CUST=$(curl -s -X POST http://localhost:8000/auth/login -H "Content-Type: application/json" \
  -d '{"email":"customer@deliveriq.io","password":"custpassword123"}' \
  | python -c 'import json,sys; print(json.load(sys.stdin)["access_token"])')

echo ${OPS:0:20}...        # sanity: non-empty means login worked
```
> No users yet? `python -m scripts.seed_users` (dev) or
> `docker compose exec api python -m scripts.seed_users` (proof).
> Tokens expire in 60 min — re-run the export, don't debug a phantom 401.

### Endpoint cookbook (real schemas — cross-check /docs after schema changes)

```bash
# create rider — OPS ONLY (401 without a token, 403 with a customer's)
curl -s -X POST http://localhost:8000/riders -H "Authorization: Bearer $OPS" \
  -H "Content-Type: application/json" \
  -d '{"name":"Suresh","current_lat":28.6139,"current_lon":77.2090}' | python -m json.tool

# create order — NO customer_id in the body; it comes from the token
curl -s -X POST http://localhost:8000/orders -H "Authorization: Bearer $CUST" \
  -H "Content-Type: application/json" \
  -d '{"restaurant_id":1,"value":250,
       "pickup_lat":28.6140,"pickup_lon":77.2090,
       "drop_lat":28.6200,"drop_lon":77.2150}' | python -m json.tool

# dispatch next order — OPS ONLY
curl -s -X POST http://localhost:8000/orders/dispatch -H "Authorization: Bearer $OPS" | python -m json.tool

# advance order status (ASSIGNED → PICKED_UP → DELIVERED; CANCELLED where legal)
curl -s -X PATCH http://localhost:8000/orders/1/status -H "Authorization: Bearer $OPS" \
  -H "Content-Type: application/json" -d '{"status":"PICKED_UP"}' | python -m json.tool

# move a rider — ops, or that rider. Writes through to the geohash index.
curl -s -X PATCH http://localhost:8000/riders/1/location -H "Authorization: Bearer $OPS" \
  -H "Content-Type: application/json" -d '{"lat":28.6150,"lon":77.2100}' | python -m json.tool

# reads — scoped by role: ops sees all, customer sees only their own
curl -s http://localhost:8000/orders -H "Authorization: Bearer $OPS"  | python -m json.tool
curl -s http://localhost:8000/orders -H "Authorization: Bearer $CUST" | python -m json.tool
curl -s http://localhost:8000/admin/stats -H "Authorization: Bearer $OPS" | python -m json.tool

# interactive alternative to all of the above: http://localhost:8000/docs
#   click Authorize, paste the raw token (no "Bearer " prefix)
```

### Security spot-checks — what each one proves

```bash
# every one of these must print 401 — the four endpoints that used to be open
for ep in /orders /riders; do
  curl -s -o /dev/null -w "GET  $ep -> %{http_code}\n" http://localhost:8000$ep; done
curl -s -o /dev/null -w "PATCH /riders/1/location -> %{http_code}\n" \
  -X PATCH http://localhost:8000/riders/1/location \
  -H "Content-Type: application/json" -d '{"lat":1,"lon":1}'

# 403, not 401 — authenticated but not permitted (authn vs authz)
curl -s -o /dev/null -w "customer -> dispatch -> %{http_code}\n" \
  -X POST http://localhost:8000/orders/dispatch -H "Authorization: Bearer $CUST"

# a token signed with the OLD shipped secret must be rejected
FORGED=$(python -c "
from jose import jwt
from datetime import datetime, timedelta, UTC
print(jwt.encode({'sub':'ops@deliveriq.io','exp':datetime.now(UTC)+timedelta(hours=1)},
                 'dev-only-change-me', algorithm='HS256'))")
curl -s -o /dev/null -w "forged ops token -> %{http_code}\n" \
  http://localhost:8000/admin/stats -H "Authorization: Bearer $FORGED"

# idempotency: same key twice = one order, second carries the replay header
curl -siS -X POST http://localhost:8000/orders -H "Authorization: Bearer $CUST" \
  -H "Idempotency-Key: demo-1" -H "Content-Type: application/json" \
  -d '{"restaurant_id":1,"value":250,"pickup_lat":28.61,"pickup_lon":77.20,"drop_lat":28.62,"drop_lon":77.21}' \
  | grep -iE "HTTP/|Idempotent-Replay"      # run twice: 2nd shows Idempotent-Replay: true

# same key, DIFFERENT body -> 422, not a wrong replay
curl -s -o /dev/null -w "key reuse w/ new body -> %{http_code}\n" \
  -X POST http://localhost:8000/orders -H "Authorization: Bearer $CUST" \
  -H "Idempotency-Key: demo-1" -H "Content-Type: application/json" \
  -d '{"restaurant_id":9,"value":999,"pickup_lat":28.61,"pickup_lon":77.20,"drop_lat":28.62,"drop_lon":77.21}'

# rate limiter — burst until the bucket drains (capacity 100, refills 100/min)
for i in $(seq 1 110); do
  curl -s -o /dev/null -w "%{http_code}\n" http://localhost:8000/orders \
    -H "Authorization: Bearer $CUST"; done | sort | uniq -c
#   observed:  101 200 / 9 429   <- 100 tokens + refill during the run

# THE OLD BYPASS, now closed: rotating a caller-supplied header used to mint a
# fresh bucket every request. Keyed on the verified token now, so it does not.
for i in $(seq 1 20); do
  curl -s -o /dev/null -w "%{http_code}\n" http://localhost:8000/orders \
    -H "Authorization: Bearer $CUST" -H "X-API-Key: rotate-$i"; done | sort | uniq -c
#   observed:  20 429            <- still throttled. Before the fix: 20 x 200.

# request-id correlation: supply one and it comes back; garbage is replaced
curl -siS http://localhost:8000/health -H "X-Request-ID: my-trace-12345" | grep -i x-request-id
```
> The whole block above is automated: **`./scripts/verify.sh`** runs these plus
> lint and the test suite, and prints a pass/fail line per check.
> `POST /riders/match` was **removed** Day 29 ("dead code with a live side
> effect"). It returns **405**, not 404 — the path still matches
> `GET /riders/{rider_id}` with `rider_id="match"`. Don't chase that ghost.

---

## 4. Inspection

```bash
docker compose ps                    # what's Up (add -a to see exited migrate)
docker compose port api 8000         # actual host port (proof mode)
docker compose logs api --tail 30    # proof mode only; dev mode = uvicorn terminal
docker compose logs -f api           # live tail
docker compose logs migrate          # did the one-shot migration succeed?
docker compose exec api sh           # shell inside a container (ls, env, cat)
docker stats                         # live CPU/RAM per container (during load tests)
```

---

## 5. Postgres & Redis one-liners

SQL is the language; psql (terminal) and DBeaver (GUI, `localhost:5432`) are just two clients speaking it.
DBeaver caveats: F5 to refresh (it shows snapshots) · sees committed rows only · app data = `deliveriq_db`, pytest wipes `deliveriq_test_db` by design.

```bash
# quick query
docker compose exec db psql -U deliveriq_user -d deliveriq_db -c "SELECT status, COUNT(*) FROM riders GROUP BY status;"

# Day-29 verdict — zero rows = no double-assignment
docker compose exec db psql -U deliveriq_user -d deliveriq_db \
  -c "SELECT rider_id, COUNT(*) FROM orders WHERE rider_id IS NOT NULL GROUP BY rider_id HAVING COUNT(*) > 1;"

# which migration is the DB actually on (Day-29 race debugging)
docker compose exec db psql -U deliveriq_user -d deliveriq_db -c "SELECT version_num FROM alembic_version;"

# interactive session — the only psql to memorize:
#   \l databases · \dt tables · \d orders schema · \x toggle expanded rows (wide tables) · \q quit
docker compose exec db psql -U deliveriq_user -d deliveriq_db
```

```bash
docker compose exec redis redis-cli KEYS '*'                      # dev-scale only; O(N) blocking, never in prod
docker compose exec redis redis-cli SMEMBERS geohash:CELL
docker compose exec redis redis-cli GET "rider:1:orders:$(date +%F)"
docker compose exec redis redis-cli -n 15 KEYS '*'                # TEST Redis (logical DB 15) — pytest leftovers
docker compose exec redis redis-cli FLUSHDB                       # wipes Redis DB 0 only → Postgres↔Redis divergence; deliberate use only
```

DNS proof (containers resolve service names via Docker's embedded DNS at 127.0.0.11):
```bash
docker compose exec db getent hosts redis
```

### Redis command reference

Redis has 4 value shapes in this project — the command you need follows from the shape:

| shape | commands | used for |
|---|---|---|
| string | `GET key` · `SET key val` · `INCR key` | `orders_today` counter |
| hash (dict-in-a-value) | `HGET key field` · `HSET key f1 v1 f2 v2` · `HMGET key f1 f2` | `rider:{id}:loc` (lat+lon together), rate-limit bucket (tokens+last_refill) |
| set (unordered, no dupes) | `SADD key member` · `SREM key member` · `SMEMBERS key` | geohash cell membership |
| — (meta / any type) | `TTL key` · `EXPIRE key seconds` · `KEYS pattern` · `FLUSHDB` | inspection, GC, test resets |

All run inside the container:
```bash
docker compose exec redis redis-cli <COMMAND> <args...>

# examples
docker compose exec redis redis-cli HMGET rate_limit:127.0.0.1 tokens last_refill
docker compose exec redis redis-cli HSET rider:1:loc lat 28.6139 lon 77.2090
docker compose exec redis redis-cli SMEMBERS geohash:ttnfuc
docker compose exec redis redis-cli SADD geohash:ttnfuc 1
docker compose exec redis redis-cli TTL rate_limit:127.0.0.1     # -2 = gone, -1 = no expiry, else seconds left
docker compose exec redis redis-cli EXPIRE rate_limit:127.0.0.1 120
docker compose exec redis redis-cli GET "rider:1:orders:$(date +%F)"
docker compose exec redis redis-cli INCR "rider:1:orders:$(date +%F)"
```

`KEYS '*'` is dev-only — O(N), blocks the single-threaded Redis event loop.
Production/large keyspaces use `SCAN` (cursor-based, non-blocking) instead — not needed at this project's scale, but know the name.

### Pub/Sub (Day 20 relic — replaced by Kafka on Day 31; keep for the story)
```bash
docker compose exec redis redis-cli SUBSCRIBE order.dispatched    # watch the channel live
docker compose exec redis redis-cli PUBLISH order.dispatched '{"order_id":1,"rider_id":11}'  # → replies N subscribers
python -m app.workers.notification_worker                          # the Day-20 worker (2nd terminal)
```
`PUBLISH` returning `0` = nobody alive = the message never existed. That's the
fire-and-forget flaw, in one integer — and the whole reason §8 exists.

---

## 6. Tests

### The one command

```bash
./scripts/verify.sh          # config guard + infra + migrations + lint + 71 tests + live auth smoke
```
16 checks, ~50 s, pass/fail line each. Safe to run while the stack is up — the
suite uses `deliveriq_test_db`, so dev data is untouched (verified). Run this
before any commit and before any demo.

### Everyday pytest

```bash
python -m pytest                    # always python -m (PATH-shadowing lesson); 71 tests
python -m pytest -x                 # stop at first failure — use while fixing
python -m pytest --lf               # re-run only last failures — the tight loop
python -m pytest -q --no-header     # quiet, for a fast green/red
python -m pytest --cov=app --cov-report=term-missing    # which lines are naked
```
Needs infra up: `docker compose up -d db redis kafka`.

### Which command runs which proof

Pick the file by the property you just touched.

| Command | Tests | What it proves |
|---|---|---|
| `pytest tests/test_orders.py` | 16 | Order lifecycle end to end: creation, validation bounds, dispatch assigns the right rider, a busy rider isn't re-dispatched, delivery frees them, illegal transitions rejected, idempotent retries replay. |
| `pytest tests/test_auth.py` | 13 | Registration, login, the **401-vs-403** split, no account-enumeration oracle, and the permitted-actor matrix — a rider may advance only their own order and may never cancel. |
| `pytest tests/test_scoping_and_idempotency.py` | 10 | **Read scoping** (customer sees only their own, rider only assigned, ops all) and **cross-tenant idempotency isolation** — two users sending the same key must not collide. |
| `pytest tests/test_rider_location_auth.py` | 8 | The **dispatch-integrity guard**. Ends with a live hijack attempt: an outsider tries to teleport a far rider onto the pickup point, and the genuinely-nearest rider must still win. |
| `pytest tests/test_middleware_hardening.py` | 13 | Rate-limit keying can't be rotated by the caller, forged tokens fall back to peer IP, request-ids are adopted only when safe, and idempotent replays appear in HTTP metrics. |
| `pytest tests/test_config.py` | 11 | The **`JWT_SECRET` startup guard**: missing, placeholder, too short, and bytes-vs-characters length. |

Narrow further with `-k`:

```bash
python -m pytest tests/test_orders.py -k dispatch -v      # just the dispatch path
python -m pytest -k "idempot" -v                          # idempotency across all files
python -m pytest -k "hijack or forged" -v                 # the two attack-shaped tests
```

### The concurrency proof (not in pytest, not in CI)

```bash
API_PORTS=8000-8002:8000 docker compose up -d --scale api=3   # PROOF MODE only
docker compose exec api python -m scripts.seed_users
python -m scripts.race_test
```
Fires **15 simultaneous dispatches across 3 replicas** against 10 orders and 10
riders, then asserts every assigned `order_id` **and** every `rider_id` is
unique. This is the headline correctness claim — that `SELECT … FOR UPDATE SKIP
LOCKED` prevents double-assignment — and it is the one property **not** protected
by CI, so run it by hand after touching `services/dispatch.py`.

Expected tail: `✅ zero double-assignment across replicas`. Anything else is a
real regression, not flakiness.

### Isolation seams (Day 21)

Postgres via `dependency_overrides[get_db]` → `deliveriq_test_db`; Redis via
`REDIS_URL` db 15 set **before import** (module global, not a `Depends`); Kafka
via patching `publish_event` at the **call sites**, not the definition site.
Three seams, three mechanisms — that asymmetry is the lesson. `conftest.py`
asserts no real producer was ever constructed, so a missed call site fails the
run instead of silently publishing to a live broker.

---

## 7. Reset buttons (increasing severity)

```bash
docker compose restart api        # proof mode bounce (env change; code needs --build)
docker compose down               # remove containers+network, KEEP data
docker compose down -v            # + wipe volumes = Postgres AND Kafka gone → §1 "after down -v" steps
```
`-v` kills `pgdata` + `kafkadata`: DB rows, Kafka messages, **and consumer-group
offsets**. No confirmation prompt.

---

## 8. Kafka — daily commands

> Broker: `apache/kafka:4.1.2`, KRaft, single node. UI: http://localhost:8080
> Everything below runs from the repo root.

### 8.0 Shortcuts — paste into your shell first

```bash
kt() { docker compose exec kafka /opt/kafka/bin/kafka-topics.sh --bootstrap-server localhost:9092 "$@"; }
kg() { docker compose exec kafka /opt/kafka/bin/kafka-consumer-groups.sh --bootstrap-server localhost:9092 "$@"; }
kc() { docker compose exec kafka /opt/kafka/bin/kafka-console-consumer.sh --bootstrap-server localhost:9092 "$@"; }
kp() { docker compose exec -T kafka /opt/kafka/bin/kafka-console-producer.sh --bootstrap-server localhost:9092 "$@"; }
kx() { docker compose exec kafka /opt/kafka/bin/kafka-configs.sh --bootstrap-server localhost:9092 "$@"; }
ko() { docker compose exec kafka /opt/kafka/bin/kafka-get-offsets.sh --bootstrap-server localhost:9092 "$@"; }
```
- **`kp` uses `-T`** — no TTY, so heredocs feed stdin (with a TTY the producer
  waits for typing). The others keep the TTY.
- **`localhost:9092` is correct here** — these run *inside* the broker container
  (the `PLAINTEXT_HOST` listener). App code uses **`kafka:19092`** in Compose,
  `localhost:9092` from the host. Never confuse the three.
- Full unaliased forms live in `PLAN.md` Day 30; aliases live here only.

### 8.1 Lifecycle
```bash
docker compose config >/dev/null && echo "YAML OK"   # parse BEFORE up — bad YAML ≠ bad Kafka
docker compose up -d kafka kafka-ui
docker compose ps                                     # want: Up, NOT Restarting
docker compose logs -f kafka                          # want: Kafka Server started
```
`ps` is the real liveness check — a log tail scrolls past a crash loop and lies.
Compose is declarative: edit + `up` reconciles the delta; unchanged services
untouched. Messages survive recreation — they're in the `kafkadata` volume.

### 8.2 Inspect
```bash
kt --list                                    # all topics (incl. __consumer_offsets)
kt --describe --topic order.dispatched       # partitions, leader, ISR
ko --topic order.dispatched                  # log-end offset per partition (fast)
kx --describe --entity-type topics --entity-name order.dispatched   # retention etc.
```
**`--list` empty *and instant* = broker healthy** (full bootstrap→metadata→response
round trip). A dead broker hangs ~60s then `TimeoutException`. Empty-instant vs
hang-and-die is the tell.
`Isr` shrinking below `Replicas` = the URP alert (trivially impossible at RF=1).

### 8.3 Produce
```bash
kp --topic order.dispatched --property parse.key=true --property key.separator=: <<'EOF'
1:{"order_id":1,"rider_id":11}
2:{"order_id":2,"rider_id":12}
EOF
```
**Expect: no output** — sends and exits silently.

> ### ⚠️ The key must match the payload
> Kafka never reads your JSON — it hashes the **key bytes** only. Write
> `1:{"order_id":9}` and order 9's event lands in **order 1's partition**, while
> order 9's correctly-keyed later events land elsewhere: **one order's timeline
> split across two files, no ordering between them.** No error — key↔payload
> consistency is *your* invariant. Day-31 rule: derive the key from the payload
> (`key=str(order_id)`), never pass them separately.

No key at all → round-robin → per-key ordering gone entirely.

### 8.4 Consume
```bash
# groupless — throwaway reader, no bookmark; re-reads every time
kc --topic order.dispatched --from-beginning \
   --property print.partition=true --property print.key=true \
   --property print.offset=true --timeout-ms 5000

# with a group — commits offsets on exit
kc --topic order.dispatched --group notifications \
   --property print.partition=true --property print.key=true --timeout-ms 8000
```
- `--timeout-ms` **exits by throwing `TimeoutException`** — ugly, expected, not a
  failure. Verdict line: `Processed a total of N messages`.
- **Read order ≠ produce order.** Order holds *within* each partition, nowhere else.
- **`--from-beginning` is a fallback, not a rewind**: it's
  `auto.offset.reset=earliest`, applied **only when the group has no committed
  offset**. On a caught-up group → `Processed a total of 0 messages`. Works
  exactly once per group, ever.

### 8.5 Groups & lag
```bash
kg --list
kg --describe --group notifications
kg --describe --group notifications --members    # who's connected, which partitions
```
- **"has no active members" ≠ "not found"** — the group *exists* with zero
  processes. A group is rows in `__consumer_offsets`, not a process.
- One row per **(group, topic, partition)**. `CURRENT-OFFSET` = **next unread**.
- **`LAG = LOG-END − CURRENT`** — the only honest consumer health metric. Alive +
  polling + low CPU can still be falling behind forever. Flat 0 = healthy;
  climbing = losing. Per-partition: 0/0/40k is not "mostly fine."

### 8.6 Replay — an admin act, not a flag
```bash
kg --group notifications --topic order.dispatched --reset-offsets --to-earliest --dry-run
kg --group notifications --topic order.dispatched --reset-offsets --to-earliest --execute
```
**Always dry-run first** (prints proposed `NEW-OFFSET`, changes nothing). Then
consume normally — no `--from-beginning` needed; the bookmark already moved.
**`--execute` refuses if the group has active members** — stop → reset → restart
is the real production procedure.

Other targets:
```bash
--reset-offsets --to-offset 42        --execute
--reset-offsets --shift-by -10        --execute
--reset-offsets --to-datetime 2026-07-16T00:00:00.000 --execute
```

### 8.7 Break-it experiments
**A. Replay across consumer death (the Day-20 flaw, dead):**
consumer down → `kp` orders 7,8 → `kg --describe` shows **LAG 2** (a number
Pub/Sub cannot express) → `kc` with the group, **no `--from-beginning`** →
**exactly 2 messages.** Not 8 (genuine resume, not full replay), not 0 (events
produced while dead survived).

**B. Retention deletes — consumption doesn't:**
```bash
kx --alter --entity-type topics --entity-name order.dispatched \
   --add-config retention.ms=1000,segment.ms=1000
# wait ~5 min → kt --describe / UI: First Offset moves off 0
kx --alter --entity-type topics --entity-name order.dispatched \
   --delete-config retention.ms,segment.ms          # REVERT
```
You read the messages 4× and they stayed; you set a *policy* and they vanished.
Gotchas: Kafka deletes whole **segments** and the **active segment is never
eligible** (hence `segment.ms`); the cleaner runs every **5 min** — wait before
you debug.

**C. Hash skew is real:** keys `7` and `8` both landed in **P0** (observed 4/2/2,
not 2/2/2). `murmur2` owes you nothing; a skewed key melts one partition while
others idle.

### 8.8 Danger zone
```bash
kg --group notifications --topic order.dispatched --reset-offsets --to-latest --execute
   # skip the backlog: mark all read WITHOUT reading = deliberate data loss (incident button)
kg --delete --group notifications        # group's offsets gone → auto.offset.reset applies next start
kt --delete --topic order.dispatched     # topic + every message
docker compose down -v                   # everything incl. pgdata + kafkadata; no prompt
```

### 8.9 kafka-ui — http://localhost:8080
Reads the broker over **`kafka:19092`** — first client on the internal listener,
so **cluster green = advertised listeners verified**, a day before the API needs
the same path.
- Topics → `order.dispatched`: partition table, message counts, `First Offset 0`
  (reading never deletes).
- Messages: filter by partition — watch the skew directly.
- Consumers: the offsets/lag table, rendered.
- `URP 0` = Under-Replicated Partitions — *the* production Kafka alert alongside lag.
- `Clean Up Policy: DELETE` vs `COMPACT` (keep latest value per key forever) —
  `__consumer_offsets` is compacted, which is exactly why the bookmark outlives
  the events it points at.
