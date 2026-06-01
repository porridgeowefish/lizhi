from __future__ import annotations

from app.application.services.ocr_service import (
    OCR_TEXT_MARKER,
    OCR_STATUS_FAILED,
    OCR_STATUS_SKIPPED_LIMIT,
    OCR_STATUS_SUCCESS,
    OcrService,
    _extract_recognize_agent_lines,
    append_ocr_text,
    extract_image_urls_from_raw_post,
)
from app.core.config import Settings
from app.db.models import OcrImageCache, OcrUsageLog
from app.db.session import build_session_factory


class StubOcrClient:
    def __init__(self, text_by_url: dict[str, str]):
        self.text_by_url = text_by_url
        self.urls: list[str] = []

    def recognize_image_url(self, image_url: str) -> str:
        self.urls.append(image_url)
        return self.text_by_url.get(image_url, "")


class FailingOcrClient:
    def __init__(self):
        self.urls: list[str] = []

    def recognize_image_url(self, image_url: str) -> str:
        self.urls.append(image_url)
        raise RuntimeError("provider failed")


def test_extract_image_urls_from_wechat_html():
    raw_post = {
        "url": "https://mp.weixin.qq.com/s/test",
        "content_html": """
        <section>
          <img data-src="//mmbiz.qpic.cn/mmbiz_png/a/0?wx_fmt=png" />
          <img src="https://example.com/static/post.jpg" />
          <img src="data:image/png;base64,abc" />
        </section>
        """,
    }

    urls = extract_image_urls_from_raw_post(raw_post)

    assert urls == [
        "https://mmbiz.qpic.cn/mmbiz_png/a/0?wx_fmt=png",
        "https://example.com/static/post.jpg",
    ]


def test_ocr_service_appends_text_only_for_short_image_posts():
    settings = Settings(ocr_enabled=True, ocr_min_text_length=20, ocr_max_images_per_post=1)
    image_url = "https://example.com/post.jpg"
    client = StubOcrClient({image_url: "志愿者招募 报名入口"})
    service = OcrService(settings, client=client)
    raw_post = {"content_html": f'<section><img src="{image_url}" /></section>'}

    result = service.maybe_append_ocr_text(raw_post, "短文")

    assert client.urls == [image_url]
    assert result.processed_count == 1
    assert OCR_TEXT_MARKER in result.content_text
    assert "志愿者招募" in result.content_text


def test_ocr_service_skips_long_text_even_with_images():
    settings = Settings(ocr_enabled=True, ocr_min_text_length=5)
    client = StubOcrClient({"https://example.com/post.jpg": "不应调用"})
    service = OcrService(settings, client=client)
    raw_post = {"content_html": '<img src="https://example.com/post.jpg" />'}

    result = service.maybe_append_ocr_text(raw_post, "这是一段足够长的正文")

    assert client.urls == []
    assert result.content_text == "这是一段足够长的正文"


def test_append_ocr_text_keeps_source_marker():
    content_text = append_ocr_text("", "讲座论坛 报名方式")

    assert content_text.startswith(OCR_TEXT_MARKER)
    assert "讲座论坛" in content_text


def test_ocr_service_reuses_cached_image_text(tmp_path):
    settings = Settings(
        database_url=f"sqlite:///{(tmp_path / 'ocr-cache.db').as_posix()}",
        ocr_enabled=True,
        ocr_min_text_length=20,
    )
    _, session_factory = build_session_factory(settings)
    image_url = "https://example.com/post.jpg"
    raw_post = {"id": "P001", "content_html": f'<img src="{image_url}" />'}

    first_client = StubOcrClient({image_url: "社团招新报名"})
    first_service = OcrService(settings, client=first_client, session_factory=session_factory)
    first = first_service.maybe_append_ocr_text(raw_post, "")

    second_client = StubOcrClient({image_url: "不应再次调用"})
    second_service = OcrService(settings, client=second_client, session_factory=session_factory)
    second = second_service.maybe_append_ocr_text(raw_post, "")

    assert first_client.urls == [image_url]
    assert second_client.urls == []
    assert "社团招新报名" in first.content_text
    assert "社团招新报名" in second.content_text

    db = session_factory()
    try:
        assert db.query(OcrImageCache).count() == 1
        assert db.query(OcrUsageLog).count() == 1
        assert db.query(OcrImageCache).one().status == OCR_STATUS_SUCCESS
    finally:
        db.close()


