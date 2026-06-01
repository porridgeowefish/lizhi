from __future__ import annotations

import argparse
import asyncio
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import or_
from sqlalchemy.orm import Session, sessionmaker

from app.application.classification import compute_content_hash, normalize_whitespace
from app.application.services.ingestion_service import extract_post_content
from app.application.services.job_queue_service import JobQueueService, job_payload
from app.application.services.ocr_service import OcrService
from app.core.config import Settings
from app.db.models import Post, PostProjection
from app.db.session import build_session_factory
from app.domain.enums import ContentStatus, JobType, LlmStatus
from app.infrastructure.connectors.werss import WerssConnector


LLM_PROCESS_PUBLISHED_AFTER = datetime(2022, 1, 1)


class ContentWorker:
    def __init__(
        self,
        session_factory: sessionmaker[Session],
        queue: JobQueueService,
        connector,
        settings: Settings,
        *,
        worker_id: str = "content-worker",
        ocr_service: OcrService | None = None,
    ):
        self.session_factory = session_factory
        self.queue = queue
        self.connector = connector
        self.settings = settings
        self.worker_id = worker_id
        self.ocr_service = ocr_service or OcrService(settings, session_factory=session_factory)

    async def run_once(self, limit: int | None = None) -> dict[str, int | str]:
        jobs = self.queue.claim([JobType.FETCH_CONTENT], self.worker_id, limit or self.settings.content_worker_batch_size)
        completed = 0
        failed = 0
        for job in jobs:
            try:
                result = await self._process_job(job.id, job_payload(job))
                self.queue.mark_succeeded(job.id, result)
                completed += 1
            except Exception as exc:  # noqa: BLE001
                self.queue.mark_failed(job.id, str(exc))
                failed += 1
        return {"status": "completed", "claimed": len(jobs), "completed": completed, "failed": failed}

    async def _process_job(self, job_id: int, payload: dict[str, Any]) -> dict[str, Any]:
        upstream_post_id = str(payload.get("upstream_post_id") or "").strip()
        post_id = payload.get("post_id")
        if not upstream_post_id and not post_id:
            raise ValueError("fetch_content job requires upstream_post_id or post_id")

        db = self.session_factory()
        try:
            post = db.get(Post, int(post_id)) if post_id else None
            if post is None and upstream_post_id:
                post = db.query(Post).filter(Post.upstream_post_id == upstream_post_id).first()
            if post is None:
                raise ValueError("post not found")
            if not self._is_queue_eligible(db, post):
                return {"post_id": post.id, "source_job_id": job_id, "skipped": "not_queue_eligible"}
            post_id_value = post.id
            upstream_post_id = post.upstream_post_id
        finally:
            db.close()

        detail = await self._fetch_detail(upstream_post_id or str(post_id))
        if str(detail.get("content") or "").strip() == "DELETED":
            raise ValueError("post is deleted or unavailable upstream")
        content_html, content_text = extract_post_content(detail)
        ocr_result = self.ocr_service.maybe_append_ocr_text(
            detail,
            content_text,
            post_id=post_id_value,
            upstream_post_id=upstream_post_id,
        )
        content_text = ocr_result.content_text
        if not normalize_whitespace(content_text):
            raise ValueError("content fetch returned empty body")

        db = self.session_factory()
        try:
            post = db.get(Post, post_id_value)
            if post is None:
                raise ValueError("post not found")

            post.content_html = content_html
            post.content_text_snapshot = content_text[:8000]
            post.content_status = ContentStatus.READY.value
            post.content_hash = compute_content_hash(
                post.title,
                post.summary,
                post.original_url,
                content_text[:2000],
                post.content_hash,
            )
            should_enqueue_llm = (
                self.settings.llm_enabled
                and normalize_whitespace(content_text)
                and self._is_queue_eligible(db, post)
            )
            if should_enqueue_llm:
                post.llm_status = LlmStatus.PENDING.value
            db.add(post)
            db.commit()
            db.refresh(post)
            post_id_value = post.id
            content_hash = post.content_hash
            published_at = post.published_at
        finally:
            db.close()

        if published_at is not None and published_at.tzinfo is not None:
            published_at = published_at.replace(tzinfo=None)
        if published_at is not None and published_at < LLM_PROCESS_PUBLISHED_AFTER:
            return {"post_id": post_id_value, "content_chars": len(content_text), "source_job_id": job_id, "llm_skipped": "published_before_2022"}

        if should_enqueue_llm:
            self.queue.enqueue(
                JobType.LLM_POST,
                f"post:{post_id_value}:hash:{content_hash}",
                {"post_id": post_id_value, "content_hash": content_hash},
                priority=120,
            )
        return {"post_id": post_id_value, "content_chars": len(content_text), "source_job_id": job_id}

    def _is_queue_eligible(self, db: Session, post: Post) -> bool:
        now = datetime.now(timezone.utc)
        recent_cutoff = now - timedelta(days=max(self.settings.queue_recent_days, 0))
        query = (
            db.query(Post.id)
            .outerjoin(PostProjection, PostProjection.post_id == Post.id)
            .filter(
                Post.id == post.id,
                or_(
                    Post.published_at >= recent_cutoff,
                    PostProjection.deadline_at >= now,
                    PostProjection.event_start_at >= now,
                ),
            )
        )
        return query.first() is not None

    async def _fetch_detail(self, upstream_post_id: str) -> dict:
        refresh_post = getattr(self.connector, "refresh_post", None)
        if refresh_post is not None:
            refreshed = await refresh_post(upstream_post_id)
            if refreshed:
                return refreshed

        fetch_detail = getattr(self.connector, "fetch_post_detail", None)
        if fetch_detail is None:
            return {}
        return await fetch_detail(upstream_post_id) or {}


async def _amain() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--once", action="store_true", help="process one bounded batch and exit")
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()
    settings = Settings.from_env()
    _, session_factory = build_session_factory(settings)
    queue = JobQueueService(session_factory)
    connector = WerssConnector(settings)
    worker = ContentWorker(session_factory, queue, connector, settings)
    result = await worker.run_once(limit=args.limit)
    print(result, flush=True)


if __name__ == "__main__":
    asyncio.run(_amain())
