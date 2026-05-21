from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.api.serializers import serialize_article, serialize_article_detail
from app.schemas.responses import ArticleDetailResponse, CategoryStatsResponse, PagedArticlesResponse

router = APIRouter(prefix="/api/articles", tags=["articles"])


@router.get("", response_model=PagedArticlesResponse)
def list_articles(
    request: Request,
    category: str = Query(default=""),
    content_type: str = Query(default=""),
    search: str = Query(default=""),
    source_id: int | None = Query(default=None),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    show_all: bool = Query(default=False),
    db: Session = Depends(get_db),
):
    items, total = request.app.state.query_service.list_articles(
        db,
        category=category,
        content_type=content_type,
        search=search,
        source_id=source_id,
        offset=offset,
        limit=limit,
        show_all=show_all,
    )
    return PagedArticlesResponse(
        items=[serialize_article(item) for item in items],
        total=total,
        offset=offset,
        limit=limit,
    )


@router.get("/categories", response_model=CategoryStatsResponse)
def category_stats(request: Request, db: Session = Depends(get_db)):
    categories, content_type_stats = request.app.state.query_service.get_category_stats(db)
    return CategoryStatsResponse(categories=categories, content_type_stats=content_type_stats)


@router.get("/{article_id}", response_model=ArticleDetailResponse)
def get_article(request: Request, article_id: int, db: Session = Depends(get_db)):
    article = request.app.state.query_service.get_article(db, article_id)
    if article is None:
        raise HTTPException(status_code=404, detail="article not found")
    return serialize_article_detail(article)

