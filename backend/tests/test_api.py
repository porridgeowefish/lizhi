from __future__ import annotations

import asyncio
from pathlib import Path

from fastapi.testclient import TestClient

from app.core.config import Settings
from app.domain.enums import SyncTriggerType
from app.main import create_app


class StubConnector:
    async def fetch_sources(self, limit: int) -> list[dict]:
        return [
            {
                "id": "SRC001",
                "mp_name": "深圳大学学生会",
                "mp_cover": "https://example.com/cover.png",
                "mp_intro": "校园活动来源",
            }
        ]

    async def fetch_articles(self, source_id: str, limit: int) -> list[dict]:
        return [
            {
                "id": "A001",
                "title": "讲座报名通知",
                "description": "面向全校学生开放报名",
                "url": "https://example.com/a1",
                "pic_url": "https://example.com/a1.png",
                "publish_time": 1710000000,
                "content_html": "<p>报名入口</p>",
            },
            {
                "id": "A002",
                "title": "活动回顾",
                "description": "精彩回顾与总结",
                "url": "https://example.com/a2",
                "pic_url": "https://example.com/a2.png",
                "publish_time": 1710000100,
                "content_html": "<p>回顾内容</p>",
            },
        ]


def build_test_client(tmp_path: Path) -> TestClient:
    settings = Settings(
        database_url=f"sqlite:///{(tmp_path / 'test.db').as_posix()}",
        enable_scheduler=False,
    )
    app = create_app(settings=settings, connector=StubConnector())
    asyncio.run(app.state.ingestion_service.run_sync(SyncTriggerType.MANUAL))
    return TestClient(app)


def test_articles_hide_hidden_by_default(tmp_path: Path):
    client = build_test_client(tmp_path)
    response = client.get("/api/articles")
    response.raise_for_status()
    payload = response.json()
    assert payload["total"] == 1
    assert payload["items"][0]["title"] == "讲座报名通知"


def test_articles_show_all_and_search_summary(tmp_path: Path):
    client = build_test_client(tmp_path)
    response = client.get("/api/articles", params={"show_all": "true", "search": "精彩回顾"})
    response.raise_for_status()
    payload = response.json()
    assert payload["total"] == 1
    assert payload["items"][0]["title"] == "活动回顾"


def test_sync_job_endpoint_returns_items(tmp_path: Path):
    client = build_test_client(tmp_path)
    response = client.post("/api/sync")
    response.raise_for_status()
    payload = response.json()
    job_id = payload["id"]
    detail = client.get(f"/api/sync/jobs/{job_id}")
    detail.raise_for_status()
    detail_payload = detail.json()
    assert detail_payload["status"] in {"completed", "partial_failed"}
    assert len(detail_payload["items"]) >= 1
