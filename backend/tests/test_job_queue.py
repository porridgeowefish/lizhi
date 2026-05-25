from __future__ import annotations

import asyncio
from pathlib import Path

from fastapi.testclient import TestClient

from app.application.services.job_queue_service import JobQueueService
from app.core.config import Settings
from app.db.models import Post, Source
from app.db.session import build_session_factory
from app.domain.enums import ContentStatus, JobStatus, JobType, LlmStatus
from app.main import create_app
from app.workers.content_worker import ContentWorker
from app.workers.enqueue_refresh_jobs import enqueue_refresh_jobs
from app.workers.refresh_worker import RefreshWorker


class ContentConnector:
    async def fetch_post_detail(self, post_id: str) -> dict:
        return {
            "content": "<section>报名入口已经开放，截止时间为5月28日18:00。</section>",
        }


class DeletedContentConnector:
    async def fetch_post_detail(self, post_id: str) -> dict:
        return {"content": "DELETED"}


class MissingPostConnector:
    async def fetch_posts(self, source_id: str, limit: int) -> list[dict]:
        return [
            {
                "id": "P010",
                "title": "讲座报名通知",
                "description": "面向全校学生开放报名，截止5月28日18:00",
                "url": "https://example.com/p10",
                "publish_time": 1780000300,
                "content_html": "",
            }
        ]

    async def fetch_post_detail(self, post_id: str) -> dict:
        return {}


def build_settings(tmp_path: Path) -> Settings:
    return Settings(
        database_url=f"sqlite:///{(tmp_path / 'jobs.db').as_posix()}",
        enable_scheduler=False,
        llm_enabled=False,
        upstream_refresh_enabled=False,
    )


def seed_source_and_post(session_factory):
    db = session_factory()
    try:
        source = Source(upstream_source_id="SRC001", name="校园机会中心")
        db.add(source)
        db.flush()
        post = Post(
            upstream_post_id="P001",
            source_id=source.id,
            source_name_snapshot=source.name,
            title="讲座报名通知",
            summary="面向全校学生开放报名",
            original_url="https://example.com/p1",
            content_html="",
            content_text_snapshot="",
            content_status=ContentStatus.MISSING.value,
            content_hash="missing",
            llm_status=LlmStatus.NOT_REQUESTED.value,
        )
        db.add(post)
        db.commit()
        db.refresh(source)
        db.refresh(post)
        return source.id, post.id
    finally:
        db.close()


def test_job_queue_dedupes_and_retains_succeeded_jobs(tmp_path: Path):
    settings = build_settings(tmp_path)
    _, session_factory = build_session_factory(settings)
    queue = JobQueueService(session_factory)

    first = queue.enqueue(
        JobType.FETCH_CONTENT,
        "upstream:P001",
        {"upstream_post_id": "P001"},
    )
    second = queue.enqueue(
        JobType.FETCH_CONTENT,
        "upstream:P001",
        {"upstream_post_id": "P001"},
    )

    assert first.id == second.id
    assert queue.summary()["pending"] == 1

    claimed = queue.claim([JobType.FETCH_CONTENT], worker_id="test-worker", limit=1)
    assert [job.id for job in claimed] == [first.id]

    queue.mark_succeeded(first.id, {"ok": True})
    assert queue.get(first.id).status == JobStatus.SUCCEEDED.value
    assert queue.summary()["succeeded"] == 1


def test_refresh_job_api_enqueues_local_sources(tmp_path: Path):
    settings = build_settings(tmp_path)
    app = create_app(settings=settings, connector=ContentConnector())
    source_id, _ = seed_source_and_post(app.state.session_factory)
    client = TestClient(app)

    response = client.post("/api/jobs/refresh")
    response.raise_for_status()
    payload = response.json()

    assert payload["created"] == 1
    assert payload["jobs"][0]["job_type"] == JobType.REFRESH_SOURCE.value
    assert payload["jobs"][0]["payload"]["source_id"] == "SRC001"

    summary = client.get("/api/jobs/summary")
    summary.raise_for_status()
    assert summary.json()["pending"] == 1


