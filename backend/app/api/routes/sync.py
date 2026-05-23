from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.serializers import serialize_sync_job
from app.db.models import LlmTask
from app.domain.enums import SyncTriggerType
from app.schemas.responses import SyncJobResponse

router = APIRouter(prefix="/api/sync", tags=["sync"])


@router.post("", response_model=SyncJobResponse)
async def manual_sync(request: Request):
    if not request.app.state.ingestion_service:
        raise HTTPException(status_code=503, detail="upstream not configured")
    job = await request.app.state.ingestion_service.run_sync(SyncTriggerType.MANUAL)
    db: Session = request.app.state.session_factory()
    try:
        hydrated = request.app.state.query_service.get_sync_job(db, job.id)
        if hydrated is None:
            raise HTTPException(status_code=404, detail="sync job not found")
        return serialize_sync_job(hydrated)
    finally:
        db.close()


@router.get("/jobs/{job_id}", response_model=SyncJobResponse)
def get_sync_job(request: Request, job_id: int):
    db: Session = request.app.state.session_factory()
    try:
        job = request.app.state.query_service.get_sync_job(db, job_id)
        if job is None:
            raise HTTPException(status_code=404, detail="sync job not found")
        return serialize_sync_job(job)
    finally:
        db.close()


@router.get("/llm-queue")
def get_llm_queue_status(request: Request):
    db: Session = request.app.state.session_factory()
    try:
        rows = (
            db.query(LlmTask.status, func.count(LlmTask.id))
            .group_by(LlmTask.status)
            .all()
        )
        return {"stats": {status: count for status, count in rows}}
    finally:
        db.close()


@router.post("/llm-queue/run")
async def run_llm_queue_once(request: Request):
    service = getattr(request.app.state, "llm_queue_service", None)
    if service is None:
        raise HTTPException(status_code=503, detail="llm queue not configured")
    return await service.process_batch()
