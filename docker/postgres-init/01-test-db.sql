-- Auto-creates the pytest database on first init of an empty pgdata volume.
-- Postgres runs everything in /docker-entrypoint-initdb.d ONCE, only when the
-- data directory is fresh — i.e. exactly the `docker compose down -v` → `up` case.
-- Warm restarts (down without -v) skip this; the DB already exists.
CREATE DATABASE deliveriq_test_db OWNER deliveriq_user;
