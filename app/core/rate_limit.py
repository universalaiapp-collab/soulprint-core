import redis
import os

REDIS_HOST = os.getenv("REDIS_HOST", "127.0.0.1")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_DB = int(os.getenv("REDIS_DB", 0))

redis_client = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    db=REDIS_DB,
    decode_responses=True,
    socket_connect_timeout=2,
    socket_timeout=2,
    retry_on_timeout=True,
)

def check_org_rate_limit(org_id: str, limit: int = 100):

    key = f"org_rate:{org_id}"

    try:
        count = redis_client.incr(key)

        if count == 1:
            redis_client.expire(key, 60)

        return count <= limit

    except redis.exceptions.RedisError:
        # Fail-open policy (production safe)
        return True
