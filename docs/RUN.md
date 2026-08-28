# Running DeliverIQ

Four commands to run it, three to prove it works.

---

## Run it

```bash
API_PORTS=8000:8000 docker compose up -d               # pin the port — see the gotcha below
docker compose exec api python -m scripts.seed_users   # the 3 demo logins
docker compose exec api python -m scripts.seed_demo    # riders + a populated board
curl -s localhost:8000/ready | python -m json.tool     # postgres/redis/kafka all "ok"
```

~25 s with a warm image. Migrations run automatically as a one-shot job the API
waits on, so there is no manual `alembic` step.

Then open **http://localhost:8000** — the console is served by FastAPI itself
(one origin, which is why there's no CORS config anywhere).

**Logins** (created by `seed_users`):

| Role | Email | Password | Can |
|---|---|---|---|
| ops | `ops@deliveriq.io` | `opspassword123` | everything: dispatch, onboard riders, `/admin/stats` |
| rider | `rider@deliveriq.io` | `riderpassword123` | advance **their own** order; 403 on cancel |
| customer | `customer@deliveriq.io` | `custpassword123` | place orders; sees only their own |

Sign-in is one click per role from the console's **act as** chips.

**Both seeds are required.** Without `seed_users` every login is a 401 (the
database has no users). Without `seed_demo` the board is empty and "Dispatch
next" has nothing to do. `seed_demo` prints `rider@deliveriq.io holds N
order(s)` — if that says `0`, re-run it, or signing in as `rider` shows a blank
board mid-demo.

## Prove it works

```bash
pytest -q                    # 79 tests: auth boundaries, dispatch, idempotency, config
./scripts/verify.sh          # 16 checks — deps, lint, tests, then live 401/403s
                             #   against a real server, incl. a forged token rejected
python -m scripts.race_test  # 15 concurrent dispatches at 3 replicas → zero duplicates
```

`verify.sh` is the one to run before demoing. `race_test` is the concurrency
claim — it needs the stack scaled to 3 (below), and also runs in CI.

## Load test

```bash
API_PORTS=8000-8002:8000 docker compose up -d --scale api=3
docker compose exec api python -m scripts.seed_users
RATE_LIMIT_ENABLED=false locust -f locustfile.py --host http://localhost:8000
```

Then open http://localhost:8089 — 50 users, 60 s.

Read **`POST /orders/dispatch` separately from order creation**; they are
different systems wearing one API, and the dispatch claim is the number that
means anything. Everything shares one laptop, so treat the results as a
**regression comparison, not capacity**.

---

## The two things that will bite you

**The port range.** Compose publishes `${API_PORTS:-8000-8002:8000}` so
`--scale api=3` has free host ports — but with a range **Docker may pick any
port in it even when 8000 is free**, including on `--build`. Pin it on *every*
`up`, and check with `docker compose port api 8000`.

**`down -v` wipes the users.** It deletes pgdata and kafkadata, so re-run both
seed scripts after. That is the entire recovery procedure.

| Symptom | Cause | Fix |
|---|---|---|
| Console won't load at `:8000` | Docker picked another port | `docker compose port api 8000`, pin with `API_PORTS=8000:8000` |
| Every login 401 | `down -v` wiped the users | `seed_users` |
| Board empty | `seed_demo` not run | `seed_demo` |
| Stack won't parse | `JWT_SECRET` unset — no default, by design | `openssl rand -hex 32` into `.env` |
| "No rider available" | Redis flushed; riders in Postgres but not in the geohash index | `python -m scripts.reindex_riders` |
| Console looks out of date at `:8000` | Host `uvicorn` serves a hand-built `frontend/dist/` | `cd frontend && npm run build`, or use `npm run dev` |
