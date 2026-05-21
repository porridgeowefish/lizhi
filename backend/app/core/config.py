from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


def _as_bool(value: str, default: bool) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(slots=True)
class Settings:
    app_name: str = "Campus Feed Backend"
    app_version: str = "0.1.0"
    host: str = "0.0.0.0"
    port: int = 8002
    database_url: str = ""
    sync_interval_minutes: int = 10
    article_fetch_limit: int = 50
    source_fetch_limit: int = 200
    enable_scheduler: bool = True
    upstream_base_url: str = ""
    upstream_username: str = ""
    upstream_password: str = ""

    @classmethod
    def from_env(cls) -> "Settings":
        load_dotenv(Path(__file__).resolve().parents[2] / ".env")
        default_db_path = Path(__file__).resolve().parents[2] / "data" / "backend.db"
        return cls(
            host=os.getenv("BACKEND_HOST", "0.0.0.0"),
            port=int(os.getenv("BACKEND_PORT", "8002")),
            database_url=os.getenv("BACKEND_DATABASE_URL", f"sqlite:///{default_db_path.as_posix()}"),
            sync_interval_minutes=int(os.getenv("BACKEND_SYNC_INTERVAL_MINUTES", "10")),
            article_fetch_limit=int(os.getenv("BACKEND_ARTICLE_FETCH_LIMIT", "50")),
            source_fetch_limit=int(os.getenv("BACKEND_SOURCE_FETCH_LIMIT", "200")),
            enable_scheduler=_as_bool(os.getenv("BACKEND_ENABLE_SCHEDULER"), True),
            upstream_base_url=os.getenv("BACKEND_UPSTREAM_BASE_URL", ""),
            upstream_username=os.getenv("BACKEND_UPSTREAM_USERNAME", ""),
            upstream_password=os.getenv("BACKEND_UPSTREAM_PASSWORD", ""),
        )
