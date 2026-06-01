#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path


DEFAULT_SAMPLE_FILE = Path("/home/linrong/codex-projects/lizhi/text/campus-activity.txt")

REGISTRATION_START_HINTS = (
    "报名开始",
    "开始报名",
    "报名系统开放",
    "报名通道开放",
    "报名入口开放",
    "开放报名",
    "报名时间",
    "申请时间",
    "投递时间",
    "预约二维码开放时间",
    "预约时间",
    "招募时间",
    "即日起",
)
REGISTRATION_DEADLINE_HINTS = (
    "报名截止",
    "截止报名",
    "报名截止时间",
    "报名截止日期",
    "申请截止",
    "投递截止",
    "提交截止",
    "招募截止",
    "预约截止",
    "截止时间",
    "截止日期",
    "截止至",
    "截至",
)
NON_REGISTRATION_HINTS = (
    "活动时间",
    "服务时间",
    "课程日期",
    "课程时间",
    "比赛时间",
    "项目时间",
    "举办时间",
    "展演时间",
    "观赛时间",
    "入场时间",
)
EVENT_START_HINTS = (
    "活动时间",
    "开始时间",
    "举办时间",
    "讲座时间",
    "比赛时间",
    "服务时间",
    "课程日期",
    "课程时间",
    "演出时间",
    "观赛时间",
    "摊宣时间",
    "首轮体验时间",
    "项目时间",
    "项目时段",
    "活动周期",
    "时间：",
    "时间｜",
    "时间&地点",
)

DATE_RE = re.compile(
    r"(?:(?P<year>20\d{2})\s*[年\-/.])?"
    r"(?P<month>\d{1,2})\s*[月\-/.]\s*"
    r"(?P<day>\d{1,2})\s*(?:日|号)?"
    r"(?:\s*[（(]?(?:周|星期)[一二三四五六日天\d]+[）)]?)?"
    r"(?:\s*(?:上午|下午|晚上|中午|晚)?\s*(?P<hour>\d{1,2}|[一二三四五六七八九十两]+)\s*[:：点时]\s*(?P<minute>\d{0,2}))?"
)
DATE_RANGE_RE = re.compile(
    r"(?P<prefix>即日起|报名时间|申请时间|投递时间|预约时间|招募时间|报名系统开放时间|预约二维码开放时间)"
    r"[^，。；;\n]{0,12}?"
    r"(?:至|到|-|—|~)"
    r"(?P<date>"
    r"(?:(?:20\d{2})\s*[年\-/.])?"
    r"\d{1,2}\s*[月\-/.]\s*\d{1,2}\s*(?:日|号)?"
    r"(?:\s*(?:上午|下午|晚上|中午|晚)?\s*\d{1,2}\s*[:：点时]\s*\d{0,2})?"
    r"|待定)"
)
TIME_ONLY_RE = re.compile(
    r"(?:上午|下午|晚上|中午|晚)?\s*"
    r"(?P<hour>\d{1,2}|[一二三四五六七八九十两]+)\s*[:：点时]\s*(?P<minute>\d{0,2})"
)


@dataclass(slots=True)
class TimeHit:
    value: str | None
    kind: str
    confidence: str
    evidence: str


@dataclass(slots=True)
class RegistrationTimes:
    registration_start_at: str | None
    registration_deadline_at: str | None
    start_hit: TimeHit | None
    deadline_hit: TimeHit | None


def normalize_text(value: str) -> str:
    text = re.sub(r"\s+", " ", value or "")
    return text.strip()


def infer_year(month: int, published_at: datetime) -> int:
    year = published_at.year
    if month < max(1, published_at.month - 6):
        year += 1
    return year


def parse_number(value: str) -> int:
    if value.isdigit():
        return int(value)
    digits = {"一": 1, "二": 2, "两": 2, "三": 3, "四": 4, "五": 5, "六": 6, "七": 7, "八": 8, "九": 9}
    if value == "十":
        return 10
    if value.startswith("十"):
        return 10 + digits.get(value[1:], 0)
    if value.endswith("十"):
        return digits.get(value[:-1], 0) * 10
    if "十" in value:
        left, right = value.split("十", 1)
        return digits.get(left, 1) * 10 + digits.get(right, 0)
    return digits.get(value, 0)


