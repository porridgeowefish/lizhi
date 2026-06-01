from __future__ import annotations

import asyncio
import html as html_lib
import json
import logging
from collections import Counter
from datetime import datetime, timezone

from sqlalchemy import func
from sqlalchemy.orm import Session, sessionmaker

from app.application.classification import (
    PRESCREEN_RULE_VERSION,
    TimeSignals,
    build_summary,
    classify_categories,
    classify_content_type,
    compute_content_hash,
    compute_ranking_score,
    compute_title_hash,
    canonical_category,
    derive_display_level,
    derive_participation_status,
    derive_time_status,
    extract_time_signals,
    html_to_text,
    normalize_category_list,
    normalize_whitespace,
    parse_iso_datetime,
    parse_llm_payload,
    prescreen_post,
    sanitize_html,
    VALID_CATEGORIES,
)
from app.application.services.ocr_service import OcrService
from app.db.models import DiscardedPost, LlmTask, Post, PostCategory, PostProjection, RawPayload, Source, SyncJob, SyncJobItem
from app.domain.enums import (
    ContentStatus,
    IngestionStatus,
    LlmStatus,
    SourceStatus,
    SyncStage,
    SyncStatus,
    SyncTriggerType,
)

_logger = logging.getLogger(__name__)


def extract_post_content(raw_post: dict) -> tuple[str, str]:
    for field in ("content_html", "content"):
        candidate = str(raw_post.get(field) or "")
        if not candidate:
            continue
        content_html = sanitize_html(candidate)
        content_text = html_to_text(content_html)
        if content_html or normalize_whitespace(content_text):
            return content_html, content_text

    content_text = normalize_whitespace(str(raw_post.get("content_text") or raw_post.get("text") or ""))
    if content_text:
        content_html = f"<p>{html_lib.escape(content_text)}</p>"
        return content_html, content_text
    return "", ""


def _parse_llm_datetimes(llm_json_str: str, published_at: datetime | None) -> tuple:
    structured = parse_llm_payload(llm_json_str)
    if not structured:
        return None, None, None
    return (
        parse_iso_datetime(structured.get("start_iso"), published_at),
        parse_iso_datetime(structured.get("end_iso"), published_at),
        parse_iso_datetime(structured.get("deadline_iso"), published_at),
    )


def _parse_publish_time(raw_post: dict) -> datetime | None:
    publish_time = raw_post.get("publish_time")
    if isinstance(publish_time, (int, float)):
        return datetime.fromtimestamp(publish_time, tz=timezone.utc)
    if isinstance(publish_time, datetime):
        return publish_time
    return None


def _as_naive(value: datetime | None) -> datetime | None:
    if value is not None and value.tzinfo is not None:
        return value.replace(tzinfo=None)
    return value


