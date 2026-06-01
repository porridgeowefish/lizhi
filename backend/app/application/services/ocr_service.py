from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import datetime
from hashlib import sha256
from html import unescape
from html.parser import HTMLParser
from typing import Protocol
from urllib.parse import urljoin, urlparse
from zoneinfo import ZoneInfo

from sqlalchemy import func
from sqlalchemy.orm import Session, sessionmaker

from app.application.classification import normalize_whitespace
from app.core.config import Settings
from app.db.models import OcrImageCache, OcrUsageLog

_logger = logging.getLogger(__name__)

OCR_TEXT_MARKER = "[OCR_TEXT]"
IMAGE_SRC_ATTRS = ("data-src", "src", "data-original", "data-lazy-src", "data-croporisrc")
OCR_ACTION_RECOGNIZE_AGENT = "RecognizeAgent"
OCR_ACTION_GENERAL_ACCURATE = "GeneralAccurateOCR"
SUPPORTED_OCR_ACTIONS = {OCR_ACTION_RECOGNIZE_AGENT, OCR_ACTION_GENERAL_ACCURATE}
OCR_STATUS_SUCCESS = "success"
OCR_STATUS_FAILED = "failed"
OCR_STATUS_SKIPPED_LIMIT = "skipped_limit"


class OcrClient(Protocol):
    def recognize_image_url(self, image_url: str, *, action: str | None = None) -> str:
        """Return OCR text for one remotely accessible image URL."""


@dataclass(slots=True)
class OcrAppendResult:
    content_text: str
    image_count: int = 0
    processed_count: int = 0
    ocr_text: str = ""


class _ImageUrlParser(HTMLParser):
    def __init__(self, base_url: str = ""):
        super().__init__(convert_charrefs=True)
        self.base_url = base_url
        self.urls: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() != "img":
            return
        attr_map = {name.lower(): value for name, value in attrs if name and value}
        for attr_name in IMAGE_SRC_ATTRS:
            url = _normalize_image_url(attr_map.get(attr_name, ""), self.base_url)
            if url:
                self.urls.append(url)
                return


def _normalize_image_url(value: str, base_url: str = "") -> str:
    raw = unescape((value or "").strip())
    if not raw or raw.startswith("data:"):
        return ""
    if raw.startswith("//"):
        raw = f"https:{raw}"
    elif base_url:
        raw = urljoin(base_url, raw)
    parsed = urlparse(raw)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return ""
    return raw


def extract_image_urls_from_html(content_html: str, *, base_url: str = "") -> list[str]:
    parser = _ImageUrlParser(base_url=base_url)
    try:
        parser.feed(content_html or "")
    except Exception as exc:  # noqa: BLE001
        _logger.warning("image url parse failed: %s", exc)
        return []
    return list(dict.fromkeys(parser.urls))


def extract_image_urls_from_raw_post(raw_post: dict) -> list[str]:
    base_url = str(raw_post.get("url") or "")
    urls: list[str] = []
    for field in ("content_html", "content"):
        value = str(raw_post.get(field) or "")
        if value:
            urls.extend(extract_image_urls_from_html(value, base_url=base_url))
    return list(dict.fromkeys(urls))


def append_ocr_text(content_text: str, ocr_text: str) -> str:
    normalized_ocr = normalize_whitespace(ocr_text)
    if not normalized_ocr:
        return content_text
    base = normalize_whitespace(content_text)
    if not base:
        return f"{OCR_TEXT_MARKER}\n{normalized_ocr}"
    return f"{base}\n\n{OCR_TEXT_MARKER}\n{normalized_ocr}"


def hash_image_url(image_url: str) -> str:
    return sha256(image_url.strip().encode("utf-8")).hexdigest()


def current_ocr_month_key() -> str:
    return datetime.now(ZoneInfo("Asia/Shanghai")).strftime("%Y-%m")


