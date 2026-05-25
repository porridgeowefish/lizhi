from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from enum import StrEnum
from typing import Any

from sqlalchemy import func, or_, select
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session, sessionmaker

from app.db.models import JobQueue
from app.domain.enums import JobStatus, JobType


def _value(value: str | StrEnum) -> str:
    return value.value if isinstance(value, StrEnum) else str(value)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class JobQueueService:
    def __init__(self, session_factory: sessionmaker[Session]):
        self.session_factory = session_factory

    def enqueue(
        self,
        job_type: str | JobType,
        dedupe_key: str,
        payload: dict[str, Any] | None = None,
        *,
        priority: int = 100,
        max_attempts: int = 3,
        run_after: datetime | None = None,
    ) -> JobQueue:
        db = self.session_factory()
        try:
            job_type_value = _value(job_type)
            existing = (
                db.query(JobQueue)
                .filter(
                    JobQueue.job_type == job_type_value,
                    JobQueue.dedupe_key == dedupe_key,
                    JobQueue.status.in_([JobStatus.PENDING.value, JobStatus.RUNNING.value]),
                )
                .order_by(JobQueue.id.desc())
                .first()
            )
            if existing is not None:
                return existing

            job = JobQueue(
                job_type=job_type_value,
                dedupe_key=dedupe_key,
                status=JobStatus.PENDING.value,
                priority=priority,
                payload_json=json.dumps(payload or {}, ensure_ascii=False),
                max_attempts=max_attempts,
                run_after=run_after or _utcnow(),
            )
            db.add(job)
            db.commit()
            db.refresh(job)
            return job
        finally:
            db.close()

    def claim(self, job_types: list[str | JobType], worker_id: str, limit: int) -> list[JobQueue]:
        if limit <= 0:
            return []

        db = self.session_factory()
        try:
            now = _utcnow()
            stale_before = now - timedelta(minutes=15)
            type_values = [_value(job_type) for job_type in job_types]
            statement = (
                select(JobQueue)
                .where(
                    JobQueue.job_type.in_(type_values),
                    JobQueue.run_after <= now,
                    JobQueue.attempts < JobQueue.max_attempts,
                    or_(
                        JobQueue.status.in_([JobStatus.PENDING.value, JobStatus.FAILED.value]),
                        (JobQueue.status == JobStatus.RUNNING.value) & (JobQueue.locked_at < stale_before),
                    ),
                )
                .order_by(JobQueue.priority.asc(), JobQueue.created_at.asc(), JobQueue.id.asc())
                .limit(limit)
            )
            jobs = list(db.scalars(statement))
            for job in jobs:
                job.status = JobStatus.RUNNING.value
                job.locked_by = worker_id
                job.locked_at = now
                job.updated_at = now
                db.add(job)
            db.commit()
            for job in jobs:
                db.refresh(job)
            return jobs
        except OperationalError:
            db.rollback()
            return []
        finally:
            db.close()

    def mark_succeeded(self, job_id: int, result: dict[str, Any] | None = None) -> None:
        db = self.session_factory()
        try:
            job = db.get(JobQueue, job_id)
            if job is None:
                return
            now = _utcnow()
            job.status = JobStatus.SUCCEEDED.value
            job.result_json = json.dumps(result or {}, ensure_ascii=False)
            job.last_error = ""
            job.locked_by = ""
            job.locked_at = None
            job.finished_at = now
            job.updated_at = now
            db.add(job)
            db.commit()
        finally:
            db.close()

    def mark_failed(self, job_id: int, error: str, *, retry_delay_seconds: int = 60) -> None:
        db = self.session_factory()
        try:
            job = db.get(JobQueue, job_id)
            if job is None:
                return
            now = _utcnow()
            job.attempts += 1
            job.status = JobStatus.DEAD.value if job.attempts >= job.max_attempts else JobStatus.FAILED.value
            job.last_error = error[:2000]
            job.locked_by = ""
            job.locked_at = None
            job.run_after = now + timedelta(seconds=retry_delay_seconds)
            job.updated_at = now
            if job.status == JobStatus.DEAD.value:
                job.finished_at = now
            db.add(job)
            db.commit()
        finally:
            db.close()

    def get(self, job_id: int) -> JobQueue | None:
        db = self.session_factory()
        try:
            job = db.get(JobQueue, job_id)
            if job is None:
                return None
            db.expunge(job)
            return job
        finally:
            db.close()

    def list_recent(self, limit: int = 50) -> list[JobQueue]:
        db = self.session_factory()
        try:
            jobs = list(
                db.scalars(
                    select(JobQueue)
                    .order_by(JobQueue.created_at.desc(), JobQueue.id.desc())
                    .limit(max(limit, 1))
                )
            )
            for job in jobs:
                db.expunge(job)
            return jobs
        finally:
            db.close()

    def summary(self) -> dict[str, int]:
        db = self.session_factory()
        try:
            rows = (
                db.query(JobQueue.status, func.count(JobQueue.id))
                .group_by(JobQueue.status)
                .all()
            )
            summary = {status.value: 0 for status in JobStatus}
            for status, count in rows:
                summary[str(status)] = int(count or 0)
            return summary
        finally:
            db.close()

    def count(self, *, job_type: str | JobType | None = None, statuses: list[str | JobStatus] | None = None) -> int:
        db = self.session_factory()
        try:
            query = db.query(func.count(JobQueue.id))
            if job_type is not None:
                query = query.filter(JobQueue.job_type == _value(job_type))
            if statuses:
                query = query.filter(JobQueue.status.in_([_value(status) for status in statuses]))
            return int(query.scalar() or 0)
        finally:
            db.close()


def job_payload(job: JobQueue) -> dict[str, Any]:
    try:
        return json.loads(job.payload_json or "{}")
    except json.JSONDecodeError:
        return {}
