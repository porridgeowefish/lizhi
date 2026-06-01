from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy.exc import OperationalError
from sqlalchemy import and_, or_, select
from sqlalchemy.orm import Session, sessionmaker

from app.application.classification import (
    VALID_CATEGORIES,
    TimeSignals,
    canonical_category,
    derive_time_status,
    html_to_text,
    parse_iso_datetime,
)
from app.application.services.llm_service import LlmService
from app.db.models import LlmTask, Post, PostCategory, PostProjection
from app.domain.enums import LlmStatus, SyncStatus

_logger = logging.getLogger(__name__)


class LlmQueueService:
    def __init__(self, session_factory: sessionmaker[Session], settings):
        self.session_factory = session_factory
        self.settings = settings
        self.llm_service = LlmService(settings)
        self._lock = asyncio.Lock()

    def enqueue_missing_tasks(self) -> dict:
        db = self.session_factory()
        try:
            statement = (
                select(Post)
                .outerjoin(PostProjection, PostProjection.post_id == Post.id)
                .where(Post.llm_status != LlmStatus.COMPLETED.value)
                .where(self._queue_eligible_clause())
                .order_by(Post.id.desc())
            )
            created = 0
            existing = 0
            for post in db.scalars(statement):
                if not (post.content_text_snapshot or post.content_html):
                    continue
                task = db.query(LlmTask).filter(LlmTask.post_id == post.id).first()
                if task is None:
                    db.add(LlmTask(post_id=post.id, status=SyncStatus.PENDING.value))
                    created += 1
                elif task.status != SyncStatus.COMPLETED.value:
                    existing += 1
            db.commit()
            return {"created": created, "existing": existing}
        finally:
            db.close()

    async def process_batch(self) -> dict:
        if not (self.settings.llm_queue_enabled and self.llm_service.enabled):
            return {"status": "skipped", "reason": "llm queue disabled or llm unavailable"}

        async with self._lock:
            task_ids = self._claim_tasks()
            processed = 0
            completed = 0
            failed = 0
            for task_id in task_ids:
                ok = await self._process_task(task_id)
                processed += 1
                if ok:
                    completed += 1
                else:
                    failed += 1
            return {
                "status": "completed",
                "claimed": len(task_ids),
                "processed": processed,
                "completed": completed,
                "failed": failed,
            }

    def _claim_tasks(self) -> list[int]:
        db = self.session_factory()
        try:
            statement = (
                select(LlmTask)
                .join(Post, Post.id == LlmTask.post_id)
                .outerjoin(PostProjection, PostProjection.post_id == Post.id)
                .where(
                    or_(
                        LlmTask.status.in_([SyncStatus.PENDING.value, SyncStatus.FAILED.value]),
                        and_(
                            LlmTask.status == SyncStatus.RUNNING.value,
                            LlmTask.locked_at < datetime.now(timezone.utc) - timedelta(minutes=15),
                        ),
                    ),
                    LlmTask.attempts < self.settings.llm_worker_max_attempts,
                    self._queue_eligible_clause(),
                )
                .order_by(LlmTask.updated_at.asc(), LlmTask.id.asc())
                .limit(self.settings.llm_worker_batch_size)
            )
            tasks = list(db.scalars(statement))
            now = datetime.now(timezone.utc)
            for task in tasks:
                task.status = SyncStatus.RUNNING.value
                task.locked_at = now
                db.add(task)
            db.commit()
            return [task.id for task in tasks]
        except OperationalError as exc:
            db.rollback()
            _logger.warning("llm queue claim skipped because database is busy: %s", exc)
            return []
        finally:
            db.close()

    def _queue_eligible_clause(self):
        now = datetime.now(timezone.utc)
        recent_cutoff = now - timedelta(days=max(self.settings.queue_recent_days, 0))
        return or_(
            Post.published_at >= recent_cutoff,
            PostProjection.deadline_at >= now,
            PostProjection.event_start_at >= now,
        )

    async def _process_task(self, task_id: int) -> bool:
        payload = self._load_task_payload(task_id)
        if payload is None:
            return False
        if payload.get("status") == "completed":
            return True

        try:
            result = await self.llm_service.summarize_and_extract(
                title=payload["title"],
                summary=payload["summary"],
                content_text=payload["content_text"],
            )
            if result["status"] != LlmStatus.COMPLETED.value:
                raise RuntimeError(result["status"])

            return self._complete_task(task_id, result)
        except Exception as exc:  # noqa: BLE001
            self._mark_failed(task_id, str(exc))
            _logger.warning("llm queue task failed for task %s: %s", task_id, exc)
            return False

    def _load_task_payload(self, task_id: int) -> dict | None:
        db = self.session_factory()
        try:
            task = db.get(LlmTask, task_id)
            if task is None:
                return None
            post = db.get(Post, task.post_id)
            if post is None:
                task.status = SyncStatus.FAILED.value
                task.last_error = "post not found"
                task.finished_at = datetime.now(timezone.utc)
                db.add(task)
                db.commit()
                return None

            content_text = post.content_text_snapshot or ""
            if not content_text and post.content_html:
                content_text = html_to_text(post.content_html)
            if not content_text:
                post.llm_status = LlmStatus.NOT_REQUESTED.value
                task.status = SyncStatus.COMPLETED.value
                task.finished_at = datetime.now(timezone.utc)
                db.add(post)
                db.add(task)
                db.commit()
                return {"status": "completed"}

            return {
                "title": post.title,
                "summary": post.summary,
                "content_text": content_text,
            }
        except OperationalError as exc:
            db.rollback()
            _logger.warning("llm queue task load skipped because database is busy: %s", exc)
            return None
        finally:
            db.close()

    def _complete_task(self, task_id: int, result: dict) -> bool:
        db = self.session_factory()
        try:
            task = db.get(LlmTask, task_id)
            if task is None:
                return False
            post = db.get(Post, task.post_id)
            if post is None:
                task.status = SyncStatus.FAILED.value
                task.last_error = "post not found"
                task.finished_at = datetime.now(timezone.utc)
                db.add(task)
                db.commit()
                return False

            self._apply_llm_result(db, post, result)
            task.status = SyncStatus.COMPLETED.value
            task.last_error = ""
            task.finished_at = datetime.now(timezone.utc)
            db.add(task)
            db.commit()
            return True
        except OperationalError as exc:
            db.rollback()
            _logger.warning("llm queue task completion skipped because database is busy: %s", exc)
            return False
        finally:
            db.close()

    def _mark_failed(self, task_id: int, error: str) -> None:
        db = self.session_factory()
        try:
            task = db.get(LlmTask, task_id)
            if task is None:
                return
            task.attempts += 1
            task.status = (
                SyncStatus.FAILED.value
                if task.attempts >= self.settings.llm_worker_max_attempts
                else SyncStatus.PENDING.value
            )
            task.last_error = error[:2000]
            task.locked_at = None
            if task.status == SyncStatus.FAILED.value:
                task.finished_at = datetime.now(timezone.utc)
            db.add(task)
            db.commit()
        except OperationalError as exc:
            db.rollback()
            _logger.warning("llm queue failure mark skipped because database is busy: %s", exc)
        finally:
            db.close()

    def _apply_llm_result(self, db: Session, post: Post, result: dict) -> None:
        structured = result.get("structured") or {}
        post.llm_summary = result.get("summary") or ""
        post.llm_structured_json = json.dumps(structured, ensure_ascii=False) if structured else ""
        post.llm_model = result.get("model") or ""
        post.llm_prompt_version = self.settings.llm_prompt_version
        post.llm_status = LlmStatus.COMPLETED.value
        post.llm_processed_at = result.get("processed_at")
        db.add(post)

        llm_category = structured.get("category", "")
        if llm_category in VALID_CATEGORIES:
            llm_category = canonical_category(llm_category)
            db.query(PostCategory).filter(PostCategory.post_id == post.id).delete()
            db.flush()
            db.add(PostCategory(post_id=post.id, category_code=llm_category, category_source="llm"))

        projection = db.query(PostProjection).filter(PostProjection.post_id == post.id).first()
        if projection is None:
            return

        if llm_category in VALID_CATEGORIES:
            projection.primary_category = llm_category

        llm_start = parse_iso_datetime(structured.get("start_iso"), post.published_at)
        llm_end = parse_iso_datetime(structured.get("end_iso"), post.published_at)
        llm_deadline = parse_iso_datetime(structured.get("deadline_iso"), post.published_at)
        if llm_start:
            projection.event_start_at = llm_start
        if llm_end:
            projection.event_end_at = llm_end
        if llm_deadline:
            projection.deadline_at = llm_deadline
        if llm_start or llm_end or llm_deadline:
            time_signals = TimeSignals(
                event_start_at=projection.event_start_at,
                event_end_at=projection.event_end_at,
                deadline_at=projection.deadline_at,
            )
            time_status, timeliness_level = derive_time_status(time_signals)
            projection.time_status = time_status.value
            projection.timeliness_level = timeliness_level.value
        db.add(projection)
