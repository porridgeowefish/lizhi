from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
from pathlib import Path

from fastapi.testclient import TestClient

from app.api.serializers import serialize_post
from app.application.services.ocr_service import OcrService
from app.core.config import Settings
from app.db.models import Post, PostCategory, PostProjection, Source
from app.domain.enums import (
    ContentStatus,
    ContentType,
    DisplayLevel,
    LlmStatus,
    ParticipationStatus,
    SyncTriggerType,
    TimelinessLevel,
    TimeStatus,
)
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


class ImageOnlyConnector:
    async def fetch_sources(self, limit: int) -> list[dict]:
        return [{"id": "SRC_OCR", "mp_name": "校园机会中心"}]

    async def fetch_posts(self, source_id: str, limit: int) -> list[dict]:
        return [
            {
                "id": "P_OCR",
                "title": "图片推文",
                "description": "",
                "url": "https://example.com/ocr",
                "publish_time": 1780000400,
                "content_html": '<section><img data-src="https://example.com/ocr.jpg" /></section>',
            }
        ]


class StubOcrClient:
    def __init__(self, text: str):
        self.text = text

    def recognize_image_url(self, image_url: str) -> str:
        return self.text


def build_test_client(tmp_path: Path) -> TestClient:
    settings = Settings(
        database_url=f"sqlite:///{(tmp_path / 'test.db').as_posix()}",
        enable_scheduler=False,
        llm_enabled=False,
    )
    app = create_app(settings=settings, connector=StubConnector())
    asyncio.run(app.state.ingestion_service.run_sync(SyncTriggerType.MANUAL))
    return TestClient(app)


def build_empty_test_client(tmp_path: Path) -> TestClient:
    return TestClient(build_empty_test_app(tmp_path))


def build_empty_test_app(tmp_path: Path):
    settings = Settings(
        database_url=f"sqlite:///{(tmp_path / 'empty.db').as_posix()}",
        enable_scheduler=False,
        llm_enabled=False,
    )
    return create_app(settings=settings, connector=None)


def insert_sorting_post(
    db,
    source: Source,
    upstream_id: str,
    title: str,
    deadline_at: datetime | None,
    published_at: datetime,
    *,
    event_start_at: datetime | None = None,
    event_end_at: datetime | None = None,
):
    post = Post(
        upstream_post_id=upstream_id,
        source_id=source.id,
        source_name_snapshot=source.name,
        title=title,
        summary=title,
        original_url=f"https://example.com/{upstream_id}",
        published_at=published_at,
        content_hash=upstream_id,
        content_status="ready",
    )
    db.add(post)
    db.flush()
    db.add(PostCategory(post_id=post.id, category_code="competition", category_source="test"))
    time_status = TimeStatus.UNDATED if deadline_at is None and event_start_at is None else TimeStatus.UPCOMING
    db.add(
        PostProjection(
            post_id=post.id,
            primary_category="competition",
            content_type=ContentType.ACTIONABLE.value,
            event_start_at=event_start_at,
            event_end_at=event_end_at,
            deadline_at=deadline_at,
            time_status=time_status.value,
            timeliness_level=TimelinessLevel.NORMAL.value,
            participation_status=ParticipationStatus.PARTICIPABLE.value,
            display_level=DisplayLevel.NORMAL.value,
            ranking_score=0,
        )
    )
    return post


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


def test_sync_appends_ocr_text_for_image_only_posts(tmp_path: Path):
    settings = Settings(
        database_url=f"sqlite:///{(tmp_path / 'ocr.db').as_posix()}",
        enable_scheduler=False,
        llm_enabled=False,
        ocr_enabled=True,
        ocr_min_text_length=20,
    )
    app = create_app(settings=settings, connector=ImageOnlyConnector())
    app.state.ingestion_service.ocr_service = OcrService(
        settings,
        client=StubOcrClient("志愿者招募活动 报名入口开放"),
    )
    asyncio.run(app.state.ingestion_service.run_sync(SyncTriggerType.MANUAL))

    db = app.state.session_factory()
    try:
        items, total = app.state.query_service.list_posts(db, search="志愿者", limit=10)
        assert total == 1
        payload = serialize_post(items[0])
        assert payload.primary_category == "volunteer"
        assert "volunteer" in payload.categories
        assert "志愿者招募" in items[0].content_text_snapshot
    finally:
        db.close()


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


