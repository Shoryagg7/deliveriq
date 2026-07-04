import json
import logging

from app.core.logging_config import setup_logging
from app.core.redis_client import redis_client

setup_logging()
logger = logging.getLogger("deliveriq.worker")
pubsub = redis_client.pubsub()
pubsub.subscribe("order.dispatched")
print("Notification worker listening on 'order.dispatched'...")

try:
    for msg in pubsub.listen():
        if msg["type"] != "message":
            continue
        data = json.loads(msg["data"])
        logger.info(f"[notify] order {data['order_id']} → rider {data['rider_id']}")
except KeyboardInterrupt:
    print("\nWorker stopped.")
finally:
    pubsub.close()
