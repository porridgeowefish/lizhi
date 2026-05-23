from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.db.models import SupportClick
from app.schemas.responses import SupportRequest, SupportResponse

router = APIRouter(prefix="/api/support", tags=["support"])


def _count_supports(db: Session) -> int:
    return db.query(func.count(SupportClick.id)).scalar() or 0


def _normalize_client_id(client_id: str) -> str:
    return client_id.strip()[:128]


@router.get("", response_model=SupportResponse)
def get_support(client_id: str = Query(default=""), db: Session = Depends(get_db)):
    token = _normalize_client_id(client_id)
    liked = False
    if token:
        liked = db.query(SupportClick.id).filter(SupportClick.client_token == token).first() is not None
    return SupportResponse(count=_count_supports(db), liked=liked)


@router.post("", response_model=SupportResponse)
def add_support(payload: SupportRequest, db: Session = Depends(get_db)):
    token = _normalize_client_id(payload.client_id)
    if len(token) < 8:
        return SupportResponse(count=_count_supports(db), liked=False)

    db.add(SupportClick(client_token=token))
    try:
        db.commit()
        return SupportResponse(count=_count_supports(db), liked=True, incremented=True)
    except IntegrityError:
        db.rollback()
        return SupportResponse(count=_count_supports(db), liked=True, incremented=False)
