from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy import func

from app.application.services.job_queue_service import JobQueueService
from app.db.models import JobQueue, Post, Source, SyncJob
from app.domain.enums import JobStatus, JobType, SourceStatus
from app.schemas.responses import JobCreateResponse, JobResponse, JobSummaryResponse

router = APIRouter(prefix="/api/jobs", tags=["jobs"])


class RefreshJobRequest(BaseModel):
    source_id: str | None = None
    start_page: int | None = None
    end_page: int | None = None


class BackfillJobRequest(BaseModel):
    source_id: str | None = None
    limit: int | None = None


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


@router.post("/backfill", response_model=JobCreateResponse)
def create_backfill_jobs(request: Request, payload: BackfillJobRequest | None = None):
    payload = payload or BackfillJobRequest()
    queue = _queue(request)
    settings = request.app.state.settings
    db = request.app.state.session_factory()
    try:
        query = db.query(Source).filter(Source.status == SourceStatus.ENABLED.value)
        if payload.source_id:
            query = query.filter(Source.upstream_source_id == payload.source_id)
        sources = query.order_by(Source.id.asc()).all()
        limit = payload.limit or settings.post_fetch_limit
        jobs = []
        for source in sources:
            job = queue.enqueue(
                JobType.SYNC_SOURCE_POSTS,
                f"source:{source.upstream_source_id}:mode:backfill:limit:{limit}",
                {"source_id": source.upstream_source_id, "limit": limit, "mode": "backfill"},
                priority=70,
            )
            jobs.append(_serialize_job(job))
        return JobCreateResponse(created=len(jobs), jobs=jobs)
    finally:
        db.close()


@router.get("/summary", response_model=JobSummaryResponse)
def get_job_summary(request: Request):
    return JobSummaryResponse(**_queue(request).summary())


@router.get("/ingestion-health")
def get_ingestion_health(request: Request):
    db = request.app.state.session_factory()
    try:
        since = datetime.now(timezone.utc) - timedelta(hours=24)
        queue_rows = (
            db.query(JobQueue.job_type, JobQueue.status, func.count(JobQueue.id))
            .group_by(JobQueue.job_type, JobQueue.status)
            .all()
        )
        hourly_posts = (
            db.query(
                func.substr(Post.created_at, 1, 13).label("hour"),
                func.count(Post.id).label("inserted"),
                func.min(Post.published_at).label("oldest_published_at"),
                func.max(Post.published_at).label("newest_published_at"),
            )
            .filter(Post.created_at >= since)
            .group_by("hour")
            .order_by("hour")
            .all()
        )
        top_sources = (
            db.query(
                Source.name,
                func.count(Post.id).label("inserted"),
                func.min(Post.published_at).label("oldest_published_at"),
                func.max(Post.published_at).label("newest_published_at"),
            )
            .join(Post, Post.source_id == Source.id)
            .filter(Post.created_at >= since)
            .group_by(Source.id)
            .order_by(func.count(Post.id).desc())
            .limit(20)
            .all()
        )
        oldest_active_job = (
            db.query(JobQueue)
            .filter(JobQueue.status.in_([JobStatus.PENDING.value, JobStatus.RUNNING.value, JobStatus.FAILED.value]))
            .order_by(JobQueue.priority.asc(), JobQueue.created_at.asc(), JobQueue.id.asc())
            .first()
        )
        last_successful_sync = (
            db.query(SyncJob)
            .filter(SyncJob.status == "completed")
            .order_by(SyncJob.finished_at.desc().nullslast(), SyncJob.id.desc())
            .first()
        )
        return {
            "generated_at": datetime.now(timezone.utc),
            "posts_total": db.query(func.count(Post.id)).scalar() or 0,
            "sources_enabled": db.query(func.count(Source.id)).filter(Source.status == SourceStatus.ENABLED.value).scalar() or 0,
            "last_successful_sync": {
                "id": last_successful_sync.id,
                "finished_at": last_successful_sync.finished_at,
                "posts_inserted": last_successful_sync.posts_inserted,
                "posts_updated": last_successful_sync.posts_updated,
            }
            if last_successful_sync
            else None,
            "oldest_active_job": _serialize_job(oldest_active_job).model_dump() if oldest_active_job else None,
            "queue_by_type_status": [
                {"job_type": job_type, "status": status, "count": count}
                for job_type, status, count in queue_rows
            ],
            "posts_inserted_by_hour_24h": [
                {
                    "hour": hour,
                    "inserted": inserted,
                    "oldest_published_at": oldest_published_at,
                    "newest_published_at": newest_published_at,
                }
                for hour, inserted, oldest_published_at, newest_published_at in hourly_posts
            ],
            "top_sources_inserted_24h": [
                {
                    "source_name": name,
                    "inserted": inserted,
                    "oldest_published_at": oldest_published_at,
                    "newest_published_at": newest_published_at,
                }
                for name, inserted, oldest_published_at, newest_published_at in top_sources
            ],
        }
    finally:
        db.close()


@router.get("/{job_id}", response_model=JobResponse)
def get_job(job_id: int, request: Request):
    job = _queue(request).get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="job not found")
    return _serialize_job(job)
