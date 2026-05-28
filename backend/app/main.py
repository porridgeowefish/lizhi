from __future__ import annotations

import asyncio
import logging
import threading
from contextlib import asynccontextmanager
from collections.abc import Awaitable, Callable

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI
import uvicorn

from app.api.routes.health import router as health_router
from app.api.routes.jobs import router as jobs_router
from app.api.routes.posts import router as posts_router
from app.api.routes.sources import router as sources_router
from app.api.routes.sync import router as sync_router
from app.api.routes.support import router as support_router
from app.application.services.ingestion_service import IngestionService
from app.application.services.job_queue_service import JobQueueService
from app.application.services.llm_queue_service import LlmQueueService
from app.application.services.query_service import QueryService
from app.core.config import Settings
from app.db.session import build_session_factory
from app.domain.enums import SyncTriggerType
from app.infrastructure.connectors.werss import WerssConnector

_logger = logging.getLogger(__name__)


def create_app(settings: Settings | None = None, connector=None) -> FastAPI:
    settings = settings or Settings.from_env()
    _, session_factory = build_session_factory(settings)
    connector = connector or (WerssConnector(settings) if settings.upstream_base_url else None)
    query_service = QueryService(homepage_recent_undated_days=settings.homepage_recent_undated_days)
    job_queue_service = JobQueueService(session_factory)
    ingestion_service = IngestionService(session_factory, connector, settings) if connector else None
    llm_queue_service = LlmQueueService(session_factory, settings) if settings.llm_queue_enabled and settings.llm_enabled else None

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        scheduler = None
        background_lock = threading.Lock()
        if settings.enable_scheduler and ingestion_service:
            scheduler = AsyncIOScheduler()
            scheduler.add_job(
                _run_background_job,
                "interval",
                args=[
                    "backend_sync",
                    background_lock,
                    lambda: ingestion_service.run_sync(SyncTriggerType.SCHEDULE),
                ],
                minutes=settings.sync_interval_minutes,
                id="backend_sync",
                replace_existing=True,
                max_instances=1,
                coalesce=True,
                misfire_grace_time=300,
            )
            if settings.upstream_refresh_enabled and hasattr(connector, "refresh_source"):
                scheduler.add_job(
                    _run_background_job,
                    "interval",
                    args=[
                        "upstream_refresh_then_sync",
                        background_lock,
                        ingestion_service.refresh_upstream_sources_then_sync,
                    ],
                    minutes=settings.upstream_refresh_interval_minutes,
                    id="upstream_refresh_then_sync",
                    replace_existing=True,
                    max_instances=1,
                    coalesce=True,
                    misfire_grace_time=900,
                )
            if llm_queue_service is not None:
                scheduler.add_job(
                    _run_background_job,
                    "interval",
                    args=["llm_queue_worker", background_lock, llm_queue_service.process_batch],
                    seconds=settings.llm_worker_interval_seconds,
                    id="llm_queue_worker",
                    replace_existing=True,
                    max_instances=1,
                    coalesce=True,
                    misfire_grace_time=120,
            )
            scheduler.start()
            if settings.upstream_refresh_enabled and settings.upstream_refresh_on_startup and hasattr(connector, "refresh_source"):
                asyncio.create_task(
                    _run_background_job(
                        "startup_upstream_refresh",
                        background_lock,
                        ingestion_service.refresh_upstream_sources_then_sync,
                    )
                )
            else:
                asyncio.create_task(
                    _run_background_job(
                        "startup_sync",
                        background_lock,
                        lambda: ingestion_service.run_sync(SyncTriggerType.STARTUP),
                    )
                )
            if llm_queue_service is not None:
                asyncio.create_task(asyncio.to_thread(llm_queue_service.enqueue_missing_tasks))
        yield
        if scheduler is not None:
            scheduler.shutdown()

    app = FastAPI(title=settings.app_name, version=settings.app_version, lifespan=lifespan)
    app.state.settings = settings
    app.state.session_factory = session_factory
    app.state.query_service = query_service
    app.state.job_queue_service = job_queue_service
    app.state.ingestion_service = ingestion_service
    app.state.llm_queue_service = llm_queue_service

    app.include_router(posts_router)
    app.include_router(sources_router)
    app.include_router(sync_router)
    app.include_router(jobs_router)
    app.include_router(support_router)
    app.include_router(health_router)
    return app


async def _run_background_job(
    name: str,
    lock: threading.Lock,
    job_factory: Callable[[], Awaitable[object]],
) -> object | None:
    if not lock.acquire(blocking=False):
        _logger.warning("background job skipped because another job is running: %s", name)
        return {"status": "skipped", "reason": "background job already running", "job": name}
    try:
        result = await asyncio.to_thread(lambda: asyncio.run(job_factory()))
        _logger.warning("background job completed: %s result=%s", name, result)
        return result
    except Exception:  # noqa: BLE001
        _logger.exception("background job failed: %s", name)
        return {"status": "failed", "job": name}
    finally:
        lock.release()


app = create_app()


if __name__ == "__main__":
    runtime_settings = Settings.from_env()
    uvicorn.run("app.main:app", host=runtime_settings.host, port=runtime_settings.port, reload=True)
