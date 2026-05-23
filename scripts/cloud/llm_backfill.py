"""Drain the DB-backed LLM queue with a single worker process."""
from __future__ import annotations

import asyncio
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "backend"))

from dotenv import load_dotenv

load_dotenv(os.environ.get("BACKEND_ENV_PATH", "/etc/campus-opportunity/backend.env"))

from app.application.services.llm_queue_service import LlmQueueService
from app.core.config import Settings
from app.db.session import build_session_factory


async def main() -> None:
    settings = Settings.from_env()
    _, session_factory = build_session_factory(settings)
    service = LlmQueueService(session_factory, settings)
    seed = service.enqueue_missing_tasks()
    print(f"Seeded queue: {seed}", flush=True)

    while True:
        result = await service.process_batch()
        print(f"Queue batch: {result}", flush=True)
        if result.get("claimed", 0) == 0:
            break
        time.sleep(1)


if __name__ == "__main__":
    asyncio.run(main())