def test_ocr_service_monthly_limit_skips_extra_images_without_text_warning(tmp_path):
    settings = Settings(
        database_url=f"sqlite:///{(tmp_path / 'ocr-limit.db').as_posix()}",
        ocr_enabled=True,
        ocr_min_text_length=20,
        ocr_max_images_per_post=2,
        ocr_monthly_limit=1,
    )
    _, session_factory = build_session_factory(settings)
    first_url = "https://example.com/one.jpg"
    second_url = "https://example.com/two.jpg"
    raw_post = {"content_html": f'<img src="{first_url}" /><img src="{second_url}" />'}
    client = StubOcrClient({first_url: "第一张图文字", second_url: "第二张图文字"})
    service = OcrService(settings, client=client, session_factory=session_factory)

    result = service.maybe_append_ocr_text(raw_post, "")

    assert client.urls == [first_url]
    assert "第一张图文字" in result.content_text
    assert "第二张图文字" not in result.content_text
    assert "monthly OCR limit reached" not in result.content_text
    assert OCR_STATUS_SKIPPED_LIMIT not in result.content_text

    db = session_factory()
    try:
        assert db.query(OcrUsageLog).count() == 1
        statuses = sorted(row.status for row in db.query(OcrImageCache).all())
        assert statuses == [OCR_STATUS_SKIPPED_LIMIT, OCR_STATUS_SUCCESS]
    finally:
        db.close()


def test_ocr_service_failed_attempt_can_consume_monthly_limit_without_error_text(tmp_path):
    settings = Settings(
        database_url=f"sqlite:///{(tmp_path / 'ocr-fail.db').as_posix()}",
        ocr_enabled=True,
        ocr_min_text_length=20,
        ocr_max_images_per_post=2,
        ocr_monthly_limit=1,
        ocr_count_failed_attempts=True,
    )
    _, session_factory = build_session_factory(settings)
    first_url = "https://example.com/one.jpg"
    second_url = "https://example.com/two.jpg"
    raw_post = {"content_html": f'<img src="{first_url}" /><img src="{second_url}" />'}
    client = FailingOcrClient()
    service = OcrService(settings, client=client, session_factory=session_factory)

    result = service.maybe_append_ocr_text(raw_post, "")

    assert client.urls == [first_url]
    assert result.content_text == ""
    assert "provider failed" not in result.content_text

    db = session_factory()
    try:
        assert db.query(OcrUsageLog).count() == 1
        statuses = sorted(row.status for row in db.query(OcrImageCache).all())
        assert statuses == [OCR_STATUS_FAILED, OCR_STATUS_SKIPPED_LIMIT]
    finally:
        db.close()


def test_ocr_service_blocks_unsupported_action(tmp_path):
    settings = Settings(
        database_url=f"sqlite:///{(tmp_path / 'ocr-action.db').as_posix()}",
        ocr_enabled=True,
        ocr_action="GeneralBasicOCR",
        ocr_min_text_length=20,
    )
    _, session_factory = build_session_factory(settings)
    image_url = "https://example.com/post.jpg"
    client = StubOcrClient({image_url: "不应调用"})
    service = OcrService(settings, client=client, session_factory=session_factory)

    result = service.maybe_append_ocr_text({"content_html": f'<img src="{image_url}" />'}, "")

    assert client.urls == []
    assert result.content_text == ""


def test_recognize_agent_response_parser_extracts_full_text_lines():
    payload = {
        "Response": [
            {
                "TextDetections": [
                    {"DetectedText": "舞台招募"},
                    {"DetectedText": "截止日期：2026.3.20"},
                ]
            }
        ],
        "RequestId": "test",
    }

    assert _extract_recognize_agent_lines(payload) == ["舞台招募", "截止日期：2026.3.20"]
