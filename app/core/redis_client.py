import os

import redis

REDIS_DB = int(os.getenv("REDIS_DB", "0"))  # tests set 15; default 0 unchanged
redis_client = redis.Redis(
    host="localhost", port=6379, db=REDIS_DB, decode_responses=True
)

