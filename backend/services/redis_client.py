"""
Shared Redis client.

Using a module-level variable so the connection pool is created once at startup
and reused across requests / background tasks.
"""
import redis.asyncio as aioredis
from config import settings

_redis: aioredis.Redis | None = None

ODDS_TTL = 90  # seconds — matches our poll interval with a small buffer
ARB_TTL = 90


async def get_redis() -> aioredis.Redis:
    global _redis
    if _redis is None:
        _redis = aioredis.from_url(settings.redis_url, decode_responses=True)
    return _redis


async def close_redis() -> None:
    global _redis
    if _redis is not None:
        await _redis.aclose()
        _redis = None
