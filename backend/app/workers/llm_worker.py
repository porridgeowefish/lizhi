from __future__ import annotations

import argparse
import asyncio
from datetime import datetime, timedelta, timezone

from sqlalchemy import or_
from app.application.services.job_queue_service import JobQueueService, job_payload
from app.application.services.llm_queue_service import LlmQueueService
from app.core.config import Settings
from app.db.models import LlmTask, Post, PostProjection
from app.db.session import build_session_factory
from app.domain.enums import JobType, LlmStatus, SyncStatus


LLM_PROCESS_PUBLISHED_AFTER = datetime(2022, 1, 1)


class LlmWorker:
    def __init__(self, session_factory, queue: JobQueueService, settings: Settings, *, worker_id: str = "llm-worker"):
        self.session_factory = session_factory
        self.queue = queue
        self.settings = settings
        self.worker_id = worker_id
        self.llm_queue = LlmQueueService(session_factory, settings)

    async def run_once(self, limit: int | None = None) -> dict:
        if not self.llm_queue.llm_service.enabled:
            return {"status": "skipped", "reason": "llm unavailable", "claimed": 0, "completed": 0, "failed": 0}

        jobs = self.queue.claim([JobType.LLM_POST], self.worker_id, limit or self.settings.llm_worker_batch_size)
        completed = 0
        failed = 0
        for job in jobs:
            payload = job_payload(job)
            try:
                if self._skip_old_post(int(payload["post_id"])):
                    self.queue.mark_succeeded(job.id, {"skipped": "published_before_2022"})
                    completed += 1
                    continue
                if not self._is_queue_eligible(int(payload["post_id"])):
                    self.queue.mark_succeeded(job.id, {"skipped": "not_queue_eligible"})
                    completed += 1
                    continue
                task_id = self._ensure_llm_task(int(payload["post_id"]))
                ok = await self.llm_queue._process_task(task_id)  # noqa: SLF001
                if not ok:
                    raise RuntimeError("llm task failed")
                self.queue.mark_succeeded(job.id, {"llm_task_id": task_id})
                completed += 1
            except Exception as exc:  # noqa: BLE001
                self.queue.mark_failed(job.id, str(exc))
                failed += 1
        return {"status": "completed", "claimed": len(jobs), "completed": completed, "failed": failed}

    def _ensure_llm_task(self, post_id: int) -> int:
        db = self.session_factory()
        try:
            post = db.get(Post, post_id)
            if post is None:
                raise ValueError("post not found")
            task = db.query(LlmTask).filter(LlmTask.post_id == post_id).first()
            if task is None:
                task = LlmTask(post_id=post_id)
            task.status = SyncStatus.PENDING.value
            task.locked_at = None
            db.add(task)
            db.commit()
            db.refresh(task)
            return task.id
        finally:
            db.close()

    def _skip_old_post(self, post_id: int) -> bool:
        db = self.session_factory()
        try:
            post = db.get(Post, post_id)
            if post is None:
                raise ValueError("post not found")
            published_at = post.published_at
            if published_at is not None and published_at.tzinfo is not None:
                published_at = published_at.replace(tzinfo=None)
            if published_at is None or published_at >= LLM_PROCESS_PUBLISHED_AFTER:
                return False
            post.llm_status = LlmStatus.NOT_REQUESTED.value
            db.add(post)
            db.commit()
            return True
        finally:
            db.close()

    def _is_queue_eligible(self, post_id: int) -> bool:
        db = self.session_factory()
        try:
            now = datetime.now(timezone.utc)
            recent_cutoff = now - timedelta(days=max(self.settings.queue_recent_days, 0))
            return (
                db.query(Post.id)
                .outerjoin(PostProjection, PostProjection.post_id == Post.id)
                .filter(
                    Post.id == post_id,
                    or_(
                        Post.published_at >= recent_cutoff,
                        PostProjection.deadline_at >= now,
                        PostProjection.event_start_at >= now,
                    ),
                )
                .first()
                is not None
            )
        finally:
            db.close()


async def _amain() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--once", action="store_true", help="process one bounded batch and exit")
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()
    settings = Settings.from_env()
    _, session_factory = build_session_factory(settings)
    queue = JobQueueService(session_factory)
    worker = LlmWorker(session_factory, queue, settings)
    result = await worker.run_once(limit=args.limit)
    print(result, flush=True)


if __name__ == "__main__":
    asyncio.run(_amain())
