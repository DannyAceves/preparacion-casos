from __future__ import annotations

import json

from redis.asyncio import Redis

from app.core.config import settings
from app.schemas.document_processing import QueueJobMessage


class RedisQueue:
    def __init__(self, redis_client: Redis, queue_name: str | None = None) -> None:
        self.redis_client = redis_client
        self.queue_name = queue_name or settings.document_processing_queue_name

    async def enqueue(self, message: QueueJobMessage) -> None:
        await self.redis_client.lpush(self.queue_name, message.model_dump_json())

    async def dequeue(self, timeout: int | None = None) -> QueueJobMessage | None:
        result = await self.redis_client.brpop(
            self.queue_name,
            timeout=timeout if timeout is not None else settings.document_processing_worker_poll_timeout,
        )
        if result is None:
            return None
        _, payload = result
        raw = payload.decode("utf-8") if isinstance(payload, bytes) else payload
        return QueueJobMessage.model_validate(json.loads(raw))
