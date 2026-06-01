from __future__ import annotations

import json
from datetime import datetime

from app.application.classification import effective_primary_category, normalize_category_list
from app.db.models import Post, Source, SyncJob, SyncJobItem
from app.schemas.responses import (
    PostDetailResponse,
    PostItemResponse,
    SourceResponse,
    SyncJobItemResponse,
    SyncJobResponse,
)


def _extract_llm_title(post: Post) -> str:
    if post.llm_structured_json:
        try:
            structured = json.loads(post.llm_structured_json)
            title = structured.get("title", "")
            if title:
                return title
        except (json.JSONDecodeError, TypeError):
            pass
    return post.title


def _as_naive(value: datetime | None) -> datetime | None:
    if value is not None and value.tzinfo is not None:
        return value.replace(tzinfo=None)
    return value


def _key_time(projection) -> tuple[datetime | None, str]:
    if projection is None:
        return None, "none"

    now = datetime.now()
    candidates = [
        ("deadline", projection.deadline_at),
        ("event_start", projection.event_start_at),
    ]
    future_candidates = [
        (key, value)
        for key, value in candidates
        if (normalized := _as_naive(value)) is not None and normalized >= now
    ]
    if future_candidates:
        key, value = min(future_candidates, key=lambda item: _as_naive(item[1]))  # type: ignore[arg-type]
        return value, key

    past_candidates = [
        (key, value)
        for key, value in candidates
        if (normalized := _as_naive(value)) is not None and normalized < now
    ]
    if past_candidates:
        key, value = max(past_candidates, key=lambda item: _as_naive(item[1]))  # type: ignore[arg-type]
        return value, key

    return None, "none"


def serialize_post(post: Post) -> PostItemResponse:
    projection = post.projection
    key_time_at, key_time_type = _key_time(projection)
    stored_categories = [category.category_code for category in post.categories]
    primary_category = effective_primary_category(projection.primary_category if projection else "", stored_categories)
    categories = normalize_category_list(stored_categories + [primary_category])
    return PostItemResponse(
        id=post.id,
        source_id=post.source_id,
        source_name=post.source_name_snapshot,
        title=post.title,
        llm_title=_extract_llm_title(post),
        summary=post.summary,
        llm_summary=post.llm_summary or "",
        original_url=post.original_url,
        cover_url=post.cover_url,
        published_at=post.published_at,
        content_status=post.content_status,
        content_type=projection.content_type if projection else "unknown",
        primary_category=primary_category,
        categories=categories,
        event_start_at=projection.event_start_at if projection else None,
        event_end_at=projection.event_end_at if projection else None,
        deadline_at=projection.deadline_at if projection else None,
        key_time_at=key_time_at,
        key_time_type=key_time_type,
        time_status=projection.time_status if projection else "undated",
        timeliness_level=projection.timeliness_level if projection else "low",
        participation_status=projection.participation_status if projection else "uncertain",
        ranking_score=projection.ranking_score if projection else 0.0,
        display_level=projection.display_level if projection else "low",
    )


def serialize_post_detail(post: Post) -> PostDetailResponse:
    base = serialize_post(post).model_dump()
    return PostDetailResponse(**base, content_html=post.content_html)


def serialize_source(source: Source) -> SourceResponse:
    return SourceResponse(
        id=source.id,
        upstream_source_id=source.upstream_source_id,
        name=source.name,
        source_type=source.source_type,
        status=source.status,
        cover_url=source.cover_url,
        intro=source.intro,
        post_count=source.post_count,
        last_synced_at=source.last_synced_at,
        last_seen_published_at=source.last_seen_published_at,
        last_seen_upstream_post_id=source.last_seen_upstream_post_id or "",
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
    try:
        discard_stats = json.loads(job.discard_stats_json or "{}")
    except json.JSONDecodeError:
        discard_stats = {}
    return SyncJobResponse(
        id=job.id,
        trigger_type=job.trigger_type,
        status=job.status,
        sources_synced=job.sources_synced,
        posts_fetched=job.posts_fetched,
        posts_inserted=job.posts_inserted,
        posts_updated=job.posts_updated,
        posts_discarded=job.posts_discarded,
        discarded_count=job.posts_discarded,
        discard_stats_by_reason=discard_stats,
        error_summary=job.error_summary,
        started_at=job.started_at,
        finished_at=job.finished_at,
        items=[serialize_sync_job_item(item) for item in job.items],
    )
