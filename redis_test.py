import redis

# Connect to the same server redis-cli talks to
r = redis.Redis(host="localhost", port=6379, decode_responses=True)

print(r.ping())  # → True   (the PONG you saw, as a Python bool)

r.set("rider:42:orders", 3)
print(r.get("rider:42:orders"))  # → 3

print(r.incr("rider:42:orders"))  # → 4
