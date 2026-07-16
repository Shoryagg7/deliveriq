# DeliverIQ — Daily Commands (v2, hybrid workflow)

> Two questions before any command: **which MODE am I in** (dev vs proof), and
> **which curl mode do I need** (A happy-path vs B debugging).

---

## 0. The two run modes

| | DEV MODE (daily) | PROOF MODE (replays, demos) |
|---|---|---|
| What runs in Docker | db + redis only | everything (migrate, api ×N, db, redis) |
| Your code runs | `uvicorn --reload` on host, port 8000 fixed | baked into image at `--build` |
| Code change costs | ~1s auto-reload | full `up --build` |
| Logs | uvicorn terminal | `docker compose logs api` |
| Use for | Days 30+ building, pytest, curling | `race_test.py`, load tests, resume demos |

Never both at once — they fight over port 8000. Ctrl-C uvicorn before a proof run.

---

## 1. DEV MODE

**Morning start:**
```bash
docker compose up -d db redis        # infra only
uvicorn app.main:app --reload        # terminal 1 — leave running, this is your log stream
```

**Daily loop (terminal 2):**
```bash
curl -siS http://localhost:8000/...  # Mode B on first request of the session
python -m pytest                     # after every meaningful change
```

**End of day:**
```bash
# Ctrl-C uvicorn, then:
docker compose stop                  # containers pause, data stays; morning = up -d db redis
git add -A && git commit -m "day NN: <what>"
```

**After a `down -v` (fresh volume) — two extra steps before uvicorn:**
```bash
docker compose exec db psql -U deliveriq_user -d deliveriq_db -c "CREATE DATABASE deliveriq_test_db;"
alembic upgrade head                 # host runs migrations; infra-only up has no migrate job
```

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

**Single-instance full-Docker (rare — e.g. testing the image itself):**
```bash
docker compose up --build -d         # API_PORTS unset → fixed 8000:8000
```

**Back to dev mode:**
```bash
docker compose down && docker compose up -d db redis
```

Port rule: `${API_PORTS:-8000:8000}` in compose.yml. Unset = deterministic 8000.
Scale runs set it inline. The yml file is never edited to switch modes.

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

**Error ladder when Mode A prints `Expecting value: line 1 column 0`:**
`curl -siS` → `docker compose ps -a` (proof mode) or read uvicorn terminal (dev mode) → logs.

### Endpoint cookbook (real schemas — cross-check /docs after schema changes)

```bash
# create rider
curl -s -X POST http://localhost:8000/riders -H "Content-Type: application/json" \
  -d '{"name":"Suresh","current_lat":28.6139,"current_lon":77.2090}' | python -m json.tool

# create order
curl -s -X POST http://localhost:8000/orders -H "Content-Type: application/json" \
  -d '{"customer_id":1,"restaurant_id":1,"value":250,
       "pickup_lat":28.6140,"pickup_lon":77.2090,
       "drop_lat":28.6200,"drop_lon":77.2150}' | python -m json.tool

# dispatch next order
curl -s -X POST http://localhost:8000/orders/dispatch | python -m json.tool

# advance order status (ASSIGNED → PICKED_UP → DELIVERED; CANCELLED where legal)
curl -s -X PATCH http://localhost:8000/orders/1/status -H "Content-Type: application/json" \
  -d '{"status":"PICKED_UP"}' | python -m json.tool

# reads
curl -s http://localhost:8000/orders/1 | python -m json.tool
curl -s http://localhost:8000/admin/stats | python -m json.tool

# interactive alternative to all of the above: http://localhost:8000/docs
```

---

## 4. Inspection

```bash
docker compose ps                    # what's Up (add -a to see exited migrate)
docker compose port api 8000         # actual host port (proof mode)
docker compose logs api --tail 30    # proof mode only; dev mode = uvicorn terminal
docker compose logs -f api           # live tail
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

# interactive session — the only psql to memorize: \l databases, \dt tables, \d orders schema, \q quit
docker compose exec db psql -U deliveriq_user -d deliveriq_db
```

```bash
docker compose exec redis redis-cli KEYS '*'                      # dev-scale only; O(N) blocking, never in prod
docker compose exec redis redis-cli SMEMBERS geohash:CELL
docker compose exec redis redis-cli GET "rider:1:orders:$(date +%F)"
docker compose exec redis redis-cli FLUSHDB                       # wipes Redis only → Postgres↔Redis divergence; deliberate use only
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

---

## 6. Tests

```bash
python -m pytest                              # always python -m (PATH-shadowing lesson); 9 tests
python -m pytest tests/test_orders.py -k dispatch -v
python scripts/race_test.py                   # PROOF MODE at scale=3 only
```

---

## 7. Reset buttons (increasing severity)

```bash
docker compose restart api        # proof mode bounce (env change; code needs --build)
docker compose down               # remove containers+network, KEEP data
docker compose down -v            # + wipe volumes = wipe Postgres → run §1 "after down -v" steps
```
##8 Kafka important testing commands

docker compose exec kafka /opt/kafka/bin/kafka-topics.sh \
  --bootstrap-server localhost:9092 \
  --describe --topic order.dispatched

docker compose exec -T kafka /opt/kafka/bin/kafka-console-producer.sh \
  --bootstrap-server localhost:9092 \
  --topic order.dispatched \
  --property parse.key=true --property key.separator=: <<'EOF'
1:{"order_id":1,"rider_id":11}
2:{"order_id":2,"rider_id":12}
3:{"order_id":3,"rider_id":13}
4:{"order_id":4,"rider_id":14}
5:{"order_id":5,"rider_id":15}
6:{"order_id":6,"rider_id":16}
EOF


docker compose exec kafka /opt/kafka/bin/kafka-consumer-groups.sh \
  --bootstrap-server localhost:9092 \
  --describe --group notifications

docker compose exec kafka /opt/kafka/bin/kafka-console-consumer.sh \
  --bootstrap-server localhost:9092 \
  --topic order.dispatched \
  --group notifications \
  --property print.partition=true --property print.key=true \
  --timeout-ms 5000


docker compose exec kafka /opt/kafka/bin/kafka-consumer-groups.sh \
  --bootstrap-server localhost:9092 \
  --group notifications --topic order.dispatched \
  --reset-offsets --to-earliest --dry-run

docker compose exec kafka /opt/kafka/bin/kafka-consumer-groups.sh \
  --bootstrap-server localhost:9092 \
  --group notifications --topic order.dispatched \
  --reset-offsets --to-earliest --execute

docker compose exec kafka /opt/kafka/bin/kafka-consumer-groups.sh \
  --bootstrap-server localhost:9092 \
  --group notifications --topic order.dispatched \
  --reset-offsets --to-latest --execute

