from functools import lru_cache

from redis.asyncio import Redis

from app.core.config import settings


@lru_cache
def get_redis_client() -> Redis:
    return Redis.from_url(
        settings.redis_url,
        decode_responses=False,
        socket_connect_timeout=5,
        # BRPOP is used as a blocking poll in the worker, so reads must be allowed
        # to wait longer than the normal queue poll window without killing the process.
        socket_timeout=None,
        health_check_interval=30,
    )
