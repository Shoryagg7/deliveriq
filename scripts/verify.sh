#!/usr/bin/env bash
# One command to check the project is sound: config guard, lint, tests, and a
# live smoke test of the auth boundaries against a real server (not TestClient).
#
#   ./scripts/verify.sh
#
# Assumes the hybrid dev setup: infra in Compose, app on the host.
set -uo pipefail
cd "$(dirname "$0")/.."

PASS=0; FAIL=0
ok()   { printf '  \033[32m✓\033[0m %s\n' "$1"; PASS=$((PASS+1)); }
bad()  { printf '  \033[31m✗\033[0m %s\n' "$1"; FAIL=$((FAIL+1)); }
step() { printf '\n\033[1m%s\033[0m\n' "$1"; }

step "1/5  Configuration"
if grep -q '^JWT_SECRET=.\{32,\}' .env 2>/dev/null; then
  ok "JWT_SECRET present and long enough"
else
  bad "JWT_SECRET missing or too short in .env"
  echo "      fix: printf 'JWT_SECRET=%s\\n' \"\$(python3 -c 'import secrets;print(secrets.token_urlsafe(48))')\" >> .env"
  exit 1
fi
# The guard itself: the value that used to ship must abort startup.
if JWT_SECRET=dev-only-change-me python3 -c 'import app.core.config' 2>/dev/null; then
  bad "the old default secret still boots (G04 regressed)"
else
  ok "placeholder secret refuses to boot (G04)"
fi

step "2/5  Infrastructure"
docker compose up -d db redis kafka >/dev/null 2>&1
for _ in $(seq 1 30); do
  docker compose exec -T db pg_isready -U deliveriq_user -d deliveriq_db >/dev/null 2>&1 && break
  sleep 1
done
docker compose exec -T db pg_isready -U deliveriq_user -d deliveriq_db >/dev/null 2>&1 \
  && ok "postgres ready" || bad "postgres not ready"
docker compose exec -T redis redis-cli ping >/dev/null 2>&1 \
  && ok "redis ready" || bad "redis not ready"
docker compose up kafka-init --exit-code-from kafka-init >/dev/null 2>&1 \
  && ok "kafka topics created" || bad "kafka topics failed"
alembic upgrade head >/dev/null 2>&1 && ok "migrations applied" || bad "migrations failed"

step "3/5  Lint"
if python3 -m ruff check app tests scripts >/dev/null 2>&1; then ok "ruff clean"; else bad "ruff found issues"; fi

step "4/5  Tests"
if python3 -m pytest tests/ -q 2>&1 | tail -1 | grep -qE '[0-9]+ passed'; then
  ok "$(python3 -m pytest tests/ -q 2>&1 | tail -1 | tr -d '\n')"
else
  bad "pytest failed — run: python3 -m pytest tests/ -q"
fi

step "5/5  Live auth boundaries (real server)"
python3 -m scripts.seed_users >/dev/null 2>&1
python3 -m uvicorn app.main:app --port 8010 --log-level error >/dev/null 2>&1 &
API_PID=$!
trap 'kill $API_PID 2>/dev/null' EXIT
for _ in $(seq 1 40); do
  curl -sf http://localhost:8010/health >/dev/null 2>&1 && break
  sleep 0.5
done

code() { curl -s -o /dev/null -w '%{http_code}' "$@"; }
B=http://localhost:8010

[ "$(code $B/health)" = 200 ] && ok "GET  /health                  200" || bad "GET /health"
[ "$(code -X POST $B/orders -H 'Content-Type: application/json' -d '{"restaurant_id":1,"value":100,"pickup_lat":28.6,"pickup_lon":77.2,"drop_lat":28.7,"drop_lon":77.1}')" = 401 ] \
  && ok "POST /orders            anon 401  (G02)" || bad "POST /orders is not protected (G02)"
[ "$(code $B/orders)" = 401 ]  && ok "GET  /orders            anon 401  (G03)" || bad "GET /orders is not protected (G03)"
[ "$(code $B/riders)" = 401 ]  && ok "GET  /riders            anon 401  (G03)" || bad "GET /riders is not protected (G03)"
[ "$(code -X PATCH $B/riders/1/location -H 'Content-Type: application/json' -d '{"lat":1,"lon":1}')" = 401 ] \
  && ok "PATCH /riders/1/location anon 401  (G01)" || bad "rider location is not protected (G01)"

TOKEN=$(curl -s -X POST $B/auth/login -H 'Content-Type: application/json' \
        -d '{"email":"ops@deliveriq.io","password":"opspassword123"}' \
        | python3 -c 'import json,sys; print(json.load(sys.stdin).get("access_token",""))' 2>/dev/null)
if [ -n "$TOKEN" ]; then
  ok "ops login issues a token"
  [ "$(code $B/riders -H "Authorization: Bearer $TOKEN")" = 200 ] \
    && ok "GET  /riders             ops 200" || bad "ops cannot read /riders"
else
  bad "ops login failed (run: python3 -m scripts.seed_users)"
fi
# A forged token must not be accepted — the point of the G04 secret.
FORGED=$(python3 -c "
from jose import jwt
from datetime import datetime, timedelta, UTC
print(jwt.encode({'sub':'ops@deliveriq.io','is_admin':True,'exp':datetime.now(UTC)+timedelta(hours=1)},'dev-only-change-me',algorithm='HS256'))")
[ "$(code $B/admin/stats -H "Authorization: Bearer $FORGED")" = 401 ] \
  && ok "forged ops token rejected      401  (G04)" || bad "FORGED TOKEN ACCEPTED (G04 regressed)"

printf '\n\033[1m%d passed, %d failed\033[0m\n' "$PASS" "$FAIL"
[ "$FAIL" -eq 0 ] && printf '\033[32mProject verified.\033[0m\n' || printf '\033[31mSee failures above.\033[0m\n'
exit $((FAIL > 0))
