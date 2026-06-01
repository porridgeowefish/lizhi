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
    post_fetch_limit: int = 500
    incremental_post_fetch_limit: int = 100
    source_fetch_limit: int = 500
    enable_scheduler: bool = True
    upstream_refresh_enabled: bool = True
    upstream_refresh_on_startup: bool = True
    upstream_refresh_interval_minutes: int = 60
    upstream_refresh_start_page: int = 0
    upstream_refresh_end_page: int = 10
    upstream_refresh_request_delay_seconds: float = 1.0
    upstream_refresh_settle_seconds: int = 300
    upstream_base_url: str = ""
    upstream_username: str = ""
    upstream_password: str = ""
    llm_enabled: bool = False
    llm_base_url: str = ""
    llm_api_key: str = ""
    llm_model: str = ""
    llm_timeout_seconds: int = 30
    llm_prompt_version: str = "iter1-v1"
    llm_max_input_chars: int = 6000
    llm_queue_enabled: bool = True
    llm_worker_interval_seconds: int = 20
    llm_worker_batch_size: int = 2
    llm_worker_max_attempts: int = 3
    content_worker_batch_size: int = 5
    queue_recent_days: int = 30
    homepage_recent_undated_days: int = 90
    ocr_enabled: bool = False
    ocr_provider: str = "tencent"
    tencent_secret_id: str = ""
    tencent_secret_key: str = ""
    tencent_ocr_region: str = "ap-guangzhou"
    ocr_action: str = "RecognizeAgent"
    ocr_max_images_per_post: int = 8
    ocr_min_text_length: int = 120
    ocr_timeout_seconds: int = 20
    ocr_monthly_limit: int = 1000
    ocr_cache_enabled: bool = True
    ocr_count_failed_attempts: bool = True

    @classmethod
    def from_env(cls) -> "Settings":
        load_dotenv(Path(__file__).resolve().parents[2] / ".env")
        default_db_path = Path(__file__).resolve().parents[3] / ".run" / "backend.db"
        return cls(
            host=os.getenv("BACKEND_HOST", "0.0.0.0"),
            port=int(os.getenv("BACKEND_PORT", "8002")),
            database_url=os.getenv("BACKEND_DATABASE_URL", f"sqlite:///{default_db_path.as_posix()}"),
            sync_interval_minutes=int(os.getenv("BACKEND_SYNC_INTERVAL_MINUTES", "10")),
            post_fetch_limit=int(os.getenv("BACKEND_POST_FETCH_LIMIT", "500")),
            incremental_post_fetch_limit=int(os.getenv("BACKEND_INCREMENTAL_POST_FETCH_LIMIT", "100")),
            source_fetch_limit=int(os.getenv("BACKEND_SOURCE_FETCH_LIMIT", "500")),
            enable_scheduler=_as_bool(os.getenv("BACKEND_ENABLE_SCHEDULER"), True),
            upstream_refresh_enabled=_as_bool(os.getenv("BACKEND_UPSTREAM_REFRESH_ENABLED"), True),
            upstream_refresh_on_startup=_as_bool(os.getenv("BACKEND_UPSTREAM_REFRESH_ON_STARTUP"), True),
            upstream_refresh_interval_minutes=int(os.getenv("BACKEND_UPSTREAM_REFRESH_INTERVAL_MINUTES", "60")),
            upstream_refresh_start_page=int(os.getenv("BACKEND_UPSTREAM_REFRESH_START_PAGE", "0")),
            upstream_refresh_end_page=int(os.getenv("BACKEND_UPSTREAM_REFRESH_END_PAGE", "10")),
            upstream_refresh_request_delay_seconds=float(os.getenv("BACKEND_UPSTREAM_REFRESH_REQUEST_DELAY_SECONDS", "1.0")),
            upstream_refresh_settle_seconds=int(os.getenv("BACKEND_UPSTREAM_REFRESH_SETTLE_SECONDS", "300")),
            upstream_base_url=os.getenv("BACKEND_UPSTREAM_BASE_URL", ""),
            upstream_username=os.getenv("BACKEND_UPSTREAM_USERNAME", ""),
            upstream_password=os.getenv("BACKEND_UPSTREAM_PASSWORD", ""),
            llm_enabled=_as_bool(os.getenv("BACKEND_LLM_ENABLED"), False),
            llm_base_url=os.getenv("BACKEND_LLM_BASE_URL", ""),
            llm_api_key=os.getenv("BACKEND_LLM_API_KEY", ""),
            llm_model=os.getenv("BACKEND_LLM_MODEL", ""),
            llm_timeout_seconds=int(os.getenv("BACKEND_LLM_TIMEOUT_SECONDS", "30")),
            llm_prompt_version=os.getenv("BACKEND_LLM_PROMPT_VERSION", "iter1-v1"),
            llm_max_input_chars=int(os.getenv("BACKEND_LLM_MAX_INPUT_CHARS", "6000")),
            llm_queue_enabled=_as_bool(os.getenv("BACKEND_LLM_QUEUE_ENABLED"), True),
            llm_worker_interval_seconds=int(os.getenv("BACKEND_LLM_WORKER_INTERVAL_SECONDS", "20")),
            llm_worker_batch_size=int(os.getenv("BACKEND_LLM_WORKER_BATCH_SIZE", "2")),
            llm_worker_max_attempts=int(os.getenv("BACKEND_LLM_WORKER_MAX_ATTEMPTS", "3")),
            content_worker_batch_size=int(os.getenv("BACKEND_CONTENT_WORKER_BATCH_SIZE", "5")),
            queue_recent_days=int(os.getenv("BACKEND_QUEUE_RECENT_DAYS", "30")),
            homepage_recent_undated_days=int(os.getenv("BACKEND_HOMEPAGE_RECENT_UNDATED_DAYS", "90")),
            ocr_enabled=_as_bool(os.getenv("BACKEND_OCR_ENABLED"), False),
            ocr_provider=os.getenv("BACKEND_OCR_PROVIDER", "tencent"),
            tencent_secret_id=os.getenv("BACKEND_TENCENT_SECRET_ID", ""),
            tencent_secret_key=os.getenv("BACKEND_TENCENT_SECRET_KEY", ""),
            tencent_ocr_region=os.getenv("BACKEND_TENCENT_OCR_REGION", "ap-guangzhou"),
            ocr_action=os.getenv("BACKEND_OCR_ACTION", "RecognizeAgent"),
            ocr_max_images_per_post=int(os.getenv("BACKEND_OCR_MAX_IMAGES_PER_POST", "8")),
            ocr_min_text_length=int(os.getenv("BACKEND_OCR_MIN_TEXT_LENGTH", "120")),
            ocr_timeout_seconds=int(os.getenv("BACKEND_OCR_TIMEOUT_SECONDS", "20")),
            ocr_monthly_limit=int(os.getenv("BACKEND_OCR_MONTHLY_LIMIT", "1000")),
            ocr_cache_enabled=_as_bool(os.getenv("BACKEND_OCR_CACHE_ENABLED"), True),
            ocr_count_failed_attempts=_as_bool(os.getenv("BACKEND_OCR_COUNT_FAILED_ATTEMPTS"), True),
        )
