from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class ArticleItemResponse(BaseModel):
    id: int
    source_id: int
    source_name: str
    title: str
    summary: str
    original_url: str
    cover_url: str
    published_at: datetime | None
    content_status: str
    content_type: str
    display_level: str
    categories: list[str]


class ArticleDetailResponse(ArticleItemResponse):
    content_html: str


class PagedArticlesResponse(BaseModel):
    items: list[ArticleItemResponse]
    total: int
    offset: int
    limit: int


class CategoryCountResponse(BaseModel):
    category: str
    count: int


class CategoryStatsResponse(BaseModel):
    categories: list[CategoryCountResponse]
    content_type_stats: dict[str, int]


class SourceResponse(BaseModel):
    id: int
    upstream_source_id: str
    name: str
    source_type: str
    status: str
    cover_url: str
    intro: str
    article_count: int
    last_synced_at: datetime | None


class SyncJobItemResponse(BaseModel):
    id: int
    source_id: int | None
    stage: str
    status: str
    item_count: int
    error_message: str
    started_at: datetime
    finished_at: datetime | None


class SyncJobResponse(BaseModel):
    id: int
    trigger_type: str
    status: str
    sources_synced: int
    articles_fetched: int
    articles_inserted: int
    articles_updated: int
    error_summary: str
    started_at: datetime | None
    finished_at: datetime | None
    items: list[SyncJobItemResponse] = []


class HealthResponse(BaseModel):
    status: str
    database: str
    upstream_configured: bool

