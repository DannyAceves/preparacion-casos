from __future__ import annotations

import asyncio
import logging
import signal
from contextlib import suppress

from app.core.config import settings
from app.core.logging import configure_logging
from app.db.session import AsyncSessionLocal
from app.queue.redis_client import get_redis_client
from app.queue.redis_queue import RedisQueue
from app.services.document_processing_runtime import DocumentProcessingRuntimeService
from app.services.document_processing_tasks import DocumentProcessingTaskService

logger = logging.getLogger(__name__)


class DocumentProcessingWorker:
    def __init__(self) -> None:
        self.redis_client = get_redis_client()
        self.queue = RedisQueue(self.redis_client)
        self._running = True

    async def run(self) -> None:
        logger.info("Document worker started", extra={"event": "worker_started"})
        while self._running:
            message = await self.queue.dequeue()
            if message is None:
                continue
            await self._process_message(message.job_id)

    async def _process_message(self, job_id) -> None:
        async with AsyncSessionLocal() as session:
            runtime = DocumentProcessingRuntimeService(session, self.queue)
            tasks = DocumentProcessingTaskService(session)
            try:
                job = await runtime.mark_job_running(job_id)
                payload = await tasks.run_job(
                    document_id=job.document_id,
                    job_type=job.job_type,
                    job_payload=job.payload,
                )
                await runtime.mark_job_completed(job.id, payload)
            except Exception as exc:  # noqa: BLE001
                logger.exception("Document processing job failed", exc_info=exc)
                await runtime.mark_job_failed(job_id, str(exc))

    def stop(self) -> None:
        self._running = False
        logger.info("Document worker stopping", extra={"event": "worker_stopping"})


async def main() -> None:
    configure_logging(settings.app_debug)
    worker = DocumentProcessingWorker()
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        with suppress(NotImplementedError):
            loop.add_signal_handler(sig, worker.stop)
    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())
