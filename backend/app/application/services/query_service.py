from __future__ import annotations

from collections import Counter

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, joinedload

from app.db.models import Article, ArticleCategory, Source, SyncJob
from app.domain.enums import DisplayLevel


class QueryService:
    def list_articles(
        self,
        db: Session,
        *,
        category: str = "",
        content_type: str = "",
        search: str = "",
        source_id: int | None = None,
        offset: int = 0,
        limit: int = 20,
        show_all: bool = False,
    ) -> tuple[list[Article], int]:
        statement = select(Article).options(joinedload(Article.categories), joinedload(Article.source))
        count_statement = select(func.count(Article.id))

        if category:
            statement = statement.join(Article.categories).where(ArticleCategory.category_code == category)
            count_statement = count_statement.join(ArticleCategory).where(ArticleCategory.category_code == category)

        if not show_all:
            statement = statement.where(Article.display_level != DisplayLevel.HIDDEN.value)
            count_statement = count_statement.where(Article.display_level != DisplayLevel.HIDDEN.value)

        if content_type:
            statement = statement.where(Article.content_type == content_type)
            count_statement = count_statement.where(Article.content_type == content_type)

        if search:
            pattern = f"%{search}%"
            search_clause = or_(
                Article.title.ilike(pattern),
                Article.summary.ilike(pattern),
                Article.source_name_snapshot.ilike(pattern),
            )
            statement = statement.where(search_clause)
            count_statement = count_statement.where(search_clause)

        if source_id is not None:
            statement = statement.where(Article.source_id == source_id)
            count_statement = count_statement.where(Article.source_id == source_id)

        statement = statement.order_by(Article.published_at.desc(), Article.id.desc()).offset(offset).limit(limit)

        items = db.execute(statement).scalars().unique().all()
        total = db.execute(count_statement).scalar_one()
        return items, total

    def get_article(self, db: Session, article_id: int) -> Article | None:
        statement = (
            select(Article)
            .options(joinedload(Article.categories), joinedload(Article.source))
            .where(Article.id == article_id)
        )
        return db.execute(statement).scalars().unique().first()

    def get_category_stats(self, db: Session) -> tuple[list[dict], dict[str, int]]:
        category_rows = db.execute(
            select(ArticleCategory.category_code, func.count(ArticleCategory.id))
            .group_by(ArticleCategory.category_code)
            .order_by(ArticleCategory.category_code)
        ).all()
        categories = [{"category": row[0], "count": row[1]} for row in category_rows]

        content_rows = db.execute(select(Article.content_type)).all()
        content_counts = Counter(row[0] for row in content_rows)
        return categories, dict(sorted(content_counts.items()))

    def list_sources(self, db: Session) -> list[Source]:
        return db.execute(select(Source).order_by(Source.name, Source.id)).scalars().all()

    def get_sync_job(self, db: Session, job_id: int) -> SyncJob | None:
        statement = select(SyncJob).where(SyncJob.id == job_id)
        return db.execute(statement).scalars().first()

