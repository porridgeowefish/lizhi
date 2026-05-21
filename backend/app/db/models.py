from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
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
    article_count: Mapped[int] = mapped_column(Integer, default=0)
    last_synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    articles: Mapped[list["Article"]] = relationship(back_populates="source")


class Article(TimestampMixin, Base):
    __tablename__ = "articles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    upstream_article_id: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    source_id: Mapped[int] = mapped_column(ForeignKey("sources.id"), index=True)
    source_name_snapshot: Mapped[str] = mapped_column(String(255))
    title: Mapped[str] = mapped_column(String(500), index=True)
    summary: Mapped[str] = mapped_column(Text, default="")
    original_url: Mapped[str] = mapped_column(String(2048), default="")
    cover_url: Mapped[str] = mapped_column(String(2048), default="")
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    content_html: Mapped[str] = mapped_column(Text, default="")
    content_status: Mapped[str] = mapped_column(String(32), default="missing")
    content_type: Mapped[str] = mapped_column(String(32), default="unknown", index=True)
    display_level: Mapped[str] = mapped_column(String(32), default="low", index=True)
    ingestion_status: Mapped[str] = mapped_column(String(32), default="new")

    source: Mapped[Source] = relationship(back_populates="articles")
    categories: Mapped[list["ArticleCategory"]] = relationship(
        back_populates="article",
        cascade="all, delete-orphan",
    )


class ArticleCategory(Base):
    __tablename__ = "article_categories"
    __table_args__ = (
        UniqueConstraint("article_id", "category_code", name="uq_article_category_code"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    article_id: Mapped[int] = mapped_column(ForeignKey("articles.id"), index=True)
    category_code: Mapped[str] = mapped_column(String(64), index=True)
    category_source: Mapped[str] = mapped_column(String(64), default="rule_engine")

    article: Mapped[Article] = relationship(back_populates="categories")


class SyncJob(TimestampMixin, Base):
    __tablename__ = "sync_jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    trigger_type: Mapped[str] = mapped_column(String(32))
    status: Mapped[str] = mapped_column(String(32), default="pending", index=True)
    sources_synced: Mapped[int] = mapped_column(Integer, default=0)
    articles_fetched: Mapped[int] = mapped_column(Integer, default=0)
    articles_inserted: Mapped[int] = mapped_column(Integer, default=0)
    articles_updated: Mapped[int] = mapped_column(Integer, default=0)
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

