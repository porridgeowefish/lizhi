from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class Source(TimestampMixin, Base):
    __tablename__ = "sources"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    upstream_source_id: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255), index=True)
    source_type: Mapped[str] = mapped_column(String(64), default="wechat_official_account")
    status: Mapped[str] = mapped_column(String(32), default="enabled")
    cover_url: Mapped[str] = mapped_column(String(1024), default="")
    intro: Mapped[str] = mapped_column(Text, default="")
    post_count: Mapped[int] = mapped_column(Integer, default=0)
    last_synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_seen_published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_seen_upstream_post_id: Mapped[str] = mapped_column(String(255), default="")

    raw_payloads: Mapped[list["RawPayload"]] = relationship(back_populates="source")
    posts: Mapped[list["Post"]] = relationship(back_populates="source")
    discarded_posts: Mapped[list["DiscardedPost"]] = relationship(back_populates="source")


class RawPayload(TimestampMixin, Base):
    __tablename__ = "raw_payloads"
    __table_args__ = (
        UniqueConstraint("source_id", "upstream_post_id", name="uq_raw_payload_source_post"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    source_id: Mapped[int] = mapped_column(ForeignKey("sources.id"), index=True)
    upstream_post_id: Mapped[str] = mapped_column(String(255), index=True)
    payload_json: Mapped[str] = mapped_column(Text)
    payload_hash: Mapped[str] = mapped_column(String(64), index=True)
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    source: Mapped[Source] = relationship(back_populates="raw_payloads")


class Post(TimestampMixin, Base):
    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    upstream_post_id: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    source_id: Mapped[int] = mapped_column(ForeignKey("sources.id"), index=True)
    source_name_snapshot: Mapped[str] = mapped_column(String(255))
    title: Mapped[str] = mapped_column(String(500), index=True)
    summary: Mapped[str] = mapped_column(Text, default="")
    llm_summary: Mapped[str] = mapped_column(Text, default="")
    original_url: Mapped[str] = mapped_column(String(2048), default="")
    cover_url: Mapped[str] = mapped_column(String(2048), default="")
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    content_html: Mapped[str] = mapped_column(Text, default="")
    content_text_snapshot: Mapped[str] = mapped_column(Text, default="")
    content_status: Mapped[str] = mapped_column(String(32), default="missing")
    content_hash: Mapped[str] = mapped_column(String(64), index=True)
    llm_structured_json: Mapped[str] = mapped_column(Text, default="")
    llm_model: Mapped[str] = mapped_column(String(128), default="")
    llm_prompt_version: Mapped[str] = mapped_column(String(64), default="")
    llm_status: Mapped[str] = mapped_column(String(32), default="not_requested")
    llm_processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    ingestion_status: Mapped[str] = mapped_column(String(32), default="new")

    source: Mapped[Source] = relationship(back_populates="posts")
    categories: Mapped[list["PostCategory"]] = relationship(
        back_populates="post",
        cascade="all, delete-orphan",
    )
    projection: Mapped["PostProjection | None"] = relationship(
        back_populates="post",
        cascade="all, delete-orphan",
        uselist=False,
    )


class PostCategory(Base):
    __tablename__ = "post_categories"
    __table_args__ = (
        UniqueConstraint("post_id", "category_code", name="uq_post_category_code"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    post_id: Mapped[int] = mapped_column(ForeignKey("posts.id"), index=True)
    category_code: Mapped[str] = mapped_column(String(64), index=True)
    category_source: Mapped[str] = mapped_column(String(64), default="rule_engine")

    post: Mapped[Post] = relationship(back_populates="categories")


class PostProjection(TimestampMixin, Base):
    __tablename__ = "post_projections"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    post_id: Mapped[int] = mapped_column(ForeignKey("posts.id"), unique=True, index=True)
    primary_category: Mapped[str] = mapped_column(String(64), index=True)
    content_type: Mapped[str] = mapped_column(String(32), default="unknown", index=True)
    event_start_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    event_end_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    deadline_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    time_status: Mapped[str] = mapped_column(String(32), default="undated", index=True)
    timeliness_level: Mapped[str] = mapped_column(String(32), default="low", index=True)
    participation_status: Mapped[str] = mapped_column(String(32), default="uncertain", index=True)
    ranking_score: Mapped[float] = mapped_column(Float, default=0.0, index=True)
    display_level: Mapped[str] = mapped_column(String(32), default="low", index=True)

    post: Mapped[Post] = relationship(back_populates="projection")


class OcrImageCache(TimestampMixin, Base):
    __tablename__ = "ocr_image_cache"
    __table_args__ = (
        UniqueConstraint("image_url_hash", "ocr_action", name="uq_ocr_image_cache_hash_action"),
        Index("ix_ocr_image_cache_month_status", "month_key", "status"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    image_url_hash: Mapped[str] = mapped_column(String(64), index=True)
    image_url: Mapped[str] = mapped_column(Text)
    ocr_action: Mapped[str] = mapped_column(String(64), default="RecognizeAgent", index=True)
    ocr_text: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(32), default="success", index=True)
    error_message: Mapped[str] = mapped_column(Text, default="")
    month_key: Mapped[str] = mapped_column(String(7), default="", index=True)
    post_id: Mapped[int | None] = mapped_column(ForeignKey("posts.id"), nullable=True, index=True)
    upstream_post_id: Mapped[str] = mapped_column(String(255), default="", index=True)


class OcrUsageLog(TimestampMixin, Base):
    __tablename__ = "ocr_usage_logs"
    __table_args__ = (
        Index("ix_ocr_usage_logs_month_action_status", "month_key", "ocr_action", "status"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    image_url_hash: Mapped[str] = mapped_column(String(64), index=True)
    image_url: Mapped[str] = mapped_column(Text)
    ocr_action: Mapped[str] = mapped_column(String(64), default="RecognizeAgent", index=True)
    status: Mapped[str] = mapped_column(String(32), default="success", index=True)
    month_key: Mapped[str] = mapped_column(String(7), default="", index=True)
    post_id: Mapped[int | None] = mapped_column(ForeignKey("posts.id"), nullable=True, index=True)
    upstream_post_id: Mapped[str] = mapped_column(String(255), default="", index=True)
    error_message: Mapped[str] = mapped_column(Text, default="")


class LlmTask(TimestampMixin, Base):
    __tablename__ = "llm_tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    post_id: Mapped[int] = mapped_column(ForeignKey("posts.id"), unique=True, index=True)
    status: Mapped[str] = mapped_column(String(32), default="pending", index=True)
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    last_error: Mapped[str] = mapped_column(Text, default="")
    locked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class JobQueue(TimestampMixin, Base):
    __tablename__ = "job_queue"
    __table_args__ = (
        Index("ix_job_queue_claim", "status", "run_after", "priority", "created_at"),
        Index("ix_job_queue_finished", "status", "finished_at"),
        Index("ix_job_queue_dedupe", "job_type", "dedupe_key", "status"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    job_type: Mapped[str] = mapped_column(String(64), index=True)
    dedupe_key: Mapped[str] = mapped_column(String(255), index=True)
    status: Mapped[str] = mapped_column(String(32), default="pending", index=True)
    priority: Mapped[int] = mapped_column(Integer, default=100)
    payload_json: Mapped[str] = mapped_column(Text, default="{}")
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    max_attempts: Mapped[int] = mapped_column(Integer, default=3)
    run_after: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)
    locked_by: Mapped[str] = mapped_column(String(128), default="")
    locked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_error: Mapped[str] = mapped_column(Text, default="")
    result_json: Mapped[str] = mapped_column(Text, default="{}")
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class SupportClick(TimestampMixin, Base):
    __tablename__ = "support_clicks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    client_token: Mapped[str] = mapped_column(String(128), unique=True, index=True)


class DiscardedPost(Base):
    __tablename__ = "discarded_posts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    upstream_post_id: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    source_id: Mapped[int | None] = mapped_column(ForeignKey("sources.id"), nullable=True, index=True)
    title_hash: Mapped[str] = mapped_column(String(64), index=True)
    discard_reason: Mapped[str] = mapped_column(String(64), index=True)
    discard_stage: Mapped[str] = mapped_column(String(64), default="prescreen")
    matched_rule_version: Mapped[str] = mapped_column(String(32), default="iter1-v1")
    matched_fields: Mapped[str] = mapped_column(Text, default="")
    matched_keywords: Mapped[str] = mapped_column(Text, default="")
    quality_signals: Mapped[str] = mapped_column(Text, default="")
    discarded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    source: Mapped[Source | None] = relationship(back_populates="discarded_posts")


class SyncJob(TimestampMixin, Base):
    __tablename__ = "sync_jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    trigger_type: Mapped[str] = mapped_column(String(32))
    status: Mapped[str] = mapped_column(String(32), default="pending", index=True)
    sources_synced: Mapped[int] = mapped_column(Integer, default=0)
    posts_fetched: Mapped[int] = mapped_column(Integer, default=0)
    posts_inserted: Mapped[int] = mapped_column(Integer, default=0)
    posts_updated: Mapped[int] = mapped_column(Integer, default=0)
    posts_discarded: Mapped[int] = mapped_column(Integer, default=0)
    discard_stats_json: Mapped[str] = mapped_column(Text, default="{}")
    error_summary: Mapped[str] = mapped_column(Text, default="")
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    items: Mapped[list["SyncJobItem"]] = relationship(
        back_populates="sync_job",
        cascade="all, delete-orphan",
    )


class SyncJobItem(Base):
    __tablename__ = "sync_job_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    sync_job_id: Mapped[int] = mapped_column(ForeignKey("sync_jobs.id"), index=True)
    source_id: Mapped[int | None] = mapped_column(ForeignKey("sources.id"), nullable=True, index=True)
    stage: Mapped[str] = mapped_column(String(64), index=True)
    status: Mapped[str] = mapped_column(String(32), default="running")
    item_count: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[str] = mapped_column(Text, default="")
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    sync_job: Mapped[SyncJob] = relationship(back_populates="items")
