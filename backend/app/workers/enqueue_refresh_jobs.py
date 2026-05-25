from __future__ import annotations

import argparse

from app.application.services.job_queue_service import JobQueueService
from app.core.config import Settings
from app.db.models import Source
from app.db.session import build_session_factory
from app.domain.enums import JobStatus, JobType, SourceStatus


def enqueue_refresh_jobs(settings: Settings, limit: int | None = None) -> dict[str, int | str]:
    _, session_factory = build_session_factory(settings)
    queue = JobQueueService(session_factory)
    db = session_factory()
    try:
        active_source_count = db.query(Source).filter(Source.status == SourceStatus.ENABLED.value).count()
        pending_refresh_jobs = queue.count(
            job_type=JobType.REFRESH_SOURCE,
            statuses=[JobStatus.PENDING, JobStatus.RUNNING, JobStatus.FAILED],
        )
        if pending_refresh_jobs:
            return {"status": "skipped", "reason": "refresh backlog active", "sources": active_source_count, "jobs": 0}

        query = db.query(Source).filter(Source.status == SourceStatus.ENABLED.value).order_by(Source.id.asc())
        if limit:
            query = query.limit(limit)
        sources = query.all()
        created = 0
        for source in sources:
            queue.enqueue(
                JobType.REFRESH_SOURCE,
                f"source:{source.upstream_source_id}:pages:{settings.upstream_refresh_start_page}-{settings.upstream_refresh_end_page}",
                {
                    "source_id": source.upstream_source_id,
                    "start_page": settings.upstream_refresh_start_page,
                    "end_page": settings.upstream_refresh_end_page,
                },
                priority=50,
            )
            created += 1
        return {"status": "completed", "sources": len(sources), "jobs": created}
    finally:
        db.close()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--once", action="store_true", help="enqueue one bounded refresh batch and exit")
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()
    print(enqueue_refresh_jobs(Settings.from_env(), limit=args.limit), flush=True)


if __name__ == "__main__":
    main()