def test_posts_search_matches_title_summary_and_content(tmp_path: Path):
    app = build_empty_test_app(tmp_path)
    db = app.state.session_factory()
    try:
        source = Source(upstream_source_id="SEARCH_SRC", name="Search Source")
        db.add(source)
        db.flush()
        now = datetime.now(timezone.utc)
        cases = [
            ("title-hit", "AI 校园讲座", "普通摘要", "普通正文"),
            ("summary-hit", "摘要命中文章", "AI 报名说明", "普通正文"),
            ("content-hit", "正文命中文章", "普通摘要", "正文包含 AI 工作坊安排"),
            ("miss", "未命中文章", "普通摘要", "普通正文"),
        ]
        for upstream_id, title, summary, content_text in cases:
            post = insert_sorting_post(db, source, upstream_id, title, None, now - timedelta(minutes=1))
            post.summary = summary
            post.content_text_snapshot = content_text
        db.commit()

        items, total = app.state.query_service.list_posts(db, search="AI", show_all=True, limit=2)
        assert total == 3
        assert len(items) == 2

        all_items, all_total = app.state.query_service.list_posts(db, search="AI", show_all=True, limit=10)
        assert all_total == 3
        assert {item.title for item in all_items} == {"AI 校园讲座", "摘要命中文章", "正文命中文章"}
    finally:
        db.close()


def test_category_filter_matches_projection_primary_category(tmp_path: Path):
    app = build_empty_test_app(tmp_path)
    db = app.state.session_factory()
    try:
        source = Source(upstream_source_id="PRIMARY_CATEGORY_SRC", name="Primary Category Source")
        db.add(source)
        db.flush()
        now = datetime.now(timezone.utc)
        post = insert_sorting_post(db, source, "primary-category-hit", "社团招新", None, now)
        db.flush()
        db.refresh(post, attribute_names=["projection", "categories"])
        post.projection.primary_category = "campus_activity"
        post.categories[0].category_code = "other"
        db.commit()

        items, total = app.state.query_service.list_posts(
            db,
            category="campus_activity",
            show_all=True,
            limit=10,
        )
        assert total == 1
        assert [item.id for item in items] == [post.id]
    finally:
        db.close()


def test_post_payload_keeps_primary_category_in_categories(tmp_path: Path):
    app = build_empty_test_app(tmp_path)
    db = app.state.session_factory()
    try:
        source = Source(upstream_source_id="PAYLOAD_CATEGORY_SRC", name="Payload Category Source")
        db.add(source)
        db.flush()
        now = datetime.now(timezone.utc)
        post = insert_sorting_post(db, source, "payload-category", "社团招新", None, now)
        db.flush()
        db.refresh(post, attribute_names=["projection", "categories"])
        post.projection.primary_category = "campus_activity"
        post.categories[0].category_code = "other"
        db.commit()

        items, total = app.state.query_service.list_posts(
            db,
            category="campus_activity",
            show_all=True,
            limit=10,
        )
        assert total == 1
        item = serialize_post(items[0]).model_dump()
        assert item["primary_category"] == "campus_activity"
        assert "campus_activity" in item["categories"]
    finally:
        db.close()


