"""Sadə Redis əsaslı rate limiter (Telegram limitlərinə uyğun)"""
import time
import redis.asyncio as redis
from config import Config

_r: redis.Redis | None = None

async def init_redis():
    global _r
    _r = redis.from_url(Config.REDIS_URL, decode_responses=True)
    try:
        await _r.ping()
    except Exception:
        _r = None
    return _r

async def allow(key: str, limit: int, per_seconds: int) -> bool:
    """Sliding window rate limit"""
    if _r is None:
        return True
    now = int(time.time())
    bucket = f"rl:{key}:{now // per_seconds}"
    cur = await _r.incr(bucket)
    if cur == 1:
        await _r.expire(bucket, per_seconds + 1)
    return cur <= limit