def test_enqueue_refresh_jobs_worker_creates_refresh_jobs(tmp_path: Path):
    settings = build_settings(tmp_path)
    _, session_factory = build_session_factory(settings)
    seed_source_and_post(session_factory)

    result = enqueue_refresh_jobs(settings)

    assert result["jobs"] == 1
    queue = JobQueueService(session_factory)
    jobs = queue.list_recent(limit=5)
    assert jobs[0].job_type == JobType.REFRESH_SOURCE.value


def test_enqueue_refresh_jobs_skips_when_refresh_backlog_exists(tmp_path: Path):
    settings = build_settings(tmp_path)
    _, session_factory = build_session_factory(settings)
    seed_source_and_post(session_factory)
    queue = JobQueueService(session_factory)
    queue.enqueue(JobType.REFRESH_SOURCE, "source:SRC001:pages:0-10", {"source_id": "SRC001"})

    result = enqueue_refresh_jobs(settings)

    assert result["status"] == "skipped"
    assert queue.summary()["pending"] == 1


def test_content_worker_fetches_missing_content_and_enqueues_llm(tmp_path: Path):
    settings = build_settings(tmp_path)
    _, session_factory = build_session_factory(settings)
    _, post_id = seed_source_and_post(session_factory)
    queue = JobQueueService(session_factory)
    queue.enqueue(
        JobType.FETCH_CONTENT,
        "upstream:P001",
        {"upstream_post_id": "P001", "post_id": post_id},
    )

    worker = ContentWorker(session_factory, queue, ContentConnector(), settings, worker_id="content-test")
    result = asyncio.run(worker.run_once(limit=1))

    assert result["completed"] == 1
    db = session_factory()
    try:
        post = db.get(Post, post_id)
        assert post.content_status == ContentStatus.READY.value
        assert "报名入口已经开放" in post.content_text_snapshot
        jobs = queue.list_recent(limit=10)
        assert any(job.job_type == JobType.LLM_POST.value for job in jobs)
    finally:
        db.close()


def test_content_worker_does_not_mark_deleted_upstream_as_ready(tmp_path: Path):
    settings = build_settings(tmp_path)
    _, session_factory = build_session_factory(settings)
    _, post_id = seed_source_and_post(session_factory)
    queue = JobQueueService(session_factory)
    job = queue.enqueue(
        JobType.FETCH_CONTENT,
        "upstream:P001",
        {"upstream_post_id": "P001", "post_id": post_id},
        max_attempts=1,
    )

    worker = ContentWorker(session_factory, queue, DeletedContentConnector(), settings, worker_id="content-test")
    result = asyncio.run(worker.run_once(limit=1))

    assert result["failed"] == 1
    assert queue.get(job.id).status == JobStatus.DEAD.value
    db = session_factory()
    try:
        post = db.get(Post, post_id)
        assert post.content_status == ContentStatus.MISSING.value
    finally:
        db.close()


def test_refresh_worker_syncs_one_source_and_enqueues_content(tmp_path: Path):
    settings = build_settings(tmp_path)
    _, session_factory = build_session_factory(settings)
    source_id, _ = seed_source_and_post(session_factory)
    queue = JobQueueService(session_factory)
    queue.enqueue(
        JobType.SYNC_SOURCE_POSTS,
        "source:SRC001:limit:500",
        {"source_id": "SRC001", "limit": 500},
    )

    worker = RefreshWorker(session_factory, queue, MissingPostConnector(), settings, worker_id="refresh-test")
    result = asyncio.run(worker.run_once(limit=1))

    assert result["completed"] == 1
    jobs = queue.list_recent(limit=20)
    assert any(job.job_type == JobType.FETCH_CONTENT.value and "P010" in job.dedupe_key for job in jobs)