def test_tag_category_becomes_effective_primary_category(tmp_path: Path):
    app = build_empty_test_app(tmp_path)
    db = app.state.session_factory()
    try:
        source = Source(upstream_source_id="TAG_CATEGORY_SRC", name="Tag Category Source")
        db.add(source)
        db.flush()
        now = datetime.now(timezone.utc)
        post = insert_sorting_post(db, source, "tag-category", "志愿者招募", None, now)
        db.flush()
        db.refresh(post, attribute_names=["projection", "categories"])
        post.projection.primary_category = "other"
        post.categories[0].category_code = "volunteer"
        db.commit()

        items, total = app.state.query_service.list_posts(
            db,
            category="volunteer",
            show_all=True,
            limit=10,
        )
        assert total == 1
        assert [item.id for item in items] == [post.id]

        payload = serialize_post(items[0]).model_dump()
        assert payload["primary_category"] == "volunteer"
        assert payload["categories"] == ["volunteer"]

        category_stats, *_ = app.state.query_service.get_category_stats(db)
        assert {"category": "volunteer", "count": 1} in category_stats
    finally:
        db.close()


def test_posts_deadline_sort_uses_nearest_key_time(tmp_path: Path):
    client = build_empty_test_client(tmp_path)
    db = client.app.state.session_factory()
    try:
        source = Source(upstream_source_id="SORT_SRC", name="Sort Source")
        db.add(source)
        db.flush()
        now = datetime.now(timezone.utc)
        insert_sorting_post(
            db,
            source,
            "expired-older",
            "Expired older event",
            None,
            now - timedelta(minutes=1),
            event_start_at=now - timedelta(days=5),
        )
        insert_sorting_post(
            db,
            source,
            "expired-recent",
            "Expired recent deadline",
            now - timedelta(days=1),
            now - timedelta(minutes=2),
            event_start_at=now - timedelta(days=2),
        )
        insert_sorting_post(db, source, "undated-new", "No key time new", None, now - timedelta(minutes=3))
        insert_sorting_post(db, source, "undated-old", "No key time old", None, now - timedelta(minutes=4))
        insert_sorting_post(
            db,
            source,
            "deadline-three",
            "Deadline in three days",
            now + timedelta(days=3),
            now - timedelta(minutes=5),
        )
        insert_sorting_post(
            db,
            source,
            "event-two",
            "Event in two days",
            None,
            now - timedelta(minutes=6),
            event_start_at=now + timedelta(days=2),
            event_end_at=now + timedelta(hours=6),
        )
        insert_sorting_post(
            db,
            source,
            "both-start-one",
            "Both times choose event",
            now + timedelta(days=5),
            now - timedelta(minutes=7),
            event_start_at=now + timedelta(days=1),
            event_end_at=now + timedelta(hours=2),
        )
        db.commit()
    finally:
        db.close()

    response = client.get("/api/posts", params={"sort": "deadline", "limit": 10, "show_all": True})
    response.raise_for_status()
    payload = response.json()

    assert payload["total"] == 7
    assert [item["title"] for item in payload["items"]] == [
        "Both times choose event",
        "Event in two days",
        "Deadline in three days",
        "No key time old",
        "No key time new",
        "Expired recent deadline",
        "Expired older event",
    ]
    assert [item["key_time_type"] for item in payload["items"]] == [
        "event_start",
        "event_start",
        "deadline",
        "none",
        "none",
        "deadline",
        "event_start",
    ]
    assert payload["items"][0]["key_time_at"] == payload["items"][0]["event_start_at"]
    assert payload["items"][1]["key_time_at"] == payload["items"][1]["event_start_at"]
    assert payload["items"][2]["key_time_at"] == payload["items"][2]["deadline_at"]


def test_posts_hide_pre_2022_content_by_default(tmp_path: Path):
    client = build_empty_test_client(tmp_path)
    db = client.app.state.session_factory()
    try:
        source = Source(upstream_source_id="CUTOFF_SRC", name="Cutoff Source")
        db.add(source)
        db.flush()
        insert_sorting_post(
            db,
            source,
            "old-post",
            "Old hidden post",
            None,
            datetime(2021, 12, 31, tzinfo=timezone.utc),
        )
        insert_sorting_post(
            db,
            source,
            "new-post",
            "New visible post",
            None,
            datetime.now(timezone.utc),
        )
        db.commit()
    finally:
        db.close()

    response = client.get("/api/posts", params={"sort": "deadline", "limit": 10})
    response.raise_for_status()
    payload = response.json()

    assert payload["total"] == 1
    assert [item["title"] for item in payload["items"]] == ["New visible post"]

    show_all = client.get("/api/posts", params={"show_all": True, "sort": "deadline", "limit": 10})
    show_all.raise_for_status()
    assert show_all.json()["total"] == 2


