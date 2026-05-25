from __future__ import annotations

import argparse
import asyncio
from collections import Counter
from datetime import datetime, timedelta, timezone

from app.application.services.ingestion_service import IngestionService
from app.application.services.job_queue_service import JobQueueService, job_payload
from app.core.config import Settings
from app.db.models import Post, Source, SyncJob
from app.db.session import build_session_factory
from app.domain.enums import ContentStatus, JobType, LlmStatus, SyncStatus, SyncTriggerType
from app.infrastructure.connectors.werss import WerssConnector


class RefreshWorker:
    def __init__(self, session_factory, queue: JobQueueService, connector, settings: Settings, *, worker_id: str = "refresh-worker"):
        self.session_factory = session_factory
        self.queue = queue
        self.connector = connector
        self.settings = settings
        self.worker_id = worker_id

    async def run_once(self, limit: int = 1) -> dict:
        jobs = self.queue.claim([JobType.REFRESH_SOURCE, JobType.SYNC_SOURCE_POSTS], self.worker_id, limit)
        completed = 0
        failed = 0
        for job in jobs:
            try:
                payload = job_payload(job)
                if job.job_type == JobType.REFRESH_SOURCE.value:
                    result = await self._refresh_source(payload)
                else:
                    result = await self._sync_posts(payload)
                self.queue.mark_succeeded(job.id, result)
                completed += 1
            except Exception as exc:  # noqa: BLE001
                self.queue.mark_failed(job.id, str(exc), retry_delay_seconds=300)
                failed += 1
        return {"status": "completed", "claimed": len(jobs), "completed": completed, "failed": failed}

    async def _refresh_source(self, payload: dict) -> dict:
        source_id = str(payload["source_id"])
        await self.connector.refresh_source(
            source_id,
            int(payload.get("start_page", self.settings.upstream_refresh_start_page)),
            int(payload.get("end_page", self.settings.upstream_refresh_end_page)),
        )
        self.queue.enqueue(
            JobType.SYNC_SOURCE_POSTS,
            f"source:{source_id}:limit:{self.settings.post_fetch_limit}",
            {"source_id": source_id, "limit": self.settings.post_fetch_limit},
            priority=40,
            run_after=datetime.now(timezone.utc) + timedelta(seconds=max(self.settings.upstream_refresh_settle_seconds, 0)),
        )
        return {"source_id": source_id}

    async def _sync_posts(self, payload: dict) -> dict:
        source_upstream_id = str(payload.get("source_id") or "").strip()
        if not source_upstream_id:
            raise ValueError("sync_source_posts requires source_id")

        db = self.session_factory()
        job = SyncJob(trigger_type=SyncTriggerType.SCHEDULE.value, status=SyncStatus.RUNNING.value, started_at=datetime.now(timezone.utc))
        db.add(job)
        db.commit()
        db.refresh(job)
        try:
            source = db.query(Source).filter(Source.upstream_source_id == source_upstream_id).first()
            if source is None:
                raise ValueError("source not found")
            service = IngestionService(self.session_factory, self.connector, self.settings)
            discard_counter: Counter[str] = Counter()
            await service._sync_source(db, job, source, discard_counter)  # noqa: SLF001
            job.sources_synced = 1
            job.posts_discarded = sum(discard_counter.values())
            job.status = SyncStatus.COMPLETED.value
            job.finished_at = datetime.now(timezone.utc)
            db.add(job)
            db.commit()
            sync_job_id = job.id
            sync_status = job.status
        except Exception:
            db.rollback()
            job.status = SyncStatus.FAILED.value
            job.finished_at = datetime.now(timezone.utc)
            db.add(job)
            db.commit()
            raise
        finally:
            db.close()

        content_jobs = self._enqueue_missing_content(source_upstream_id)
        llm_jobs = self._enqueue_llm_jobs()
        return {"sync_job_id": sync_job_id, "status": sync_status, "content_jobs": content_jobs, "llm_jobs": llm_jobs}

    def _enqueue_llm_jobs(self) -> int:
        db = self.session_factory()
        try:
            posts = (
                db.query(Post)
                .filter(
                    Post.content_status == ContentStatus.READY.value,
                    Post.llm_status.in_([LlmStatus.PENDING.value, LlmStatus.FAILED.value, LlmStatus.NOT_REQUESTED.value]),
                )
                .order_by(Post.id.asc())
                .limit(500)
                .all()
            )
            count = 0
            for post in posts:
                if not (post.content_text_snapshot or post.content_html):
                    continue
                self.queue.enqueue(
                    JobType.LLM_POST,
                    f"post:{post.id}:hash:{post.content_hash}",
                    {"post_id": post.id, "content_hash": post.content_hash},
                    priority=120,
                )
                count += 1
            return count
        finally:
            db.close()

    async def _sync_posts_legacy(self) -> dict:
        service = IngestionService(self.session_factory, self.connector, self.settings)
        job = await service.run_sync(SyncTriggerType.SCHEDULE)
        return {"sync_job_id": job.id, "status": job.status}

    def _enqueue_missing_content(self, source_upstream_id: str | None = None) -> int:
        db = self.session_factory()
        try:
            query = db.query(Post).filter(Post.content_status == ContentStatus.MISSING.value)
            if source_upstream_id:
                query = query.join(Source).filter(Source.upstream_source_id == source_upstream_id)
            posts = query.order_by(Post.id.asc()).limit(500).all()
            count = 0
            for post in posts:
                self.queue.enqueue(
                    JobType.FETCH_CONTENT,
                    f"upstream:{post.upstream_post_id}",
                    {"upstream_post_id": post.upstream_post_id, "post_id": post.id},
                    priority=90,
                )
                count += 1
            return count
        finally:
            db.close()


async def _amain() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--once", action="store_true", help="process one bounded batch and exit")
    parser.add_argument("--limit", type=int, default=1)
    args = parser.parse_args()
    settings = Settings.from_env()
    _, session_factory = build_session_factory(settings)
    queue = JobQueueService(session_factory)
    connector = WerssConnector(settings)
    worker = RefreshWorker(session_factory, queue, connector, settings)
    result = await worker.run_once(limit=args.limit)
    print(result, flush=True)


if __name__ == "__main__":
    asyncio.run(_amain())
