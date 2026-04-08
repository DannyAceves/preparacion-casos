from __future__ import annotations

import asyncio

from sqlalchemy import text

from app.db.session import AsyncSessionLocal
from app.queue.redis_client import get_redis_client


async def main() -> int:
    async with AsyncSessionLocal() as session:
        await session.execute(text("SELECT 1"))
    redis_client = get_redis_client()
    await redis_client.ping()
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
