from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class PostItemResponse(BaseModel):
    id: int
    source_id: int
    source_name: str
    title: str
    llm_title: str
    summary: str
    llm_summary: str
    original_url: str
    cover_url: str
    published_at: datetime | None
    content_status: str
    content_type: str
    primary_category: str
    categories: list[str]
    event_start_at: datetime | None
    event_end_at: datetime | None
    deadline_at: datetime | None
    key_time_at: datetime | None
    key_time_type: str
    time_status: str
    timeliness_level: str
    participation_status: str
    ranking_score: float
    display_level: str


class PostDetailResponse(PostItemResponse):
    content_html: str


class PagedPostsResponse(BaseModel):
    items: list[PostItemResponse]
    total: int
    offset: int
    limit: int


class CategoryCountResponse(BaseModel):
    category: str
    count: int


class CategoryStatsResponse(BaseModel):
    categories: list[CategoryCountResponse]
    content_type_stats: dict[str, int]
    participation_stats: dict[str, int]
    time_status_stats: dict[str, int]
    time_unknown_breakdown: dict[str, int] = {}


class SourceResponse(BaseModel):
    id: int
    upstream_source_id: str
    name: str
    source_type: str
    status: str
    cover_url: str
    intro: str
    post_count: int
    last_synced_at: datetime | None
    last_seen_published_at: datetime | None
    last_seen_upstream_post_id: str


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
    posts_fetched: int
    posts_inserted: int
    posts_updated: int
    posts_discarded: int
    discarded_count: int
    discard_stats_by_reason: dict[str, int]
    error_summary: str
    started_at: datetime | None
    finished_at: datetime | None
    items: list[SyncJobItemResponse] = []


class HealthResponse(BaseModel):
    status: str
    database: str
    upstream_configured: bool


class SupportRequest(BaseModel):
    client_id: str


class SupportResponse(BaseModel):
    count: int
    liked: bool
    incremented: bool = False


class JobResponse(BaseModel):
    id: int
    job_type: str
    dedupe_key: str
    status: str
    priority: int
    payload: dict
    attempts: int
    max_attempts: int
    last_error: str
    result: dict
    created_at: datetime
    updated_at: datetime
    finished_at: datetime | None


class JobCreateResponse(BaseModel):
    created: int
    jobs: list[JobResponse]


class JobSummaryResponse(BaseModel):
    pending: int = 0
    running: int = 0
    succeeded: int = 0
    failed: int = 0
    dead: int = 0
    cancelled: int = 0
