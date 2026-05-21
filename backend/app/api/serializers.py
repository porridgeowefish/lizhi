from __future__ import annotations

from app.db.models import Article, Source, SyncJob, SyncJobItem
from app.schemas.responses import (
    ArticleDetailResponse,
    ArticleItemResponse,
    SourceResponse,
    SyncJobItemResponse,
    SyncJobResponse,
)


def serialize_article(article: Article) -> ArticleItemResponse:
    return ArticleItemResponse(
        id=article.id,
        source_id=article.source_id,
        source_name=article.source_name_snapshot,
        title=article.title,
        summary=article.summary,
        original_url=article.original_url,
        cover_url=article.cover_url,
        published_at=article.published_at,
        content_status=article.content_status,
        content_type=article.content_type,
        display_level=article.display_level,
        categories=[category.category_code for category in article.categories],
    )


def serialize_article_detail(article: Article) -> ArticleDetailResponse:
    base = serialize_article(article).model_dump()
    return ArticleDetailResponse(**base, content_html=article.content_html)


def serialize_source(source: Source) -> SourceResponse:
    return SourceResponse(
        id=source.id,
        upstream_source_id=source.upstream_source_id,
        name=source.name,
        source_type=source.source_type,
        status=source.status,
        cover_url=source.cover_url,
        intro=source.intro,
        article_count=source.article_count,
        last_synced_at=source.last_synced_at,
    )


def serialize_sync_job_item(item: SyncJobItem) -> SyncJobItemResponse:
    return SyncJobItemResponse(
        id=item.id,
        source_id=item.source_id,
        stage=item.stage,
        status=item.status,
        item_count=item.item_count,
        error_message=item.error_message,
        started_at=item.started_at,
        finished_at=item.finished_at,
    )


def serialize_sync_job(job: SyncJob) -> SyncJobResponse:
    return SyncJobResponse(
        id=job.id,
        trigger_type=job.trigger_type,
        status=job.status,
        sources_synced=job.sources_synced,
        articles_fetched=job.articles_fetched,
        articles_inserted=job.articles_inserted,
        articles_updated=job.articles_updated,
        error_summary=job.error_summary,
        started_at=job.started_at,
        finished_at=job.finished_at,
        items=[serialize_sync_job_item(item) for item in job.items],
    )

