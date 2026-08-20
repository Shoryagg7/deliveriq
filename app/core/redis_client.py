"""Redis clients — one sync, one async, both with timeouts.

TWO clients on purpose (G06). The service layer runs inside sync `def` routes,
which FastAPI hands to a threadpool, so blocking there costs one worker thread.
The middleware chain runs on the event loop, where a blocking call stalls EVERY
in-flight request on the process — so the middleware must await.

Both carry timeouts (G07). The fail-open paths in the middleware catch
`redis.RedisError`; a Redis that accepts a connection and then hangs raises
nothing at all without a socket timeout, so the protective control fails in
exactly the mode it was written to survive.
"""

import redis
import redis.asyncio as aioredis

from app.core.config import settings

_TIMEOUTS = {
    "socket_timeout": settings.redis_socket_timeout,
    "socket_connect_timeout": settings.redis_connect_timeout,
    # A dropped connection surfaces as a timeout, not an error, so retrying it
    # once turns a blip into a slow request instead of a 500.
    "retry_on_timeout": True,
    # Proactively reap connections a firewall or Redis idle-timeout has killed.
    "health_check_interval": 30,
}

# Sync — services, workers, scripts, and the /ready probe (a sync route).
redis_client = redis.Redis.from_url(
    settings.redis_url, decode_responses=True, **_TIMEOUTS
)

# Async — middleware only. Same server, same keys, different call style.
async_redis_client = aioredis.Redis.from_url(
    settings.redis_url, decode_responses=True, **_TIMEOUTS
)
