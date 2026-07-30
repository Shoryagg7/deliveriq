# app/core/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict


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

    # Dev default only — deployment MUST override JWT_SECRET. A shipped default
    # secret means anyone with the source can mint an admin token.
    jwt_secret: str = "dev-only-change-me"
    jwt_expire_minutes: int = 60


settings = Settings()  # type: ignore