def test_posts_default_scope_keeps_future_key_time_and_recent_undated(tmp_path: Path):
    client = build_empty_test_client(tmp_path)
    db = client.app.state.session_factory()
    try:
        source = Source(upstream_source_id="SCOPE_SRC", name="Scope Source")
        db.add(source)
        db.flush()
        now = datetime.now(timezone.utc)
        insert_sorting_post(
            db,
            source,
            "future-deadline",
            "Future deadline",
            now + timedelta(days=3),
            now - timedelta(days=200),
        )
        insert_sorting_post(
            db,
            source,
            "recent-undated",
            "Recent undated",
            None,
            now - timedelta(days=10),
        )
        insert_sorting_post(
            db,
            source,
            "old-undated",
            "Old undated",
            None,
            now - timedelta(days=200),
        )
        insert_sorting_post(
            db,
            source,
            "expired-key-time",
            "Expired key time",
            now - timedelta(days=1),
            now - timedelta(days=1),
        )
        db.commit()
    finally:
        db.close()

    response = client.get("/api/posts", params={"sort": "deadline", "limit": 10})
    response.raise_for_status()
    payload = response.json()

    assert payload["total"] == 2
    assert [item["title"] for item in payload["items"]] == ["Future deadline", "Recent undated"]

    show_all = client.get("/api/posts", params={"show_all": True, "sort": "deadline", "limit": 10})
    show_all.raise_for_status()
    assert show_all.json()["total"] == 4


def test_sync_job_reports_discard_counts(tmp_path: Path):
    client = build_test_client(tmp_path)
    response = client.post("/api/sync")
    response.raise_for_status()
    payload = response.json()
    assert payload["posts_discarded"] >= 1
    assert payload["discarded_count"] == payload["posts_discarded"]
    assert "recap" in payload["discard_stats_by_reason"] or "garbled_hidden_source" in payload["discard_stats_by_reason"]


def test_category_stats_include_new_dimensions(tmp_path: Path):
    client = build_test_client(tmp_path)
    response = client.get("/api/posts/categories")
    response.raise_for_status()
    payload = response.json()
    assert "participation_stats" in payload
    assert "time_status_stats" in payload
    assert "time_unknown_breakdown" in payload


def test_category_stats_breaks_down_undated_reasons(tmp_path: Path):
    client = build_empty_test_client(tmp_path)
    db = client.app.state.session_factory()
    try:
        source = Source(upstream_source_id="UNDATED_SRC", name="Undated Source")
        db.add(source)
        db.flush()
        now = datetime.now(timezone.utc)
        rows = [
            ("missing", ContentStatus.MISSING.value, LlmStatus.NOT_REQUESTED.value),
            ("waiting", ContentStatus.READY.value, LlmStatus.PENDING.value),
            ("failed", ContentStatus.READY.value, LlmStatus.FAILED.value),
            ("processed", ContentStatus.READY.value, LlmStatus.COMPLETED.value),
        ]
        for upstream_id, content_status, llm_status in rows:
            post = insert_sorting_post(
                db,
                source,
                upstream_id,
                f"Undated {upstream_id}",
                None,
                now - timedelta(minutes=1),
            )
            post.content_status = content_status
            post.llm_status = llm_status
        db.commit()
    finally:
        db.close()

    response = client.get("/api/posts/categories")
    response.raise_for_status()
    payload = response.json()

    assert payload["time_status_stats"]["undated"] == 4
    assert payload["time_unknown_breakdown"] == {
        "content_missing": 1,
        "llm_failed": 1,
        "llm_waiting": 1,
        "processed_no_time": 1,
    }


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
