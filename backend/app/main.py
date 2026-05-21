from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager

from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI
import uvicorn

from app.api.routes.articles import router as articles_router
from app.api.routes.health import router as health_router
from app.api.routes.sources import router as sources_router
from app.api.routes.sync import router as sync_router
from app.application.services.ingestion_service import IngestionService
from app.application.services.query_service import QueryService
from app.core.config import Settings
from app.db.session import build_session_factory
from app.domain.enums import SyncTriggerType
from app.infrastructure.connectors.werss import WerssConnector


def create_app(settings: Settings | None = None, connector=None) -> FastAPI:
    settings = settings or Settings.from_env()
    _, session_factory = build_session_factory(settings)
    connector = connector or (WerssConnector(settings) if settings.upstream_base_url else None)
    query_service = QueryService()
    ingestion_service = IngestionService(session_factory, connector, settings) if connector else None

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        scheduler = None
        if settings.enable_scheduler and ingestion_service:
            scheduler = BackgroundScheduler()
            scheduler.add_job(
                lambda: asyncio.run(ingestion_service.run_sync(SyncTriggerType.SCHEDULE)),
                "interval",
                minutes=settings.sync_interval_minutes,
                id="backend_sync",
            )
            scheduler.start()
            asyncio.create_task(ingestion_service.run_sync(SyncTriggerType.STARTUP))
        yield
        if scheduler is not None:
            scheduler.shutdown()

    app = FastAPI(title=settings.app_name, version=settings.app_version, lifespan=lifespan)
    app.state.settings = settings
    app.state.session_factory = session_factory
    app.state.query_service = query_service
    app.state.ingestion_service = ingestion_service

    app.include_router(articles_router)
    app.include_router(sources_router)
    app.include_router(sync_router)
    app.include_router(health_router)
    return app


app = create_app()


if __name__ == "__main__":
    runtime_settings = Settings.from_env()
    uvicorn.run("app.main:app", host=runtime_settings.host, port=runtime_settings.port, reload=True)
