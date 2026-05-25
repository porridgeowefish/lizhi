from __future__ import annotations

import json

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from app.application.services.job_queue_service import JobQueueService
from app.db.models import JobQueue, Source
from app.domain.enums import JobType, SourceStatus
from app.schemas.responses import JobCreateResponse, JobResponse, JobSummaryResponse

router = APIRouter(prefix="/api/jobs", tags=["jobs"])


class RefreshJobRequest(BaseModel):
    source_id: str | None = None
    start_page: int | None = None
    end_page: int | None = None


def _payload(value: str) -> dict:
    try:
        return json.loads(value or "{}")
    except json.JSONDecodeError:
        return {}


def _serialize_job(job: JobQueue) -> JobResponse:
    return JobResponse(
        id=job.id,
        job_type=job.job_type,
        dedupe_key=job.dedupe_key,
        status=job.status,
        priority=job.priority,
        payload=_payload(job.payload_json),
        attempts=job.attempts,
        max_attempts=job.max_attempts,
        last_error=job.last_error,
        result=_payload(job.result_json),
        created_at=job.created_at,
        updated_at=job.updated_at,
        finished_at=job.finished_at,
    )


def _queue(request: Request) -> JobQueueService:
    return request.app.state.job_queue_service


@router.post("/refresh", response_model=JobCreateResponse)
def create_refresh_jobs(request: Request, payload: RefreshJobRequest | None = None):
    payload = payload or RefreshJobRequest()
    queue = _queue(request)
    settings = request.app.state.settings
    db = request.app.state.session_factory()
    try:
        query = db.query(Source).filter(Source.status == SourceStatus.ENABLED.value)
        if payload.source_id:
            query = query.filter(Source.upstream_source_id == payload.source_id)
        sources = query.order_by(Source.id.asc()).all()
        jobs = []
        start_page = payload.start_page if payload.start_page is not None else settings.upstream_refresh_start_page
        end_page = payload.end_page if payload.end_page is not None else settings.upstream_refresh_end_page
        for source in sources:
            job = queue.enqueue(
                JobType.REFRESH_SOURCE,
                f"source:{source.upstream_source_id}:pages:{start_page}-{end_page}",
                {
                    "source_id": source.upstream_source_id,
                    "start_page": start_page,
                    "end_page": end_page,
                },
                priority=50,
            )
            jobs.append(_serialize_job(job))
        return JobCreateResponse(created=len(jobs), jobs=jobs)
    finally:
        db.close()


@router.get("/summary", response_model=JobSummaryResponse)
def get_job_summary(request: Request):
    return JobSummaryResponse(**_queue(request).summary())


@router.get("/{job_id}", response_model=JobResponse)
def get_job(job_id: int, request: Request):
    job = _queue(request).get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="job not found")
    return _serialize_job(job)
