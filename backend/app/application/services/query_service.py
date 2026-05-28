from __future__ import annotations

from collections import Counter
from datetime import date, datetime, timedelta

from sqlalchemy import case, func, or_, select
from sqlalchemy.orm import Session, joinedload

from app.db.models import Post, PostCategory, PostProjection, Source, SyncJob
from app.domain.enums import ContentStatus, DisplayLevel, LlmStatus, TimelinessLevel, TimeStatus


DISPLAY_PUBLISHED_AFTER = datetime(2022, 1, 1)


class QueryService:
    def __init__(self, *, homepage_recent_undated_days: int = 90):
        self.homepage_recent_undated_days = homepage_recent_undated_days

    def list_posts(
        self,
        db: Session,
        *,
        category: str = "",
        content_type: str = "",
        time_range: str = "",
        search: str = "",
        source_id: int | None = None,
        sort: str = "deadline",
        offset: int = 0,
        limit: int = 20,
        show_all: bool = False,
    ) -> tuple[list[Post], int]:
        statement = (
            select(Post)
            .join(Post.projection)
            .options(joinedload(Post.categories), joinedload(Post.source), joinedload(Post.projection))
        )
        count_statement = select(func.count(Post.id)).join(PostProjection, PostProjection.post_id == Post.id)

        if category:
            statement = statement.join(Post.categories).where(PostCategory.category_code == category)
            count_statement = count_statement.join(PostCategory).where(PostCategory.category_code == category)

        if not show_all:
            now = datetime.now()
            recent_undated_cutoff = now - timedelta(days=max(self.homepage_recent_undated_days, 0))
            has_future_key_time = (PostProjection.deadline_at >= now) | (PostProjection.event_start_at >= now)
            has_key_time = PostProjection.deadline_at.is_not(None) | PostProjection.event_start_at.is_not(None)
            recent_undated = (~has_key_time) & Post.published_at.is_not(None) & (Post.published_at >= recent_undated_cutoff)
            default_visibility = has_future_key_time | recent_undated
            statement = statement.where(PostProjection.display_level != DisplayLevel.HIDDEN.value)
            statement = statement.where(PostProjection.timeliness_level != TimelinessLevel.HIDDEN.value)
            statement = statement.where(or_(Post.published_at.is_(None), Post.published_at >= DISPLAY_PUBLISHED_AFTER))
            statement = statement.where(default_visibility)
            count_statement = count_statement.where(PostProjection.display_level != DisplayLevel.HIDDEN.value)
            count_statement = count_statement.where(PostProjection.timeliness_level != TimelinessLevel.HIDDEN.value)
            count_statement = count_statement.where(or_(Post.published_at.is_(None), Post.published_at >= DISPLAY_PUBLISHED_AFTER))
            count_statement = count_statement.where(default_visibility)

        if content_type:
            statement = statement.where(PostProjection.content_type == content_type)
            count_statement = count_statement.where(PostProjection.content_type == content_type)

        if time_range:
            today = date.today()
            monday = today - timedelta(days=today.weekday())
            ranges = {
                "this_week": (monday, monday + timedelta(days=6)),
                "this_weekend": (monday + timedelta(days=5), monday + timedelta(days=6)),
                "next_week": (monday + timedelta(days=7), monday + timedelta(days=13)),
            }
            if time_range in ranges:
                sd, ed = ranges[time_range]
                start = datetime(sd.year, sd.month, sd.day)
                end = datetime(ed.year, ed.month, ed.day, 23, 59, 59)
                statement = statement.where(PostProjection.deadline_at >= start, PostProjection.deadline_at <= end)
                count_statement = count_statement.where(PostProjection.deadline_at >= start, PostProjection.deadline_at <= end)

        if search:
            pattern = f"%{search}%"
            search_clause = or_(
                Post.title.ilike(pattern),
                Post.summary.ilike(pattern),
                Post.source_name_snapshot.ilike(pattern),
            )
            statement = statement.where(search_clause)
            count_statement = count_statement.where(search_clause)

        if source_id is not None:
            statement = statement.where(Post.source_id == source_id)
            count_statement = count_statement.where(Post.source_id == source_id)

        if sort == "deadline":
            now = datetime.now()
            deadline_future = PostProjection.deadline_at >= now
            start_future = PostProjection.event_start_at >= now
            has_deadline = PostProjection.deadline_at.is_not(None)
            has_start = PostProjection.event_start_at.is_not(None)
            has_key_time = has_deadline | has_start
            has_future_key_time = deadline_future | start_future
            key_time_group = case((has_future_key_time, 0), (~has_key_time, 1), else_=2)
            future_key_time = case(
                (
                    deadline_future & start_future & (PostProjection.deadline_at <= PostProjection.event_start_at),
                    PostProjection.deadline_at,
                ),
                (deadline_future & start_future, PostProjection.event_start_at),
                (deadline_future, PostProjection.deadline_at),
                (start_future, PostProjection.event_start_at),
            )
            expired_key_time = case(
                (has_deadline & has_start & (PostProjection.deadline_at >= PostProjection.event_start_at), PostProjection.deadline_at),
                (has_deadline & has_start, PostProjection.event_start_at),
                (has_deadline, PostProjection.deadline_at),
                (has_start, PostProjection.event_start_at),
            )
            undated_published_at = case((~has_key_time, Post.published_at))
            statement = statement.order_by(
                key_time_group.asc(),
                future_key_time.asc().nullslast(),
                undated_published_at.asc().nullslast(),
                expired_key_time.desc().nullslast(),
                Post.id.desc(),
            )
        else:
            statement = statement.order_by(
                Post.published_at.desc().nullslast(),
                PostProjection.deadline_at.asc().nullslast(),
                Post.id.desc(),
            )
        statement = statement.offset(offset).limit(limit)

        items = db.execute(statement).scalars().unique().all()
        total = db.execute(count_statement).scalar_one()
        return items, total

    def get_post(self, db: Session, post_id: int) -> Post | None:
        statement = (
            select(Post)
            .options(joinedload(Post.categories), joinedload(Post.source), joinedload(Post.projection))
            .where(Post.id == post_id)
        )
        return db.execute(statement).scalars().unique().first()

    def get_category_stats(self, db: Session) -> tuple[list[dict], dict[str, int], dict[str, int], dict[str, int], dict[str, int]]:
        now = datetime.now()
        recent_undated_cutoff = now - timedelta(days=max(self.homepage_recent_undated_days, 0))
        has_future_key_time = (PostProjection.deadline_at >= now) | (PostProjection.event_start_at >= now)
        has_key_time = PostProjection.deadline_at.is_not(None) | PostProjection.event_start_at.is_not(None)
        recent_undated = (~has_key_time) & Post.published_at.is_not(None) & (Post.published_at >= recent_undated_cutoff)
        default_visibility = has_future_key_time | recent_undated
        category_rows = db.execute(
            select(PostCategory.category_code, func.count(PostCategory.id))
            .join(Post, Post.id == PostCategory.post_id)
            .join(PostProjection, PostProjection.post_id == Post.id)
            .where(PostProjection.display_level != DisplayLevel.HIDDEN.value)
            .where(PostProjection.timeliness_level != TimelinessLevel.HIDDEN.value)
            .where(or_(Post.published_at.is_(None), Post.published_at >= DISPLAY_PUBLISHED_AFTER))
            .where(default_visibility)
            .group_by(PostCategory.category_code)
            .order_by(PostCategory.category_code)
        ).all()
        categories = [{"category": row[0], "count": row[1]} for row in category_rows]

        projection_rows = db.execute(
            select(
                PostProjection.content_type,
                PostProjection.participation_status,
                PostProjection.time_status,
                Post.content_status,
                Post.llm_status,
            )
            .join(Post, Post.id == PostProjection.post_id)
            .where(or_(Post.published_at.is_(None), Post.published_at >= DISPLAY_PUBLISHED_AFTER))
            .where(PostProjection.display_level != DisplayLevel.HIDDEN.value)
            .where(PostProjection.timeliness_level != TimelinessLevel.HIDDEN.value)
            .where(default_visibility)
        ).all()
        content_counts = Counter(row[0] for row in projection_rows)
        participation_counts = Counter(row[1] for row in projection_rows)
        time_counts = Counter(row[2] for row in projection_rows)
        unknown_time_breakdown = Counter()
        for _, _, time_status, content_status, llm_status in projection_rows:
            if time_status != TimeStatus.UNDATED.value:
                continue
            if content_status != ContentStatus.READY.value:
                unknown_time_breakdown["content_missing"] += 1
            elif llm_status in {LlmStatus.NOT_REQUESTED.value, LlmStatus.PENDING.value}:
                unknown_time_breakdown["llm_waiting"] += 1
            elif llm_status == LlmStatus.FAILED.value:
                unknown_time_breakdown["llm_failed"] += 1
            elif llm_status in {LlmStatus.COMPLETED.value, LlmStatus.FALLBACK.value}:
                unknown_time_breakdown["processed_no_time"] += 1
            else:
                unknown_time_breakdown["other"] += 1
        return (
            categories,
            dict(sorted(content_counts.items())),
            dict(sorted(participation_counts.items())),
            dict(sorted(time_counts.items())),
            dict(sorted(unknown_time_breakdown.items())),
        )

    def list_sources(self, db: Session) -> list[Source]:
        return db.execute(select(Source).order_by(Source.name, Source.id)).scalars().all()

    def get_sync_job(self, db: Session, job_id: int) -> SyncJob | None:
        statement = select(SyncJob).where(SyncJob.id == job_id)
        return db.execute(statement).scalars().first()
