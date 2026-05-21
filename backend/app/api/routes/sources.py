from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.api.serializers import serialize_source
from app.schemas.responses import SourceResponse

router = APIRouter(prefix="/api/sources", tags=["sources"])


@router.get("", response_model=list[SourceResponse])
def list_sources(request: Request, db: Session = Depends(get_db)):
    sources = request.app.state.query_service.list_sources(db)
    return [serialize_source(source) for source in sources]