def build_datetime(match: re.Match[str], published_at: datetime) -> datetime | None:
    year = int(match.group("year") or infer_year(int(match.group("month")), published_at))
    month = int(match.group("month"))
    day = int(match.group("day"))
    raw_hour = match.group("hour")
    raw_minute = match.group("minute")
    hour = parse_number(raw_hour) if raw_hour else 23
    minute = int(raw_minute) if raw_minute else (0 if raw_hour else 59)
    phrase = match.group(0)
    if raw_hour and ("下午" in phrase or "晚上" in phrase or "晚" in phrase) and hour < 12:
        hour += 12
    if raw_hour and "中午" in phrase and hour < 11:
        hour += 12
    try:
        return datetime(year, month, day, hour, minute)
    except ValueError:
        return None


def parse_date_text(value: str, published_at: datetime) -> datetime | None:
    match = DATE_RE.search(value)
    return build_datetime(match, published_at) if match else None


def has_any(value: str, hints: tuple[str, ...]) -> bool:
    return any(hint in value for hint in hints)


def window(text: str, start: int, end: int, size: int = 30) -> str:
    return text[max(0, start - size) : min(len(text), end + size)]


def confidence_for(snippet: str, kind: str) -> str:
    if kind == "deadline":
        if has_any(snippet, ("报名截止", "申请截止", "投递截止", "提交截止", "招募截止")):
            return "high"
        if has_any(snippet, ("截止时间", "截止日期", "截至", "截止至")) and has_any(snippet, ("报名", "申请", "投递", "提交", "招募", "预约")):
            return "high"
        return "medium"

    if has_any(snippet, ("报名开始", "开始报名", "报名系统开放", "报名通道开放", "报名入口开放", "预约二维码开放时间", "即日起")):
        return "high"
    if has_any(snippet, ("报名时间", "申请时间", "投递时间", "招募时间", "预约时间", "开放时间")):
        return "medium"
    return "low"


def score_hit(hit: TimeHit) -> tuple[int, str]:
    confidence_score = {"high": 3, "medium": 2, "low": 1}.get(hit.confidence, 0)
    specificity = 1 if hit.value and "T" in hit.value else 0
    return confidence_score, str(specificity)


def is_covered(span: tuple[int, int], covered_spans: list[tuple[int, int]]) -> bool:
    start, end = span
    return any(start >= covered_start and end <= covered_end for covered_start, covered_end in covered_spans)


def date_context(text: str, match: re.Match[str]) -> tuple[str, str, str]:
    before = text[max(0, match.start() - 24) : match.start()]
    after = text[match.end() : min(len(text), match.end() + 16)]
    return before, after, f"{before}{match.group(0)}{after}"


def classify_date_match(text: str, match: re.Match[str]) -> tuple[str | None, str]:
    before, after, snippet = date_context(text, match)
    if has_any(before, REGISTRATION_DEADLINE_HINTS) or (
        has_any(after, REGISTRATION_DEADLINE_HINTS) and not has_any(before, REGISTRATION_START_HINTS)
    ):
        return "deadline", snippet
    if has_any(before, REGISTRATION_START_HINTS) or has_any(after, REGISTRATION_START_HINTS):
        return "start", snippet
    return None, snippet


def should_treat_as_event_start(text: str, match: re.Match[str]) -> bool:
    before, after, snippet = date_context(text, match)
    if has_any(snippet, REGISTRATION_DEADLINE_HINTS):
        return False
    return has_any(before, EVENT_START_HINTS) or has_any(after, EVENT_START_HINTS)


def attach_nearby_time(dt: datetime, text: str, match: re.Match[str]) -> datetime:
    if match.group("hour"):
        return dt
    after = text[match.end() : min(len(text), match.end() + 90)]
    time_match = TIME_ONLY_RE.search(after)
    if not time_match:
        return dt
    if DATE_RE.search(after[: time_match.start()]):
        return dt
    hour = parse_number(time_match.group("hour"))
    minute = int(time_match.group("minute") or "0")
    phrase = time_match.group(0)
    if ("下午" in phrase or "晚上" in phrase or "晚" in phrase) and hour < 12:
        hour += 12
    if "中午" in phrase and hour < 11:
        hour += 12
    try:
        return dt.replace(hour=hour, minute=minute)
    except ValueError:
        return dt


