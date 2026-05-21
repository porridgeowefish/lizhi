from __future__ import annotations

from fastapi import APIRouter, Request
from sqlalchemy import text

from app.schemas.responses import HealthResponse

router = APIRouter(prefix="/api", tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health(request: Request):
    db = request.app.state.session_factory()
    try:
        db.execute(text("SELECT 1"))
        database = "ok"
    except Exception:  # noqa: BLE001
        database = "error"
    finally:
        db.close()

    settings = request.app.state.settings
    return HealthResponse(
        status="ok" if database == "ok" else "degraded",
        database=database,
        upstream_configured=bool(settings.upstream_base_url),
    )

