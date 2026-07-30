# --- stage 1: build the React bundle ---------------------------------------
# Built INSIDE the image so `docker compose up --build` is the only command
# anyone needs. Committing dist/ would mean a stale UI whenever someone forgets
# to rebuild, plus a diff full of minified noise on every change.
FROM node:24-slim AS frontend

WORKDIR /ui
# Package files first: this layer stays cached unless dependencies actually
# change, so editing a component doesn't reinstall node_modules.
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build


# --- stage 2: the API ------------------------------------------------------
FROM python:3.14-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends gcc libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
# Only the BUILT bundle crosses over — no node_modules, no Node runtime in the
# final image, and no dependence on whatever happens to be in a local dist/.
COPY --from=frontend /ui/dist ./frontend/dist

EXPOSE 8000

CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
