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
                "mp_name": "校园机会中心",
                "mp_cover": "https://example.com/cover.png",
                "mp_intro": "校园机会来源",
            }
        ]

    async def fetch_posts(self, source_id: str, limit: int) -> list[dict]:
        return [
            {
                "id": "P001",
                "title": "讲座报名通知",
                "description": "面向全校学生开放报名，截止5月28日18:00",
                "url": "https://example.com/p1",
                "pic_url": "https://example.com/p1.png",
                "publish_time": 1780000000,
                "content_html": "<p>报名入口已经开放，截止5月28日18:00</p>",
            },
            {
                "id": "P002",
                "title": "活动精彩回顾",
                "description": "让我们一起回顾本次活动精彩瞬间",
                "url": "https://example.com/p2",
                "pic_url": "https://example.com/p2.png",
                "publish_time": 1780000100,
                "content_html": "<p>活动现场气氛热烈</p>",
            },
            {
                "id": "P003",
                "title": "锟斤拷锟斤拷@@",
                "description": "",
                "url": "https://example.com/p3",
                "pic_url": "https://example.com/p3.png",
                "publish_time": 1780000200,
                "content_html": "<p>@@@</p>",
            },
        ]


class DetailContentConnector:
    async def fetch_sources(self, limit: int) -> list[dict]:
        return [{"id": "SRC002", "mp_name": "校园机会中心"}]

    async def fetch_posts(self, source_id: str, limit: int) -> list[dict]:
        return [
            {
                "id": "P004",
                "title": "讲座报名通知",
                "description": "面向全校学生开放报名，截止5月28日18:00",
                "url": "https://example.com/p4",
                "publish_time": 1780000300,
                "content_html": "",
            }
        ]

    async def fetch_post_detail(self, post_id: str) -> dict:
        return {"content_html": "", "content": "<section>报名入口已经开放，截止5月28日18:00</section>"}


def build_test_client(tmp_path: Path) -> TestClient:
    settings = Settings(
        database_url=f"sqlite:///{(tmp_path / 'test.db').as_posix()}",
        enable_scheduler=False,
        llm_enabled=False,
    )
    app = create_app(settings=settings, connector=StubConnector())
    asyncio.run(app.state.ingestion_service.run_sync(SyncTriggerType.MANUAL))
    return TestClient(app)


def test_sync_uses_detail_content_fallback(tmp_path: Path):
    settings = Settings(
        database_url=f"sqlite:///{(tmp_path / 'detail.db').as_posix()}",
        enable_scheduler=False,
        llm_enabled=False,
    )
    app = create_app(settings=settings, connector=DetailContentConnector())
    asyncio.run(app.state.ingestion_service.run_sync(SyncTriggerType.MANUAL))
    client = TestClient(app)

    payload = client.get("/api/posts").json()
    assert payload["total"] == 1
    post_id = payload["items"][0]["id"]
    detail = client.get(f"/api/posts/{post_id}")
    detail.raise_for_status()
    assert "报名入口已经开放" in detail.json()["content_html"]


def test_posts_hide_prescreened_by_default(tmp_path: Path):
    client = build_test_client(tmp_path)
    response = client.get("/api/posts")
    response.raise_for_status()
    payload = response.json()
    assert payload["total"] == 1
    assert payload["items"][0]["title"] == "讲座报名通知"
    assert payload["items"][0]["participation_status"] == "participable"


def test_posts_search_and_detail(tmp_path: Path):
    client = build_test_client(tmp_path)
    response = client.get("/api/posts", params={"search": "讲座"})
    response.raise_for_status()
    payload = response.json()
    assert payload["total"] == 1
    post_id = payload["items"][0]["id"]

    detail = client.get(f"/api/posts/{post_id}")
    detail.raise_for_status()
    detail_payload = detail.json()
    assert detail_payload["content_html"]
    assert detail_payload["time_status"] in {"upcoming", "undated"}


def test_sync_job_reports_discard_counts(tmp_path: Path):
    client = build_test_client(tmp_path)
    response = client.post("/api/sync")
    response.raise_for_status()
    payload = response.json()
    assert payload["posts_discarded"] >= 2
    assert payload["discarded_count"] == payload["posts_discarded"]
    assert "recap" in payload["discard_stats_by_reason"] or "garbled_hidden_source" in payload["discard_stats_by_reason"]


def test_category_stats_include_new_dimensions(tmp_path: Path):
    client = build_test_client(tmp_path)
    response = client.get("/api/posts/categories")
    response.raise_for_status()
    payload = response.json()
    assert "participation_stats" in payload
    assert "time_status_stats" in payload


def test_support_click_is_counted_once_per_client(tmp_path: Path):
    client = build_test_client(tmp_path)
    client_id = "test-client-001"

    first = client.post("/api/support", json={"client_id": client_id})
    first.raise_for_status()
    assert first.json() == {"count": 1, "liked": True, "incremented": True}

    second = client.post("/api/support", json={"client_id": client_id})
    second.raise_for_status()
    assert second.json() == {"count": 1, "liked": True, "incremented": False}

    stats = client.get("/api/support", params={"client_id": client_id})
    stats.raise_for_status()
    assert stats.json() == {"count": 1, "liked": True, "incremented": False}
