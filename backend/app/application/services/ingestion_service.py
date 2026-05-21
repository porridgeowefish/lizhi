from __future__ import annotations

import logging
from datetime import datetime, timezone

from sqlalchemy import func
from sqlalchemy.orm import Session, sessionmaker

_logger = logging.getLogger(__name__)

from app.application.classification import (
    classify_categories,
    classify_content_type,
    derive_display_level,
)
from app.db.models import Article, ArticleCategory, Source, SyncJob, SyncJobItem
from app.domain.enums import ContentStatus, IngestionStatus, SourceStatus, SyncStage, SyncStatus, SyncTriggerType


class IngestionService:
    def __init__(self, session_factory: sessionmaker[Session], connector, settings):
        self.session_factory = session_factory
        self.connector = connector
        self.settings = settings

    async def run_sync(self, trigger_type: SyncTriggerType) -> SyncJob:
        db = self.session_factory()
        job = SyncJob(trigger_type=trigger_type.value, status=SyncStatus.PENDING.value)
        db.add(job)
        db.commit()
        db.refresh(job)

        job.status = SyncStatus.RUNNING.value
        job.started_at = datetime.now(timezone.utc)
        db.commit()

        source_failures: list[str] = []
        fatal_error = ""

        try:
            source_stage = self._start_item(db, job.id, None, SyncStage.FETCH_SOURCES.value)
            raw_sources = await self.connector.fetch_sources(limit=self.settings.source_fetch_limit)
            source_stage.item_count = len(raw_sources)
            self._finish_item(db, source_stage, SyncStatus.COMPLETED.value)

            sources = [self._upsert_source(db, raw_source) for raw_source in raw_sources]
            db.commit()

            for source in sources:
                fetch_item = self._start_item(db, job.id, source.id, SyncStage.FETCH_ARTICLES.value)
                try:
                    raw_articles = await self.connector.fetch_articles(
                        source_id=source.upstream_source_id,
                        limit=self.settings.article_fetch_limit,
                    )
                    if len(raw_articles) > 0:
                        _logger.info("source %s has %d articles", source.upstream_source_id, len(raw_articles))
                    fetch_item.item_count = len(raw_articles)
                    self._finish_item(db, fetch_item, SyncStatus.COMPLETED.value)

                    normalize_item = self._start_item(db, job.id, source.id, SyncStage.NORMALIZE.value)
                    persist_item = self._start_item(db, job.id, source.id, SyncStage.PERSIST.value)

                    normalized_count = 0
                    for raw_article in raw_articles:
                        created = self._upsert_article(db, source, raw_article)
                        normalized_count += 1
                        job.articles_inserted += 1 if created else 0
                        job.articles_updated += 0 if created else 1

                    # Fetch content for articles that lack it
                    content_item = self._start_item(db, job.id, source.id, "fetch_content")
                    content_count = 0
                    for raw_article in raw_articles:
                        article_id = str(raw_article.get("id", "")).strip()
                        if not article_id:
                            continue
                        article = db.query(Article).filter(Article.upstream_article_id == article_id).first()
                        if article is None:
                            _logger.debug("content fetch: article %s not found in db", article_id)
                            continue
                        if article.content_html:
                            continue
                        try:
                            detail = await self.connector.fetch_article_detail(article_id)
                        except Exception as exc:
                            _logger.warning("content fetch failed for %s: %s", article_id, exc)
                            continue
                        if detail and detail.get("content_html"):
                            article.content_html = detail["content_html"]
                            article.content_status = ContentStatus.READY.value
                            db.add(article)
                            content_count += 1
                        else:
                            _logger.debug("content fetch: no content_html for %s (detail=%s)", article_id, bool(detail))
                    db.commit()
                    content_item.item_count = content_count
                    self._finish_item(db, content_item, SyncStatus.COMPLETED.value)

                    normalize_item.item_count = normalized_count
                    persist_item.item_count = normalized_count
                    self._finish_item(db, normalize_item, SyncStatus.COMPLETED.value)
                    self._finish_item(db, persist_item, SyncStatus.COMPLETED.value)

                    job.sources_synced += 1
                    job.articles_fetched += len(raw_articles)
                    source.article_count = db.query(func.count(Article.id)).filter(Article.source_id == source.id).scalar() or 0
                    source.last_synced_at = datetime.now(timezone.utc)
                    db.commit()
                except Exception as exc:  # noqa: BLE001
                    db.rollback()
                    source_failures.append(f"{source.name}: {exc}")
                    self._fail_item(db, fetch_item, str(exc))

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
            fatal_error = str(exc)
            job.status = SyncStatus.FAILED.value
            job.error_summary = fatal_error
        finally:
            job.finished_at = datetime.now(timezone.utc)
            db.add(job)
            db.commit()
            db.refresh(job)
            db.close()

        return job

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

    def _fail_item(self, db: Session, item: SyncJobItem, error_message: str) -> None:
        item.status = SyncStatus.FAILED.value
        item.error_message = error_message
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

    def _upsert_article(self, db: Session, source: Source, raw_article: dict) -> bool:
        upstream_article_id = str(raw_article.get("id") or "").strip()
        if not upstream_article_id:
            raise ValueError("article is missing upstream id")

        summary = raw_article.get("description", "")
        title = raw_article.get("title", "")
        content_html = raw_article.get("content_html", "") or ""
        categories = classify_categories(title, summary)
        content_type = classify_content_type(title, summary)
        display_level = derive_display_level(content_type)
        publish_time = raw_article.get("publish_time")
        if isinstance(publish_time, (int, float)):
            publish_time = datetime.fromtimestamp(publish_time, tz=timezone.utc)
        elif not isinstance(publish_time, datetime):
            publish_time = None

        article = db.query(Article).filter(Article.upstream_article_id == upstream_article_id).first()
        created = article is None
        if article is None:
            article = Article(
                upstream_article_id=upstream_article_id,
                source_id=source.id,
                source_name_snapshot=source.name,
                title=title,
                summary=summary,
                original_url=raw_article.get("url", ""),
                cover_url=raw_article.get("pic_url", ""),
                published_at=publish_time,
                content_html=content_html,
                content_status=ContentStatus.READY.value if content_html else ContentStatus.MISSING.value,
                content_type=content_type.value,
                display_level=display_level.value,
                ingestion_status=IngestionStatus.NEW.value,
            )
            db.add(article)
            db.flush()
        else:
            article.source_id = source.id
            article.source_name_snapshot = source.name
            article.title = title
            article.summary = summary
            article.original_url = raw_article.get("url", "")
            article.cover_url = raw_article.get("pic_url", "")
            article.published_at = publish_time
            if content_html:
                article.content_html = content_html
                article.content_status = ContentStatus.READY.value
            article.content_type = content_type.value
            article.display_level = display_level.value
            article.ingestion_status = IngestionStatus.UPDATED.value
            article.categories.clear()
            db.add(article)
            db.flush()

        article.categories = [
            ArticleCategory(category_code=category_code, category_source="rule_engine")
            for category_code in categories
        ]
        db.add(article)
        db.flush()
        return created