def _extract_recognize_agent_lines(payload: dict) -> list[str]:
    response_items = payload.get("Response") or []
    if isinstance(response_items, dict):
        response_items = response_items.get("Response") or []
    lines: list[str] = []
    for item in response_items:
        if not isinstance(item, dict):
            continue
        answer = str(item.get("Answer") or "").strip()
        if answer:
            lines.append(answer)
        for detection in item.get("TextDetections") or []:
            if isinstance(detection, dict):
                detected = str(detection.get("DetectedText") or "").strip()
                if detected:
                    lines.append(detected)
    return lines


def _extract_text_detection_lines(payload: dict) -> list[str]:
    detections = payload.get("TextDetections") or payload.get("Response", {}).get("TextDetections") or []
    lines: list[str] = []
    for item in detections:
        if not isinstance(item, dict):
            continue
        detected = str(item.get("DetectedText") or "").strip()
        if detected:
            lines.append(detected)
    return lines


class TencentCloudOcrClient:
    def __init__(self, settings: Settings):
        if not settings.tencent_secret_id or not settings.tencent_secret_key:
            raise RuntimeError("Tencent OCR credentials are not configured")
        self.settings = settings
        self._client = None
        self._models = None

    def _get_client(self):
        if self._client is not None:
            return self._client, self._models

        try:
            from tencentcloud.common import credential
            from tencentcloud.common.profile.client_profile import ClientProfile
            from tencentcloud.common.profile.http_profile import HttpProfile
            from tencentcloud.ocr.v20181119 import models, ocr_client
        except ImportError as exc:
            raise RuntimeError("tencentcloud-sdk-python is required when OCR is enabled") from exc

        cred = credential.Credential(self.settings.tencent_secret_id, self.settings.tencent_secret_key)
        http_profile = HttpProfile()
        http_profile.endpoint = "ocr.tencentcloudapi.com"
        if self.settings.ocr_timeout_seconds > 0:
            http_profile.reqTimeout = self.settings.ocr_timeout_seconds
        client_profile = ClientProfile()
        client_profile.httpProfile = http_profile
        self._client = ocr_client.OcrClient(cred, self.settings.tencent_ocr_region, client_profile)
        self._models = models
        return self._client, self._models

    def recognize_image_url(self, image_url: str, *, action: str | None = None) -> str:
        action = normalize_whitespace(action or self.settings.ocr_action) or OCR_ACTION_RECOGNIZE_AGENT
        if action not in SUPPORTED_OCR_ACTIONS:
            raise RuntimeError(f"Unsupported Tencent OCR action: {action}")
        client, models = self._get_client()
        if action == OCR_ACTION_RECOGNIZE_AGENT:
            request = models.RecognizeAgentRequest()
            request.from_json_string(json.dumps({"ImageUrl": image_url, "QueryType": 0}, ensure_ascii=False))
            response = client.RecognizeAgent(request)
            payload = json.loads(response.to_json_string())
            lines = _extract_recognize_agent_lines(payload)
            return normalize_whitespace(" ".join(line for line in lines if line))

        request = models.GeneralAccurateOCRRequest()
        request.from_json_string(json.dumps({"ImageUrl": image_url}, ensure_ascii=False))
        response = client.GeneralAccurateOCR(request)
        payload = json.loads(response.to_json_string())
        lines = _extract_text_detection_lines(payload)
        return normalize_whitespace(" ".join(line for line in lines if line))