class IngestionService:
    def __init__(self, session_factory: sessionmaker[Session], connector, settings, *, ocr_service: OcrService | None = None):
        self.session_factory = session_factory
        self.connector = connector
        self.settings = settings
        self.ocr_service = ocr_service or OcrService(settings, session_factory=session_factory)
        self._lock = asyncio.Lock()

    async def run_sync(self, trigger_type: SyncTriggerType) -> SyncJob:
        async with self._lock:
            return await self._run_sync_locked(trigger_type)

    async def refresh_upstream_sources_then_sync(self) -> dict:
        refresh_source = getattr(self.connector, "refresh_source", None)
        if refresh_source is None:
            return {"status": "skipped", "reason": "connector does not support upstream refresh"}

        raw_sources = await self.connector.fetch_sources(limit=self.settings.source_fetch_limit)
        _logger.warning(
            "upstream refresh started: sources=%s start_page=%s end_page=%s",
            len(raw_sources),
            self.settings.upstream_refresh_start_page,
            self.settings.upstream_refresh_end_page,
        )
        refreshed = 0
        skipped = 0
        failures: list[str] = []

        for raw_source in raw_sources:
            source_id = str(raw_source.get("id") or raw_source.get("faker_id") or "").strip()
            source_name = str(raw_source.get("mp_name") or source_id)
            if not source_id:
                skipped += 1
                continue
            try:
                payload = await refresh_source(
                    source_id,
                    self.settings.upstream_refresh_start_page,
                    self.settings.upstream_refresh_end_page,
                )
                if payload.get("code") not in {0, None}:
                    failures.append(f"{source_name}: {payload.get('message') or payload.get('code')}")
                else:
                    refreshed += 1
            except Exception as exc:  # noqa: BLE001
                failures.append(f"{source_name}: {exc}")
                _logger.exception("upstream refresh failed for %s", source_id)

            delay = max(float(self.settings.upstream_refresh_request_delay_seconds), 0.0)
            if delay:
                await asyncio.sleep(delay)

        settle_seconds = max(int(self.settings.upstream_refresh_settle_seconds), 0)
        if settle_seconds:
            _logger.warning("upstream refresh settling before sync: seconds=%s", settle_seconds)
            await asyncio.sleep(settle_seconds)

        sync_job = await self.run_sync(SyncTriggerType.SCHEDULE)
        result = {
            "status": "completed" if not failures else "partial_failed",
            "sources_total": len(raw_sources),
            "sources_refreshed": refreshed,
            "sources_skipped": skipped,
            "failures": failures,
            "sync_job_id": sync_job.id,
            "sync_status": sync_job.status,
            "posts_fetched": sync_job.posts_fetched,
            "posts_inserted": sync_job.posts_inserted,
            "posts_updated": sync_job.posts_updated,
            "posts_discarded": sync_job.posts_discarded,
        }
        _logger.warning("upstream refresh finished: %s", result)
        return result

    async def _run_sync_locked(self, trigger_type: SyncTriggerType) -> SyncJob:
        db = self.session_factory()
        job = SyncJob(trigger_type=trigger_type.value, status=SyncStatus.PENDING.value)
        db.add(job)
        db.commit()
        db.refresh(job)

        job.status = SyncStatus.RUNNING.value
        job.started_at = datetime.now(timezone.utc)
        db.commit()

        source_failures: list[str] = []
        discard_counter: Counter[str] = Counter()

        try:
            source_stage = self._start_item(db, job.id, None, SyncStage.FETCH_SOURCES.value)
            raw_sources = await self.connector.fetch_sources(limit=self.settings.source_fetch_limit)
            source_stage.item_count = len(raw_sources)
            self._finish_item(db, source_stage, SyncStatus.COMPLETED.value)

            sources = [self._upsert_source(db, raw_source) for raw_source in raw_sources]
            db.commit()

            for source in sources:
                try:
                    await self._sync_source(db, job, source, discard_counter, backfill=False)
                    job.sources_synced += 1
                    source.post_count = db.query(func.count(Post.id)).filter(Post.source_id == source.id).scalar() or 0
                    source.last_synced_at = datetime.now(timezone.utc)
                    db.add(source)
                    db.commit()
                except Exception as exc:  # noqa: BLE001
                    db.rollback()
                    source_failures.append(f"{source.name}: {exc}")
                    _logger.exception("source sync failed for %s", source.upstream_source_id)

            if source_failures and job.sources_synced > 0:
                job.status = SyncStatus.PARTIAL_FAILED.value
                job.error_summary = "\n".join(source_failures)
            elif source_failures:
                job.status = SyncStatus.FAILED.value
                job.error_summary = "\n".join(source_failures)
            else:
                job.status = SyncStatus.COMPLETED.value
        except Exception as exc:  # noqa: BLE001
            db.rollback()
            job.status = SyncStatus.FAILED.value
            job.error_summary = str(exc)
        finally:
            job.posts_discarded = sum(discard_counter.values())
            job.discard_stats_json = json.dumps(dict(sorted(discard_counter.items())), ensure_ascii=False)
            job.finished_at = datetime.now(timezone.utc)
            db.add(job)
            db.commit()
            db.refresh(job)
            db.close()

        return job

    async def _sync_source(
        self,
        db: Session,
        job: SyncJob,
        source: Source,
        discard_counter: Counter[str],
        *,
        fetch_limit: int | None = None,
        backfill: bool = False,
    ) -> None:
        fetch_item = self._start_item(db, job.id, source.id, SyncStage.FETCH_POSTS.value)
        effective_limit = fetch_limit or (
            self.settings.post_fetch_limit if backfill else self.settings.incremental_post_fetch_limit
        )
        previous_seen_id = (source.last_seen_upstream_post_id or "").strip()
        raw_posts = await self.connector.fetch_posts(
            source_id=source.upstream_source_id,
            limit=effective_limit,
        )
        fetch_item.item_count = len(raw_posts)
        self._finish_item(db, fetch_item, SyncStatus.COMPLETED.value)
        job.posts_fetched += len(raw_posts)
        self._update_source_high_water(source, raw_posts)

        prescreen_item = self._start_item(db, job.id, source.id, SyncStage.PRESCREEN.value)
        store_item = self._start_item(db, job.id, source.id, SyncStage.STORE_RAW_PAYLOAD.value)
        detail_item = self._start_item(db, job.id, source.id, SyncStage.FETCH_DETAIL.value)
        normalize_item = self._start_item(db, job.id, source.id, SyncStage.NORMALIZE.value)
        llm_item = self._start_item(db, job.id, source.id, SyncStage.LLM_EXTRACT.value)
        project_item = self._start_item(db, job.id, source.id, SyncStage.PROJECT.value)
        persist_item = self._start_item(db, job.id, source.id, SyncStage.PERSIST.value)

        prescreened_count = 0
        stored_count = 0
        detail_count = 0
        normalized_count = 0
        llm_count = 0
        projected_count = 0
        for raw_post in raw_posts:
            upstream_post_id = str(raw_post.get("id") or "").strip()
            if not upstream_post_id:
                continue
            if not backfill and previous_seen_id and upstream_post_id == previous_seen_id:
                break
            existing_post = db.query(Post).filter(Post.upstream_post_id == upstream_post_id).first()
            if existing_post and existing_post.content_status == ContentStatus.MISSING.value:
                detail = await self._fetch_detail_if_needed(raw_post, upstream_post_id)
                if detail:
                    raw_post = {**raw_post, **detail}
                    detail_count += 1
            title = str(raw_post.get("title") or "")
            summary = str(raw_post.get("description") or "")
            source_name = source.name
            _, raw_content_text = extract_post_content(raw_post)
            body_excerpt = raw_content_text[:200]
            decision = prescreen_post(title=title, summary=summary, source_name=source_name, body_excerpt=body_excerpt)
            if decision.discard:
                if existing_post:
                    self._fill_existing_content_if_available(db, existing_post, raw_post)
                self._upsert_discarded_post(
                    db,
                    source=source,
                    upstream_post_id=upstream_post_id,
                    title=title,
                    decision=decision,
                )
                discard_counter[decision.reason] += 1
                prescreened_count += 1
                continue

            raw_payload, payload_hash = self._upsert_raw_payload(db, source=source, raw_post=raw_post)
            stored_count += 1 if raw_payload else 0

            detail = await self._fetch_detail_if_needed(raw_post, upstream_post_id)
            if detail:
                raw_post = {**raw_post, **detail}
                detail_count += 1

            content_html, content_text = extract_post_content(raw_post)
            content_text = self._append_ocr_text_if_needed(raw_post, content_text, existing_post)
            secondary_decision = prescreen_post(
                title=title,
                summary=summary,
                source_name=source_name,
                body_excerpt=content_text[:400],
            )
            if secondary_decision.discard:
                if existing_post:
                    self._fill_existing_content_if_available(db, existing_post, raw_post)
                self._upsert_discarded_post(
                    db,
                    source=source,
                    upstream_post_id=upstream_post_id,
                    title=title,
                    decision=secondary_decision,
                )
                discard_counter[secondary_decision.reason] += 1
                continue

            content_hash = compute_content_hash(
                title,
                summary,
                raw_post.get("url", ""),
                content_text[:2000],
                payload_hash,
            )
            post = existing_post or db.query(Post).filter(Post.upstream_post_id == upstream_post_id).first()
            existing_hash = post.content_hash if post else ""
            changed = content_hash != existing_hash
            llm_result = self._base_llm_result()
            should_enqueue_llm = changed and self.settings.llm_enabled and normalize_whitespace(content_text)
            if post and not changed:
                llm_result = {
                    "summary": post.llm_summary,
                    "structured": json.loads(post.llm_structured_json) if post.llm_structured_json else {},
                    "status": post.llm_status or LlmStatus.NOT_REQUESTED.value,
                    "model": post.llm_model,
                    "processed_at": post.llm_processed_at,
                }
                should_enqueue_llm = (
                    post.llm_status != LlmStatus.COMPLETED.value
                    and self.settings.llm_enabled
                    and normalize_whitespace(content_text)
                )
            elif should_enqueue_llm:
                llm_result["status"] = LlmStatus.PENDING.value
            if should_enqueue_llm and llm_result["status"] != LlmStatus.COMPLETED.value:
                llm_result["status"] = LlmStatus.PENDING.value
                llm_count += 1

            post, created = self._upsert_post(
                db,
                source=source,
                raw_post=raw_post,
                content_html=content_html,
                content_text=content_text,
                content_hash=content_hash,
                llm_result=llm_result,
                changed=changed,
            )
            if should_enqueue_llm:
                self._enqueue_llm_task(db, post)
            normalized_count += 1
            job.posts_inserted += 1 if created else 0
            job.posts_updated += 0 if created else 1

            self._upsert_projection(db, post)
            projected_count += 1

        db.commit()
        prescreen_item.item_count = prescreened_count
        store_item.item_count = stored_count
        detail_item.item_count = detail_count
        normalize_item.item_count = normalized_count
        llm_item.item_count = llm_count
        project_item.item_count = projected_count
        persist_item.item_count = normalized_count
        self._finish_item(db, prescreen_item, SyncStatus.COMPLETED.value)
        self._finish_item(db, store_item, SyncStatus.COMPLETED.value)
        self._finish_item(db, detail_item, SyncStatus.COMPLETED.value)
        self._finish_item(db, normalize_item, SyncStatus.COMPLETED.value)
        self._finish_item(db, llm_item, SyncStatus.COMPLETED.value)
        self._finish_item(db, project_item, SyncStatus.COMPLETED.value)
        self._finish_item(db, persist_item, SyncStatus.COMPLETED.value)

    def _base_llm_result(self) -> dict:
        return {
            "summary": "",
            "structured": {},
            "status": LlmStatus.NOT_REQUESTED.value,
            "model": "",
            "processed_at": None,
        }

    def _enqueue_llm_task(self, db: Session, post: Post) -> None:
        task = db.query(LlmTask).filter(LlmTask.post_id == post.id).first()
        if task is None:
            task = LlmTask(post_id=post.id)
        task.status = SyncStatus.PENDING.value
        task.attempts = 0
        task.last_error = ""
        task.locked_at = None
        task.finished_at = None
        db.add(task)
        db.flush()

    def _fill_existing_content_if_available(self, db: Session, post: Post, raw_post: dict) -> bool:
        content_html, content_text = extract_post_content(raw_post)
        content_text = self._append_ocr_text_if_needed(raw_post, content_text, post)
        if not (content_html or normalize_whitespace(content_text)):
            return False

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
        post.ingestion_status = IngestionStatus.UPDATED.value
        if self.settings.llm_enabled and normalize_whitespace(content_text):
            post.llm_status = LlmStatus.PENDING.value
            self._enqueue_llm_task(db, post)
        db.add(post)
        db.flush()
        return True

    def _append_ocr_text_if_needed(self, raw_post: dict, content_text: str, post: Post | None = None) -> str:
        result = self.ocr_service.maybe_append_ocr_text(
            raw_post,
            content_text,
            post_id=post.id if post else None,
            upstream_post_id=(post.upstream_post_id if post else str(raw_post.get("id") or "")),
        )
        if result.ocr_text:
            _logger.warning(
                "OCR text appended for upstream post %s: images=%s processed=%s chars=%s",
                raw_post.get("id") or "",
                result.image_count,
                result.processed_count,
                len(result.ocr_text),
            )
        return result.content_text

    async def _fetch_detail_if_needed(self, raw_post: dict, upstream_post_id: str) -> dict:
        if raw_post.get("content_html") or raw_post.get("content") or raw_post.get("content_text"):
            return {}
        fetch_detail = getattr(self.connector, "fetch_post_detail", None)
        if fetch_detail is None:
            return {}
        try:
            detail = await fetch_detail(upstream_post_id)
        except Exception as exc:  # noqa: BLE001
            _logger.warning("detail fetch failed for %s: %s", upstream_post_id, exc)
            return {}
        return detail or {}

    def _start_item(self, db: Session, sync_job_id: int, source_id: int | None, stage: str) -> SyncJobItem:
        item = SyncJobItem(sync_job_id=sync_job_id, source_id=source_id, stage=stage, status=SyncStatus.RUNNING.value)
        db.add(item)
        db.commit()
        db.refresh(item)
        return item

    def _finish_item(self, db: Session, item: SyncJobItem, status: str) -> None:
        item.status = status
        item.finished_at = datetime.now(timezone.utc)
        db.add(item)
        db.commit()

    def _upsert_source(self, db: Session, raw_source: dict) -> Source:
        upstream_source_id = str(raw_source.get("id") or raw_source.get("faker_id") or "").strip()
        if not upstream_source_id:
            raise ValueError("source is missing upstream id")

        source = db.query(Source).filter(Source.upstream_source_id == upstream_source_id).first()
        if source is None:
            source = Source(
                upstream_source_id=upstream_source_id,
                name=raw_source.get("mp_name", ""),
                source_type="wechat_official_account",
                status=SourceStatus.ENABLED.value,
                cover_url=raw_source.get("mp_cover", ""),
                intro=raw_source.get("mp_intro", ""),
            )
            db.add(source)
            db.flush()
            return source

        source.name = raw_source.get("mp_name", source.name)
        source.cover_url = raw_source.get("mp_cover", source.cover_url)
        source.intro = raw_source.get("mp_intro", source.intro)
        source.status = SourceStatus.ENABLED.value
        db.add(source)
        db.flush()
        return source

    def _upsert_raw_payload(self, db: Session, *, source: Source, raw_post: dict) -> tuple[RawPayload, str]:
        upstream_post_id = str(raw_post.get("id") or "").strip()
        payload_json = json.dumps(raw_post, ensure_ascii=False, sort_keys=True)
        payload_hash = compute_content_hash(payload_json)
        payload = (
            db.query(RawPayload)
            .filter(RawPayload.source_id == source.id, RawPayload.upstream_post_id == upstream_post_id)
            .first()
        )
        if payload is None:
            payload = RawPayload(
                source_id=source.id,
                upstream_post_id=upstream_post_id,
                payload_json=payload_json,
                payload_hash=payload_hash,
            )
            db.add(payload)
            db.flush()
        else:
            payload.payload_json = payload_json
            payload.payload_hash = payload_hash
            payload.fetched_at = datetime.now(timezone.utc)
            db.add(payload)
            db.flush()
        return payload, payload_hash

    def _upsert_discarded_post(
        self,
        db: Session,
        *,
        source: Source,
        upstream_post_id: str,
        title: str,
        decision,
    ) -> None:
        discarded = db.query(DiscardedPost).filter(DiscardedPost.upstream_post_id == upstream_post_id).first()
        if discarded is None:
            discarded = DiscardedPost(
                upstream_post_id=upstream_post_id,
                source_id=source.id,
                title_hash=compute_title_hash(title),
            )
        discarded.source_id = source.id
        discarded.discard_reason = decision.reason
        discarded.discard_stage = SyncStage.PRESCREEN.value
        discarded.matched_rule_version = PRESCREEN_RULE_VERSION
        discarded.matched_fields = json.dumps(decision.matched_fields or [], ensure_ascii=False)
        discarded.matched_keywords = json.dumps(decision.matched_keywords or [], ensure_ascii=False)
        discarded.quality_signals = json.dumps(decision.quality_signals or {}, ensure_ascii=False)
        discarded.discarded_at = datetime.now(timezone.utc)
        db.add(discarded)
        db.flush()

    def _upsert_post(
        self,
        db: Session,
        *,
        source: Source,
        raw_post: dict,
        content_html: str,
        content_text: str,
        content_hash: str,
        llm_result: dict,
        changed: bool,
    ) -> tuple[Post, bool]:
        upstream_post_id = str(raw_post.get("id") or "").strip()
        publish_time = _parse_publish_time(raw_post)

        post = db.query(Post).filter(Post.upstream_post_id == upstream_post_id).first()
        created = post is None
        if post is None:
            post = Post(
                upstream_post_id=upstream_post_id,
                source_id=source.id,
                source_name_snapshot=source.name,
                title=str(raw_post.get("title") or ""),
                original_url=str(raw_post.get("url") or ""),
                cover_url=str(raw_post.get("pic_url") or ""),
                published_at=publish_time,
                ingestion_status=IngestionStatus.NEW.value,
                content_hash=content_hash,
            )
            db.add(post)
            db.flush()

        post.source_id = source.id
        post.source_name_snapshot = source.name
        post.title = str(raw_post.get("title") or "")
        post.original_url = str(raw_post.get("url") or "")
        post.cover_url = str(raw_post.get("pic_url") or "")
        post.published_at = publish_time
        post.content_html = content_html
        post.content_text_snapshot = content_text[:8000]
        post.content_status = (
            ContentStatus.READY.value
            if content_html or normalize_whitespace(content_text)
            else ContentStatus.MISSING.value
        )
        post.content_hash = content_hash
        post.ingestion_status = IngestionStatus.NEW.value if created else (IngestionStatus.UPDATED.value if changed else IngestionStatus.UNCHANGED.value)
        post.llm_status = llm_result["status"]
        post.llm_model = llm_result["model"] or ""
        post.llm_prompt_version = self.settings.llm_prompt_version if llm_result["status"] != LlmStatus.NOT_REQUESTED.value else ""
        post.llm_processed_at = llm_result["processed_at"]
        post.llm_structured_json = json.dumps(llm_result["structured"], ensure_ascii=False) if llm_result["structured"] else ""
        post.llm_summary = llm_result["summary"] or ""
        post.summary = build_summary(
            title=post.title,
            upstream_summary=str(raw_post.get("description") or ""),
            llm_summary=post.llm_summary,
            content_text=content_text,
        )
        db.add(post)
        db.flush()

        categories = normalize_category_list(classify_categories(post.title, post.summary, content_text))
        # Prefer LLM category over rule-based for both filtering and display
        llm_structured = llm_result.get("structured") or {}
        llm_cat = llm_structured.get("category", "")
        if llm_cat in VALID_CATEGORIES:
            categories = [canonical_category(llm_cat)]
        category_source = "llm" if llm_cat in VALID_CATEGORIES else "rule_engine"
        db.query(PostCategory).filter(PostCategory.post_id == post.id).delete()
        db.flush()
        post.categories = [
            PostCategory(
                category_code=category_code,
                category_source="llm" if category_code == llm_cat else category_source,
            )
            for category_code in categories
        ]
        db.add(post)
        db.flush()
        return post, created

    def _update_source_high_water(self, source: Source, raw_posts: list[dict]) -> None:
        if not raw_posts:
            return

        latest_post = None
        latest_published_at = None
        for raw_post in raw_posts:
            upstream_post_id = str(raw_post.get("id") or "").strip()
            if not upstream_post_id:
                continue
            published_at = _parse_publish_time(raw_post)
            if latest_post is None:
                latest_post = raw_post
                latest_published_at = published_at
                continue
            if published_at is not None and (
                latest_published_at is None or _as_naive(published_at) > _as_naive(latest_published_at)
            ):
                latest_post = raw_post
                latest_published_at = published_at

        if latest_post is None:
            return
        source.last_seen_upstream_post_id = str(latest_post.get("id") or source.last_seen_upstream_post_id or "")
        if latest_published_at is not None:
            source.last_seen_published_at = latest_published_at

    def _upsert_projection(self, db: Session, post: Post) -> None:
        content_type = classify_content_type(post.title, post.summary, post.content_text_snapshot)
        categories = normalize_category_list([category.category_code for category in post.categories])
        primary_category = categories[0]
        time_signals = extract_time_signals(post.title, post.summary, post.content_text_snapshot, post.published_at)

        llm_start, llm_end, llm_deadline = _parse_llm_datetimes(post.llm_structured_json, post.published_at)
        event_start = time_signals.event_start_at or llm_start
        event_end = time_signals.event_end_at or llm_end
        deadline = time_signals.deadline_at or llm_deadline
        time_signals_merged = TimeSignals(event_start_at=event_start, event_end_at=event_end, deadline_at=deadline)

        time_status, timeliness_level = derive_time_status(time_signals_merged)
        participation_status = derive_participation_status(
            content_type=content_type,
            time_status=time_status,
            text=normalize_whitespace(f"{post.title} {post.summary} {post.content_text_snapshot}"),
        )
        display_level = derive_display_level(content_type, timeliness_level)
        ranking_score = compute_ranking_score(
            participation_status=participation_status,
            content_type=content_type,
            primary_category=primary_category,
            time_status=time_status,
            deadline_at=deadline,
            published_at=post.published_at,
        )

        projection = post.projection or PostProjection(post_id=post.id)
        projection.primary_category = primary_category
        projection.content_type = content_type.value
        projection.event_start_at = event_start
        projection.event_end_at = event_end
        projection.deadline_at = deadline
        projection.time_status = time_status.value
        projection.timeliness_level = timeliness_level.value
        projection.participation_status = participation_status.value
        projection.ranking_score = ranking_score
        projection.display_level = display_level.value
        db.add(projection)
        db.flush()