def extract_event_start_and_deadline_points(text: str, published_at: datetime) -> list[dict]:
    text = normalize_text(text)
    points: list[tuple[int, dict]] = []
    covered_spans: list[tuple[int, int]] = []

    for range_match in DATE_RANGE_RE.finditer(text):
        snippet = window(text, range_match.start(), range_match.end(), 35)
        if has_any(snippet, NON_REGISTRATION_HINTS) and not has_any(snippet, ("报名", "申请", "投递", "招募", "预约")):
            continue
        date_text = range_match.group("date")
        if date_text == "待定":
            continue
        covered_spans.append(range_match.span("date"))
        deadline = parse_date_text(date_text, published_at)
        if deadline:
            points.append(
                (
                    range_match.start("date"),
                    {
                        "event_start_at": None,
                        "registration_deadline_at": deadline.isoformat(timespec="minutes"),
                    },
                )
            )

    for match in DATE_RE.finditer(text):
        dt = build_datetime(match, published_at)
        if not dt:
            continue
        kind, snippet = classify_date_match(text, match)
        if kind == "deadline" and not is_covered(match.span(), covered_spans):
            if re.search(r"(报名|申请|投递|提交|招募|预约)?截止后", snippet):
                continue
            points.append(
                (
                    match.start(),
                    {
                        "event_start_at": None,
                        "registration_deadline_at": dt.isoformat(timespec="minutes"),
                    },
                )
            )
            continue
        if should_treat_as_event_start(text, match):
            event_dt = attach_nearby_time(dt, text, match)
            points.append(
                (
                    match.start(),
                    {
                        "event_start_at": event_dt.isoformat(timespec="minutes"),
                        "registration_deadline_at": None,
                    },
                )
            )

    return [point for _, point in sorted(points, key=lambda item: item[0])]


def extract_registration_times(text: str, published_at: datetime) -> RegistrationTimes:
    text = normalize_text(text)
    start_hits: list[TimeHit] = []
    deadline_hits: list[TimeHit] = []
    covered_spans: list[tuple[int, int]] = []

    for range_match in DATE_RANGE_RE.finditer(text):
        snippet = window(text, range_match.start(), range_match.end(), 35)
        if has_any(snippet, NON_REGISTRATION_HINTS) and not has_any(snippet, ("报名", "申请", "投递", "招募", "预约")):
            continue
        prefix = range_match.group("prefix")
        start_value = published_at.replace(hour=0, minute=0, second=0, microsecond=0).isoformat(timespec="minutes")
        start_hits.append(
            TimeHit(
                value=start_value,
                kind="start",
                confidence=confidence_for(prefix, "start"),
                evidence=snippet,
            )
        )
        date_text = range_match.group("date")
        if date_text != "待定":
            covered_spans.append(range_match.span("date"))
            deadline = parse_date_text(date_text, published_at)
            if deadline:
                deadline_hits.append(
                    TimeHit(
                        value=deadline.isoformat(timespec="minutes"),
                        kind="deadline",
                        confidence=confidence_for(snippet, "deadline"),
                        evidence=snippet,
                    )
                )

    for match in DATE_RE.finditer(text):
        if is_covered(match.span(), covered_spans):
            continue
        dt = build_datetime(match, published_at)
        if not dt:
            continue
        kind, snippet = classify_date_match(text, match)
        if has_any(snippet, NON_REGISTRATION_HINTS) and not has_any(snippet, ("报名", "申请", "投递", "提交", "招募", "预约")):
            continue
        if re.search(r"(报名|申请|投递|提交|招募|预约)?截止后", snippet):
            continue

        if kind == "deadline":
            deadline_hits.append(
                TimeHit(
                    value=dt.isoformat(timespec="minutes"),
                    kind="deadline",
                    confidence=confidence_for(snippet, "deadline"),
                    evidence=snippet,
                )
            )
        elif kind == "start":
            start_hits.append(
                TimeHit(
                    value=dt.isoformat(timespec="minutes"),
                    kind="start",
                    confidence=confidence_for(snippet, "start"),
                    evidence=snippet,
                )
            )

    start_hit = sorted(start_hits, key=score_hit, reverse=True)[0] if start_hits else None
    deadline_hit = sorted(deadline_hits, key=score_hit, reverse=True)[0] if deadline_hits else None
    return RegistrationTimes(
        registration_start_at=start_hit.value if start_hit else None,
        registration_deadline_at=deadline_hit.value if deadline_hit else None,
        start_hit=start_hit,
        deadline_hit=deadline_hit,
    )


