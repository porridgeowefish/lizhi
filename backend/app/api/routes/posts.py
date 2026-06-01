from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.api.serializers import serialize_post, serialize_post_detail
from app.schemas.responses import CategoryStatsResponse, PagedPostsResponse, PostDetailResponse

router = APIRouter(prefix="/api/posts", tags=["posts"])


@router.get("", response_model=PagedPostsResponse)
def list_posts(
    request: Request,
    category: str = Query(default=""),
    subcategory: str = Query(default=""),
    content_type: str = Query(default=""),
    time_range: str = Query(default=""),
    search: str = Query(default=""),
    source_id: int | None = Query(default=None),
    sort: str = Query(default="deadline"),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    show_all: bool = Query(default=False),
    db: Session = Depends(get_db),
):
    items, total = request.app.state.query_service.list_posts(
        db,
        category=category,
        subcategory=subcategory,
        content_type=content_type,
        time_range=time_range,
        search=search,
        source_id=source_id,
        sort=sort,
        offset=offset,
        limit=limit,
        show_all=show_all,
    )
    return PagedPostsResponse(
        items=[serialize_post(item) for item in items],
        total=total,
        offset=offset,
        limit=limit,
    )


@router.get("/categories", response_model=CategoryStatsResponse)
def category_stats(request: Request, db: Session = Depends(get_db)):
    (
        categories,
        content_type_stats,
        participation_stats,
        time_status_stats,
        time_unknown_breakdown,
    ) = request.app.state.query_service.get_category_stats(db)
    return CategoryStatsResponse(
        categories=categories,
        content_type_stats=content_type_stats,
        participation_stats=participation_stats,
        time_status_stats=time_status_stats,
        time_unknown_breakdown=time_unknown_breakdown,
    )


@router.get("/{post_id}", response_model=PostDetailResponse)
def get_post(request: Request, post_id: int, db: Session = Depends(get_db)):
    post = request.app.state.query_service.get_post(db, post_id)
    if post is None:
        raise HTTPException(status_code=404, detail="post not found")
    return serialize_post_detail(post)
