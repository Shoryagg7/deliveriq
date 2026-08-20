# app/core/config.py
from pydantic import ValidationError, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# HS256 signs with a key of arbitrary length, but a key shorter than the hash it
# feeds is weaker than the algorithm it configures. 32 bytes is the floor.
MIN_JWT_SECRET_BYTES = 32

# Values that have shipped in this repo, or are the obvious first guess. A
# secret published in source control is not a secret — and every require_ops
# guard in the project is worth exactly as much as this value's unpredictability.
BANNED_JWT_SECRETS = frozenset(
    {"dev-only-change-me", "change-me", "changeme", "secret", "password", "test"}
)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str
    redis_url: str = "redis://localhost:6379/0"
    rate_limit_enabled: bool = True
    rate_limit_capacity: int = 100
    rate_limit_refill_per_min: int = 100

    # Bootstrap = the handshake address only. The broker replies with its
    # advertised listener, and THAT is what the client actually connects to.
    #   host shell  -> localhost:9092  (PLAINTEXT_HOST listener)
    #   in Compose  -> kafka:19092     (PLAINTEXT listener)
    kafka_bootstrap: str = "localhost:9092"

    # Where the `audit` consumer group appends its trail. Container overrides
    # this to a mounted volume path so the file survives a rebuild.
    audit_log_path: str = "audit.log"

    # NO DEFAULT, deliberately (G04). A default that works is a default nobody
    # overrides, and a shipped signing key lets anyone with the source mint an
    # ops token. A control that can be skipped by forgetting a variable is not a
    # control; refusing to boot is the only version of this that always runs.
    jwt_secret: str
    jwt_expire_minutes: int = 60

    # --- Postgres pool (G08) -----------------------------------------------
    # Explicit, because the sizing arithmetic only means something against a
    # number that is actually configured: replicas x pool_size must stay under
    # the server's max_connections (~100 by default). 3 x 20 = 60 leaves room
    # for migrations, psql, and the workers.
    db_pool_size: int = 20
    db_max_overflow: int = 10
    # Recycle before any sane server-side idle timeout can close a connection
    # underneath us.
    db_pool_recycle: int = 1800

    # --- Redis (G07) --------------------------------------------------------
    # Without these, a Redis that ACCEPTS a connection and then hangs blocks
    # forever, and the deliberate fail-open in the middleware never runs —
    # it only catches a refused connection. A timeout is what turns a hang
    # into a RedisError the middleware can actually degrade on.
    redis_socket_timeout: float = 2.0
    redis_connect_timeout: float = 2.0

    # --- Idempotency (G19) --------------------------------------------------
    # Must outlive the slowest request the server will serve, or the in-flight
    # claim expires while the first attempt is still running and a retry
    # double-executes — the exact outcome the middleware exists to prevent.
    idempotency_lock_ttl: int = 120

    # --- Rate limiting (G13) ------------------------------------------------
    # Only enable behind a proxy that OVERWRITES X-Forwarded-For. Trusting it
    # when nothing rewrites it lets any caller forge a fresh IP per request,
    # which is the bypass this setting exists to avoid re-introducing.
    trust_proxy_headers: bool = False

    @field_validator("jwt_secret")
    @classmethod
    def _reject_weak_jwt_secret(cls, v: str) -> str:
        if v.strip().lower() in BANNED_JWT_SECRETS:
            raise ValueError(
                "JWT_SECRET is a known placeholder value. Anyone with access to "
                "this repository could forge an ops token with it."
            )
        if len(v.encode()) < MIN_JWT_SECRET_BYTES:
            raise ValueError(
                f"JWT_SECRET must be at least {MIN_JWT_SECRET_BYTES} bytes; "
                f"got {len(v.encode())}."
            )
        return v


try:
    settings = Settings()  # type: ignore[call-arg]
except ValidationError as exc:
    # Fail LOUDLY and with the remedy attached. Pydantic's raw error names the
    # field but not what to do about it, and this is the one config error that
    # is a security hole rather than an inconvenience.
    raise RuntimeError(
        f"DeliverIQ cannot start — invalid configuration:\n\n{exc}\n\n"
        "Generate a JWT_SECRET with:\n"
        "    python -c 'import secrets; print(secrets.token_urlsafe(48))'\n"
        "then set it in .env (local) or the environment (Compose/CI/deploy).\n"
    ) from exc