SAMPLES = [
    "报名截止时间：2026年5月30日",
    "报名系统开放时间为北京时间2026年3月26日10:00，截止时间为北京时间2026年7月15日中午12:00。",
    "即日起至5月31日22:00，扫描二维码填写报名表。",
    "服务时间：2026年七月中旬至七月底，活动地点另行通知。",
    "报名截止后统一筛选并安排面试。",
    "报名截止时间：3 月 23 号 18:00",
    "报名截止时间：周五5月29日17:00前",
    "报名时间即日起至待定 摊位有限，先到先得。",
]


def split_text(text: str, chunk_chars: int) -> list[str]:
    if chunk_chars <= 0:
        return [text]
    chunks = []
    for index in range(0, len(text), chunk_chars):
        chunk = text[index : index + chunk_chars]
        if has_any(chunk, REGISTRATION_START_HINTS + REGISTRATION_DEADLINE_HINTS + EVENT_START_HINTS):
            chunks.append(chunk)
    return chunks


def main() -> None:
    parser = argparse.ArgumentParser(description="Test regex extraction of registration start/deadline times.")
    parser.add_argument("--file", type=Path, default=None, help="Optional text file to scan.")
    parser.add_argument("--published-at", default="2026-05-01T00:00:00", help="Reference publish time for year inference.")
    parser.add_argument("--chunk-chars", type=int, default=900, help="Chunk size when scanning a file.")
    parser.add_argument("--limit", type=int, default=20, help="Maximum file chunks to print.")
    parser.add_argument("--file-only", action="store_true", help="Only print results from --file, not built-in samples.")
    parser.add_argument("--time-points-only", action="store_true", help="Only print extracted time points.")
    parser.add_argument("--event-start-and-deadline-only", action="store_true", help="Only print event_start_at and registration_deadline_at points from --file.")
    args = parser.parse_args()

    published_at = datetime.fromisoformat(args.published_at)
    results: list[dict] = []

    if not args.file_only:
        for sample in SAMPLES:
            extracted = extract_registration_times(sample, published_at)
            if args.time_points_only:
                results.append(
                    {
                        "registration_start_at": extracted.registration_start_at,
                        "registration_deadline_at": extracted.registration_deadline_at,
                    }
                )
            else:
                results.append({"source": "built-in", "text": sample, "result": asdict(extracted)})

    file_path = args.file
    if file_path is None and DEFAULT_SAMPLE_FILE.exists():
        file_path = DEFAULT_SAMPLE_FILE
    if file_path:
        file_text = file_path.read_text(encoding="utf-8")
        if args.event_start_and_deadline_only:
            results.extend(extract_event_start_and_deadline_points(file_text, published_at))
            print(json.dumps(results, ensure_ascii=False, indent=2))
            return
        for idx, chunk in enumerate(split_text(file_text, args.chunk_chars)[: args.limit], start=1):
            extracted = extract_registration_times(chunk, published_at)
            if extracted.registration_start_at or extracted.registration_deadline_at:
                if args.time_points_only:
                    results.append(
                        {
                            "registration_start_at": extracted.registration_start_at,
                            "registration_deadline_at": extracted.registration_deadline_at,
                        }
                    )
                    continue
                results.append(
                    {
                        "source": str(file_path),
                        "chunk": idx,
                        "preview": normalize_text(chunk)[:220],
                        "result": asdict(extracted),
                    }
                )

    print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
