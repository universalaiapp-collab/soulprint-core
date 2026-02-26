import time
from fastapi import HTTPException
from app.core.redis_client import redis_client

def check_rate_limit(org_id: str, limit_per_sec: int):
    current_second = int(time.time())
    key = f"ratelimit:{org_id}:{current_second}"

    request_count = redis_client.incr(key)

    if request_count == 1:
        redis_client.expire(key, 2)

    if request_count > limit_per_sec:
        raise HTTPException(
            status_code=429,
            detail="RATE_LIMIT_EXCEEDED"
        )