class OcrService:
    def __init__(
        self,
        settings: Settings,
        client: OcrClient | None = None,
        session_factory: sessionmaker[Session] | None = None,
    ):
        self.settings = settings
        self._client = client
        self.session_factory = session_factory

    def should_ocr(self, content_text: str, image_urls: list[str]) -> bool:
        if not self.settings.ocr_enabled:
            return False
        if not image_urls:
            return False
        return len(normalize_whitespace(content_text)) < max(self.settings.ocr_min_text_length, 0)

    def maybe_append_ocr_text(
        self,
        raw_post: dict,
        content_text: str,
        *,
        post_id: int | None = None,
        upstream_post_id: str = "",
    ) -> OcrAppendResult:
        image_urls = extract_image_urls_from_raw_post(raw_post)
        if not self.should_ocr(content_text, image_urls):
            return OcrAppendResult(content_text=content_text, image_count=len(image_urls))

        ocr_text, processed_count = self._recognize_images(
            image_urls[: max(self.settings.ocr_max_images_per_post, 0)],
            post_id=post_id,
            upstream_post_id=upstream_post_id or str(raw_post.get("id") or ""),
        )
        if not ocr_text:
            return OcrAppendResult(content_text=content_text, image_count=len(image_urls))
        return OcrAppendResult(
            content_text=append_ocr_text(content_text, ocr_text),
            image_count=len(image_urls),
            processed_count=processed_count,
            ocr_text=ocr_text,
        )

    def _recognize_images(
        self,
        image_urls: list[str],
        *,
        post_id: int | None = None,
        upstream_post_id: str = "",
    ) -> tuple[str, int]:
        if not image_urls:
            return "", 0
        if self.settings.ocr_provider.lower() != "tencent":
            _logger.warning("unsupported OCR provider: %s", self.settings.ocr_provider)
            return "", 0
        action = normalize_whitespace(self.settings.ocr_action) or "RecognizeAgent"
        if action not in SUPPORTED_OCR_ACTIONS:
            _logger.warning("unsupported OCR action: %s", action)
            return "", 0

        if self.session_factory is None:
            return self._recognize_images_without_cache(image_urls)

        db = self.session_factory()
        try:
            return self._recognize_images_with_cache(
                db,
                image_urls,
                action=action,
                post_id=post_id,
                upstream_post_id=upstream_post_id,
            )
        finally:
            db.close()

    def _recognize_images_without_cache(self, image_urls: list[str]) -> tuple[str, int]:
        client = self._get_client()
        if client is None:
            return "", 0

        text_parts: list[str] = []
        processed_count = 0
        for image_url in image_urls:
            try:
                image_text = client.recognize_image_url(image_url)
            except Exception as exc:  # noqa: BLE001
                _logger.warning("OCR failed for image %s: %s", image_url, exc)
                continue
            if normalize_whitespace(image_text):
                text_parts.append(image_text)
                processed_count += 1
        return normalize_whitespace(" ".join(text_parts)), processed_count

    def _recognize_images_with_cache(
        self,
        db: Session,
        image_urls: list[str],
        *,
        action: str,
        post_id: int | None,
        upstream_post_id: str,
    ) -> tuple[str, int]:
        text_parts: list[str] = []
        processed_count = 0
        client: OcrClient | None = None
        for image_url in image_urls:
            image_hash = hash_image_url(image_url)
            cached = self._find_cache_row(db, image_hash, action)
            if cached and cached.status == OCR_STATUS_SUCCESS:
                if normalize_whitespace(cached.ocr_text):
                    text_parts.append(cached.ocr_text)
                    processed_count += 1
                continue

            month_key = current_ocr_month_key()
            if self._monthly_usage_count(db, month_key) >= max(self.settings.ocr_monthly_limit, 0):
                self._record_cache_row(
                    db,
                    image_hash=image_hash,
                    image_url=image_url,
                    action=action,
                    status=OCR_STATUS_SKIPPED_LIMIT,
                    month_key=month_key,
                    post_id=post_id,
                    upstream_post_id=upstream_post_id,
                    error_message="monthly OCR limit reached",
                )
                db.commit()
                continue

            if client is None:
                client = self._get_client()
            if client is None:
                return normalize_whitespace(" ".join(text_parts)), processed_count

            try:
                image_text = client.recognize_image_url(image_url)
            except Exception as exc:  # noqa: BLE001
                _logger.warning("OCR failed for image %s: %s", image_url, exc)
                self._record_usage_log(
                    db,
                    image_hash=image_hash,
                    image_url=image_url,
                    action=action,
                    status=OCR_STATUS_FAILED,
                    month_key=month_key,
                    post_id=post_id,
                    upstream_post_id=upstream_post_id,
                    error_message=str(exc),
                )
                self._record_cache_row(
                    db,
                    image_hash=image_hash,
                    image_url=image_url,
                    action=action,
                    status=OCR_STATUS_FAILED,
                    month_key=month_key,
                    post_id=post_id,
                    upstream_post_id=upstream_post_id,
                    error_message=str(exc),
                )
                db.commit()
                continue

            normalized_text = normalize_whitespace(image_text)
            self._record_usage_log(
                db,
                image_hash=image_hash,
                image_url=image_url,
                action=action,
                status=OCR_STATUS_SUCCESS,
                month_key=month_key,
                post_id=post_id,
                upstream_post_id=upstream_post_id,
            )
            self._record_cache_row(
                db,
                image_hash=image_hash,
                image_url=image_url,
                action=action,
                status=OCR_STATUS_SUCCESS,
                month_key=month_key,
                post_id=post_id,
                upstream_post_id=upstream_post_id,
                ocr_text=normalized_text,
            )
            db.commit()
            if normalized_text:
                text_parts.append(normalized_text)
                processed_count += 1
        return normalize_whitespace(" ".join(text_parts)), processed_count

    def _get_client(self) -> OcrClient | None:
        try:
            client = self._client or TencentCloudOcrClient(self.settings)
            self._client = client
            return client
        except Exception as exc:  # noqa: BLE001
            _logger.warning("OCR client initialization failed: %s", exc)
            return None

    def _find_cache_row(self, db: Session, image_hash: str, action: str) -> OcrImageCache | None:
        if not self.settings.ocr_cache_enabled:
            return None
        return (
            db.query(OcrImageCache)
            .filter(
                OcrImageCache.image_url_hash == image_hash,
                OcrImageCache.ocr_action == action,
            )
            .first()
        )

    def _monthly_usage_count(self, db: Session, month_key: str) -> int:
        statuses = [OCR_STATUS_SUCCESS]
        if self.settings.ocr_count_failed_attempts:
            statuses.append(OCR_STATUS_FAILED)
        return (
            db.query(func.count(OcrUsageLog.id))
            .filter(
                OcrUsageLog.month_key == month_key,
                OcrUsageLog.status.in_(statuses),
            )
            .scalar()
            or 0
        )

    def _record_usage_log(
        self,
        db: Session,
        *,
        image_hash: str,
        image_url: str,
        action: str,
        status: str,
        month_key: str,
        post_id: int | None,
        upstream_post_id: str,
        error_message: str = "",
    ) -> None:
        db.add(
            OcrUsageLog(
                image_url_hash=image_hash,
                image_url=image_url,
                ocr_action=action,
                status=status,
                month_key=month_key,
                post_id=post_id,
                upstream_post_id=upstream_post_id,
                error_message=error_message[:2000],
            )
        )

    def _record_cache_row(
        self,
        db: Session,
        *,
        image_hash: str,
        image_url: str,
        action: str,
        status: str,
        month_key: str,
        post_id: int | None,
        upstream_post_id: str,
        ocr_text: str = "",
        error_message: str = "",
    ) -> None:
        row = (
            db.query(OcrImageCache)
            .filter(
                OcrImageCache.image_url_hash == image_hash,
                OcrImageCache.ocr_action == action,
            )
            .first()
        )
        if row is None:
            row = OcrImageCache(image_url_hash=image_hash, ocr_action=action)
        row.image_url = image_url
        row.status = status
        row.month_key = month_key
        row.post_id = post_id
        row.upstream_post_id = upstream_post_id
        row.ocr_text = ocr_text
        row.error_message = error_message[:2000]
        db.add(row)
