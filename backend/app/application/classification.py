from __future__ import annotations

import html
import json
import re
from dataclasses import dataclass
from datetime import datetime
from hashlib import sha256

from app.domain.enums import (
    ContentType,
    DiscardReason,
    DisplayLevel,
    ParticipationStatus,
    TimeStatus,
    TimelinessLevel,
)

PRESCREEN_RULE_VERSION = "iter1-v1"
CONTENT_CLASSIFICATION_MAX_CHARS = 3000

CATEGORY_PRIORITY = [
    "campus_activity",
    "competition",
    "volunteer",
    "exam_certification",
    "recruitment",
    "lecture",
    "graduate_study",
]

CATEGORY_DISPLAY_ORDER = CATEGORY_PRIORITY + ["other"]
CATEGORY_ALIASES: dict[str, tuple[str, ...]] = {
    "campus_activity": ("campus_activity", "club_activity"),
    "exam_certification": ("exam_certification", "exam"),
    "other": ("other", "notice"),
}


def category_aliases(category: str) -> tuple[str, ...]:
    return CATEGORY_ALIASES.get(category, (category,))


def canonical_category(category: str) -> str:
    for canonical, aliases in CATEGORY_ALIASES.items():
        if category in aliases:
            return canonical
    if category in CATEGORY_DISPLAY_ORDER:
        return category
    return "other"


def normalize_category_list(categories: list[str]) -> list[str]:
    normalized = [canonical_category(category) for category in categories if category]
    unique = list(dict.fromkeys(normalized))
    priority = {category: index for index, category in enumerate(CATEGORY_DISPLAY_ORDER)}
    unique.sort(key=lambda category: priority.get(category, len(priority)))
    return unique or ["other"]


def effective_primary_category(primary_category: str, categories: list[str]) -> str:
    primary = canonical_category(primary_category)
    if primary != "other":
        return primary

    for category in normalize_category_list(categories):
        if category != "other":
            return category
    return "other"


CATEGORY_CORE_KEYWORDS: dict[str, list[str]] = {
    "campus_activity": [
        "社团",
        "招新",
        "迎新",
        "晚会",
        "音乐节",
        "文化节",
        "游园会",
        "运动会",
        "歌手大赛",
        "校园跑",
        "联谊",
        "团建",
        "文艺汇演",
        "学生会",
        "艺术节",
        "电竞赛",
    ],
    "lecture": [
        "讲座",
        "论坛",
        "沙龙",
        "分享会",
        "报告会",
        "讲堂",
        "公开课",
        "学术报告",
        "圆桌论坛",
        "研讨会",
        "经验分享",
        "主题报告",
    ],
    "volunteer": [
        "志愿者",
        "公益",
        "支教",
        "献血",
        "义工",
        "社区服务",
        "环保行动",
        "公益活动",
        "志愿服务",
        "志愿招募",
        "社会实践",
    ],
    "competition": [
        "竞赛",
        "大赛",
        "挑战杯",
        "互联网+",
        "数学建模",
        "创新创业",
        "电子设计",
        "机器人大赛",
        "案例分析",
        "作品征集",
        "项目申报",
        "科创比赛",
    ],
    "recruitment": [
        "招聘",
        "校招",
        "实习",
        "宣讲会",
        "岗位",
        "简历投递",
        "面试",
        "offer",
        "就业",
        "人才计划",
        "招聘会",
        "管培生",
    ],
    "graduate_study": [
        "考研",
        "保研",
        "研究生",
        "留学",
        "交换项目",
        "夏令营",
        "推免",
        "硕士招生",
        "博士招生",
        "CSC",
        "海外交流",
        "申请材料",
    ],
    "exam_certification": [
        "四六级",
        "大学英语四级",
        "大学英语六级",
        "英语四级",
        "英语六级",
        "CET-4",
        "CET-6",
        "CET4",
        "CET6",
        "普通话",
        "普通话水平测试",
        "计算机等级考试",
        "全国计算机等级考试",
        "NCRE",
        "教师资格证",
        "教师资格考试",
        "教资",
        "法考",
        "法律职业资格考试",
        "软考",
        "计算机技术与软件专业技术资格",
        "CFA",
    ],
}

CATEGORY_RULES = CATEGORY_CORE_KEYWORDS

CATEGORY_COMBO_RULES: dict[str, list[tuple[list[str], ...]]] = {
    "campus_activity": [
        (["社团"], ["招新"]),
        (["校园"], ["活动"]),
        (["学生会"], ["纳新"]),
        (["迎新"], ["活动"]),
        (["文化"], ["活动"]),
    ],
    "lecture": [
        (["专家"], ["讲座"]),
        (["学术"], ["报告"]),
        (["主题"], ["分享"]),
        (["经验"], ["交流"]),
        (["技术"], ["分享"]),
    ],
    "volunteer": [
        (["志愿者"], ["招募"]),
        (["公益"], ["活动"]),
        (["社区"], ["服务"]),
        (["支教"], ["活动"]),
        (["环保"], ["行动"]),
    ],
    "competition": [
        (["报名"], ["竞赛"]),
        (["作品"], ["提交"]),
        (["参赛"], ["队伍"]),
        (["创新"], ["大赛"]),
        (["项目"], ["评审"]),
    ],
    "recruitment": [
        (["校园"], ["招聘"]),
        (["岗位"], ["招聘"]),
        (["实习"], ["岗位"]),
        (["企业"], ["宣讲"]),
        (["简历"], ["投递"]),
    ],
    "graduate_study": [
        (["保研"], ["经验"]),
        (["考研"], ["讲座"]),
        (["研究生"], ["招生"]),
        (["留学"], ["申请"]),
        (["交换"], ["项目"]),
    ],
    "exam_certification": [
        (["四六级"], ["报名"]),
        (["普通话"], ["报名"]),
        (["计算机等级"], ["报名"]),
        (["教师资格"], ["报名"]),
        (["法考"], ["报名"]),
        (["软考"], ["报名"]),
        (["CFA"], ["报名"]),
        (["证书"], ["考试"]),
        (["资格"], ["考试"]),
    ],
}

CATEGORY_EXCLUDE_KEYWORDS: dict[str, list[str]] = {
    "campus_activity": [
        "竞赛",
        "大赛",
        "挑战杯",
        "数学建模",
        "项目申报",
        "作品征集",
        "招聘",
        "校招",
        "实习",
        "宣讲会",
        "岗位",
        "简历投递",
        "面试",
        "offer",
        "就业",
        "招聘会",
        "管培生",
        "志愿者",
        "公益",
        "志愿服务",
        "志愿招募",
        "义工",
        "支教",
        "献血",
        "四六级",
        "普通话",
        "计算机等级考试",
        "教师资格证",
        "法考",
        "软考",
        "CFA",
        "讲座",
        "论坛",
        "沙龙",
        "报告会",
        "公开课",
        "研讨会",
        "经验分享",
        "保研",
        "考研",
        "研究生",
        "留学",
        "交换项目",
        "夏令营",
        "推免",
    ],
    "lecture": [
        "招聘",
        "岗位",
        "投递",
        "录用",
        "保研",
        "招生",
        "交换项目",
    ],
    "volunteer": ["招聘", "实习", "竞赛", "保研"],
    "competition": ["获奖名单", "结果公示", "赛事回顾"],
    "recruitment": ["学术讲座", "经验分享", "技术论坛"],
    "graduate_study": ["招聘", "实习", "竞赛"],
    "exam_certification": [
        "期末",
        "期中",
        "补考",
        "缓考",
        "重修",
        "选课",
        "退课",
        "调课",
        "考试安排",
        "考场安排",
        "成绩查询",
    ],
}

CATEGORY_SCORE_THRESHOLD = 5
CORE_KEYWORD_SCORE = 5
COMBO_KEYWORD_SCORE = 8
EXCLUDE_KEYWORD_PENALTY = 5

NON_SHENZHEN_LOCATIONS = [
    "北京", "上海", "广州", "成都", "杭州", "武汉", "南京", "重庆", "西安",
    "苏州", "天津", "长沙", "郑州", "东莞", "青岛", "沈阳", "宁波", "昆明",
    "大连", "厦门", "福州", "无锡", "合肥", "济南", "佛山", "唐山", "温州",
    "常州", "泉州", "南宁", "贵阳", "南昌", "长春", "石家庄", "太原", "哈尔滨",
    "海口", "兰州", "呼和浩特", "乌鲁木齐", "拉萨", "银川", "西宁",
    "珠海", "中山", "惠州",
]

ACTIONABLE_HINTS = [
    "报名",
    "申请",
    "招募",
    "投递",
    "参加",
    "参赛",
    "征集",
    "提交",
    "申报",
    "报名入口",
    "报名通道",
    "提交材料",
    "截止",
    "开放申请",
]

REFERENCE_HINTS = ["须知", "说明", "提醒", "安排", "公告"]

EXCLUDE_RULES: dict[DiscardReason, dict[str, list[str]]] = {
    DiscardReason.RECAP: {
        "keywords": ["回顾", "总结", "综述", "纪实", "实录", "花絮", "剪影", "风采", "掠影", "瞬间"],
        "phrases": ["精彩回顾", "活动回顾", "赛事回顾", "工作总结", "成果回顾", "活动剪影", "精彩瞬间", "现场回顾", "活动花絮", "过程纪实"],
        "body": ["回顾本次活动", "现将活动情况总结如下", "让我们一起回顾", "本次活动取得了", "活动现场气氛热烈"],
    },
    DiscardReason.CLOSURE: {
        "keywords": ["落幕", "闭幕", "收官", "结束", "结营", "结课", "结项", "完结"],
        "phrases": ["圆满落幕", "圆满结束", "顺利结束", "顺利闭幕", "成功收官", "圆满收官", "正式闭幕", "完美落幕", "圆满结营", "顺利结课"],
        "body": ["至此圆满结束", "画上圆满句号", "本次会议圆满结束", "活动告一段落", "已顺利完成全部议程"],
    },
    DiscardReason.CONGRATULATION: {
        "keywords": ["恭喜", "祝贺", "喜报", "表彰", "捷报", "喜讯"],
        "phrases": ["热烈祝贺", "喜报频传", "荣获佳绩", "再创佳绩", "获奖喜报", "表彰通报", "先进表彰", "荣誉表彰"],
        "body": ["向他们表示祝贺", "特此表彰", "取得优异成绩", "荣获", "获此殊荣"],
    },
    DiscardReason.PUBLICITY_RESULT: {
        "keywords": ["名单", "公示", "结果", "入围", "录取", "通过", "获奖", "候选"],
        "phrases": ["获奖名单", "公示名单", "评选结果", "入围名单", "录取名单", "通过名单", "候选名单", "结果公布", "评审结果", "拟推荐名单"],
        "body": ["现予以公示", "名单如下", "结果如下", "公示期为", "经评审决定"],
    },
    DiscardReason.INTRODUCTION: {
        "keywords": ["介绍", "简介", "概况", "概览", "科普", "盘点", "解读", "认识"],
        "phrases": ["带你了解", "带你认识", "你了解吗", "什么是", "一文了解", "全面介绍", "相关简介", "基础知识", "知识普及", "机构介绍"],
        "body": ["本文将为你介绍", "带大家了解", "下面为大家介绍", "主要包括以下内容", "基本情况如下"],
    },
    DiscardReason.OPINION: {
        "keywords": ["观点", "评论", "随想", "感悟", "思考", "观察", "看法", "评析"],
        "phrases": ["我的看法", "个人观点", "几点思考", "现象观察", "深度评论", "问题思考", "观点分享", "经验感悟"],
        "body": ["笔者认为", "我认为", "值得思考的是", "从这个角度看", "个人理解"],
    },
    DiscardReason.TUTORIAL: {
        "keywords": ["教程", "指南", "攻略", "入门", "手册", "说明", "教学", "操作"],
        "phrases": ["手把手教你", "使用指南", "报名教程", "操作教程", "完整攻略", "入门指南", "步骤说明", "实用教程", "怎么做", "如何进行"],
        "body": ["第一步", "第二步", "操作如下", "具体步骤", "按以下流程进行"],
    },
    DiscardReason.RECORD_ONLY: {
        "keywords": ["记录", "纪行", "纪实", "实录", "报道", "简讯", "快讯", "纪要"],
        "phrases": ["活动纪实", "现场实录", "会议纪要", "工作纪实", "走访记录", "调研记录", "采访记录", "参会纪实", "现场报道", "活动简讯"],
        "body": ["活动现场", "会议现场", "有关情况记录如下", "全程记录", "本次走访中"],
    },
}

DIRECT_PREFIXES = ("恭喜", "祝贺", "喜报", "公示", "名单", "回顾", "教程", "指南", "介绍", "纪实")
NON_ACTIONABLE_PENALTIES = {"回顾", "总结", "落幕", "闭幕", "公示", "名单", "恭喜", "喜报", "教程", "介绍", "记录"}

NON_CAMPUS_SOURCE_KEYWORDS = [
    "相亲", "婚恋", "交友", "恋爱", "脱单", "征婚",
    "房产", "二手房", "租房", "楼盘", "房贷",
    "代购", "微商", "优惠券", "返利", "砍价",
    "按摩", "足浴", "SPA", "美容院",
]
NON_CAMPUS_CONTENT_KEYWORDS = [
    "相亲大会", "单身派对", "脱单活动", "交友派对",
    "找对象", "找老乡", "单身男女", "CP活动",
    "72小时CP", "恋爱offer", "双向奔赴",
    "楼盘开盘", "购房优惠", "房产投资",
]
PARTICIPABLE_HINTS = ["报名", "申请", "招募", "投递", "参加", "参赛", "征集", "公开招募", "开放申请", "提交材料"]

TIME_PATTERNS = [
    re.compile(r"(?:(?P<year>\d{4})[年\-/.])?(?P<month>\d{1,2})[月\-/.](?P<day>\d{1,2})[日号]?(?:\s*(?P<hour>\d{1,2})[:：](?P<minute>\d{2}))?"),
]
DATE_RANGE_PATTERN = re.compile(
    r"(?P<sm>\d{1,2})月(?P<sd>\d{1,2})日?(?:\s*(?P<sh>\d{1,2})[:：](?P<smin>\d{2}))?\s*(?:至|到|-|—|~)\s*"
    r"(?P<em>\d{1,2})月(?P<ed>\d{1,2})日?(?:\s*(?P<eh>\d{1,2})[:：](?P<emin>\d{2}))?"
)

DEADLINE_HINTS = ["截止", "报名截止", "申请截止", "投递截止", "截止时间"]
START_HINTS = ["开始", "活动时间", "活动将于", "举办时间", "时间为"]
END_HINTS = ["结束", "截至", "持续至", "截止至"]
SANITIZE_TAGS = ("script", "style", "iframe", "object", "embed", "link", "meta", "img")


@dataclass(slots=True)
class PrescreenDecision:
    discard: bool
    reason: str = ""
    matched_keywords: list[str] | None = None
    matched_fields: list[str] | None = None
    quality_signals: dict[str, float | int | str | dict] | None = None


@dataclass(slots=True)
class TimeSignals:
    event_start_at: datetime | None
    event_end_at: datetime | None
    deadline_at: datetime | None


def normalize_whitespace(value: str) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def html_to_text(value: str) -> str:
    text = re.sub(r"<[^>]+>", " ", value or "")
    return normalize_whitespace(html.unescape(text))


def sanitize_html(value: str) -> str:
    cleaned = value or ""
    for tag in SANITIZE_TAGS:
        cleaned = re.sub(rf"<{tag}\b[^>]*>.*?</{tag}>", "", cleaned, flags=re.IGNORECASE | re.DOTALL)
        cleaned = re.sub(rf"<{tag}\b[^>]*/?>", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\son\w+\s*=\s*(['\"]).*?\1", "", cleaned, flags=re.IGNORECASE | re.DOTALL)
    cleaned = re.sub(r"\s(href|src)\s*=\s*(['\"])javascript:.*?\2", "", cleaned, flags=re.IGNORECASE | re.DOTALL)
    return cleaned


def compute_content_hash(*parts: str) -> str:
    normalized = "||".join(normalize_whitespace(part) for part in parts)
    return sha256(normalized.encode("utf-8")).hexdigest()


def compute_title_hash(title: str) -> str:
    return sha256(normalize_whitespace(title).encode("utf-8")).hexdigest()


def _contains_any(text: str, items: list[str]) -> list[str]:
    return [item for item in items if item and item.lower() in text.lower()]


def _matches_combo_rule(text: str, combo_rule: tuple[list[str], ...]) -> bool:
    return all(_contains_any(text, group) for group in combo_rule)


def _score_category_text(text: str, category: str, *, weight: int) -> int:
    if not text:
        return 0
    core_hits = _contains_any(text, CATEGORY_CORE_KEYWORDS.get(category, []))
    combo_hits = [rule for rule in CATEGORY_COMBO_RULES.get(category, []) if _matches_combo_rule(text, rule)]
    exclude_hits = _contains_any(text, CATEGORY_EXCLUDE_KEYWORDS.get(category, []))

    score = len(core_hits) * CORE_KEYWORD_SCORE
    score += len(combo_hits) * COMBO_KEYWORD_SCORE
    if exclude_hits and not (category == "exam_certification" and core_hits):
        score -= len(exclude_hits) * EXCLUDE_KEYWORD_PENALTY
    return score * weight


def _quality_signals(text: str) -> dict[str, float | int | str]:
    value = text or ""
    length = len(value)
    cjk_count = len(re.findall(r"[\u4e00-\u9fff]", value))
    english_words = len(re.findall(r"\b[a-zA-Z]{3,}\b", value))
    replacement_char_count = value.count("�") + value.count("锟")
    mojibake_count = len(re.findall(r"[鐨氬鏄嬩绾诲湷]", value))
    symbol_count = len(re.findall(r"[^0-9A-Za-z\u4e00-\u9fff\s]", value))
    alnum_runs = sum(len(match.group(0)) for match in re.finditer(r"[A-Za-z0-9]{6,}", value))
    readable_token_count = cjk_count + english_words
    return {
        "length": length,
        "cjk_ratio": round(cjk_count / max(1, length), 3),
        "alnum_run_ratio": round(alnum_runs / max(1, length), 3),
        "replacement_char_count": replacement_char_count,
        "symbol_ratio": round(symbol_count / max(1, length), 3),
        "readable_token_count": readable_token_count,
        "mojibake_ratio": round(mojibake_count / max(1, length), 3),
    }


def _is_garbled_text(text: str) -> tuple[bool, dict[str, float | int | str]]:
    signals = _quality_signals(text)
    value = text or ""
    if not value:
        return False, signals
    if signals["replacement_char_count"] >= 2:
        return True, signals
    abnormal_run = bool(re.search(r"[^\w\s\u4e00-\u9fff]{4,}", value))
    low_readability = signals["cjk_ratio"] < 0.15 and signals["readable_token_count"] < 4
    high_noise = (
        signals["replacement_char_count"] >= 1
        or signals["symbol_ratio"] > 0.35
        or signals["alnum_run_ratio"] > 0.45
        or signals["mojibake_ratio"] > 0.35
    )
    too_short_noise = signals["length"] <= 12 and signals["readable_token_count"] <= 2 and high_noise
    return bool(abnormal_run or too_short_noise or (low_readability and high_noise)), signals


def prescreen_post(*, title: str, summary: str = "", source_name: str = "", body_excerpt: str = "") -> PrescreenDecision:
    title_text = normalize_whitespace(title)
    summary_text = normalize_whitespace(summary)
    body_text = normalize_whitespace(body_excerpt)

    source_lc = normalize_whitespace(source_name).lower()
    combined_lc = f"{title_text} {summary_text}".lower()
    non_campus_source_kw = _contains_any(source_lc, NON_CAMPUS_SOURCE_KEYWORDS)
    non_campus_content_kw = _contains_any(combined_lc, NON_CAMPUS_CONTENT_KEYWORDS)
    if non_campus_source_kw or non_campus_content_kw:
        return PrescreenDecision(
            True,
            DiscardReason.NON_CAMPUS.value,
            non_campus_source_kw + non_campus_content_kw,
            ["source_name"] if non_campus_source_kw else ["title", "summary"],
            None,
        )

    title_garbled, title_signals = _is_garbled_text(title_text)
    source_garbled, source_signals = _is_garbled_text(source_name)
    summary_garbled, summary_signals = _is_garbled_text(summary_text)

    if title_garbled:
        return PrescreenDecision(True, DiscardReason.GARBLED_HIDDEN_SOURCE.value, [], ["title"], title_signals)
    if source_garbled and summary_garbled:
        return PrescreenDecision(
            True,
            DiscardReason.GARBLED_HIDDEN_SOURCE.value,
            [],
            ["source_name", "summary"],
            {"source": source_signals, "summary": summary_signals},
        )
    if title_signals["cjk_ratio"] < 0.15 and (not source_name or source_garbled) and title_signals["readable_token_count"] < 4:
        return PrescreenDecision(
            True,
            DiscardReason.GARBLED_HIDDEN_SOURCE.value,
            [],
            ["title", "source_name"],
            {"title": title_signals, "source": source_signals},
        )

    for prefix in DIRECT_PREFIXES:
        if title_text.startswith(prefix):
            for reason, rule in EXCLUDE_RULES.items():
                if prefix in rule["keywords"] or prefix in rule["phrases"]:
                    return PrescreenDecision(True, reason.value, [prefix], ["title"], None)

    title_lc = title_text.lower()
    summary_lc = summary_text.lower()
    body_lc = body_text.lower()
    for reason, rule in EXCLUDE_RULES.items():
        title_phrases = _contains_any(title_lc, rule["phrases"])
        if title_phrases:
            return PrescreenDecision(True, reason.value, title_phrases, ["title"], None)

        title_keywords = _contains_any(title_lc, rule["keywords"])
        summary_keywords = _contains_any(summary_lc, rule["keywords"] + rule["body"])
        body_keywords = _contains_any(body_lc, rule["body"])
        matched_keywords = list(dict.fromkeys(title_keywords + summary_keywords + body_keywords))

        if title_keywords and summary_keywords:
            return PrescreenDecision(True, reason.value, matched_keywords, ["title", "summary"], None)
        if len(set(title_keywords + summary_keywords)) >= 2:
            fields = (["title"] if title_keywords else []) + (["summary"] if summary_keywords else [])
            return PrescreenDecision(True, reason.value, matched_keywords, fields, None)
        if (title_keywords or summary_keywords) and len(body_keywords) >= 2:
            fields = (["title"] if title_keywords else []) + (["summary"] if summary_keywords else []) + ["body_excerpt"]
            return PrescreenDecision(True, reason.value, matched_keywords, fields, None)

    return PrescreenDecision(False)


def classify_categories(title: str, summary: str = "", content: str = "") -> list[str]:
    headline_text = normalize_whitespace(f"{title} {summary}")
    content_text = normalize_whitespace((content or "")[:CONTENT_CLASSIFICATION_MAX_CHARS])
    combined_text = normalize_whitespace(f"{headline_text} {content_text}")
    scores = {}
    for category in CATEGORY_PRIORITY:
        score = _score_category_text(headline_text, category, weight=2)
        score += _score_category_text(content_text, category, weight=1)
        if category == "campus_activity" and _is_off_campus_activity(combined_text):
            score = 0
        scores[category] = score

    if scores["campus_activity"] >= CATEGORY_SCORE_THRESHOLD and any(
        scores[category] >= CATEGORY_SCORE_THRESHOLD
        for category in CATEGORY_PRIORITY
        if category != "campus_activity"
    ):
        scores["campus_activity"] = 0

    for category in CATEGORY_PRIORITY:
        if scores[category] >= CATEGORY_SCORE_THRESHOLD:
            return [category]
    return ["other"]


def _is_off_campus_activity(text: str) -> bool:
    return any(loc in text for loc in NON_SHENZHEN_LOCATIONS)


def classify_content_type(title: str, summary: str = "", content: str = "") -> ContentType:
    text = normalize_whitespace(f"{title} {summary}").lower()
    if _contains_any(text, list(NON_ACTIONABLE_PENALTIES)):
        return ContentType.NON_ACTIONABLE
    if _contains_any(text, ACTIONABLE_HINTS):
        return ContentType.ACTIONABLE
    if _contains_any(text, REFERENCE_HINTS):
        return ContentType.REFERENCE
    return ContentType.UNKNOWN


def derive_display_level(content_type: ContentType, timeliness_level: TimelinessLevel) -> DisplayLevel:
    if timeliness_level == TimelinessLevel.HIDDEN:
        return DisplayLevel.HIDDEN
    if content_type == ContentType.ACTIONABLE:
        return DisplayLevel.NORMAL
    if content_type == ContentType.REFERENCE:
        return DisplayLevel.LOW
    if content_type == ContentType.NON_ACTIONABLE:
        return DisplayLevel.HIDDEN
    return DisplayLevel.LOW


def _infer_year(month: int, published_at: datetime | None) -> int:
    base = published_at or datetime.now()
    year = base.year
    if published_at and month < max(1, published_at.month - 6):
        year += 1
    return year


def _tzinfo(published_at: datetime | None):
    return published_at.tzinfo if published_at and published_at.tzinfo else None


def _safe_datetime(year: int, month: int, day: int, hour: int, minute: int, published_at: datetime | None) -> datetime | None:
    try:
        return datetime(year, month, day, hour, minute, tzinfo=_tzinfo(published_at))
    except ValueError:
        return None


def _build_datetime(match: re.Match[str], published_at: datetime | None) -> datetime | None:
    year = int(match.groupdict().get("year") or _infer_year(int(match.group("month")), published_at))
    month = int(match.group("month"))
    day = int(match.group("day"))
    hour = int(match.groupdict().get("hour") or 23)
    minute = int(match.groupdict().get("minute") or 59)
    return _safe_datetime(year, month, day, hour, minute, published_at)


def extract_time_signals(title: str, summary: str, content: str, published_at: datetime | None) -> TimeSignals:
    text = normalize_whitespace(f"{title} {summary} {content}")
    deadline = None
    start = None
    end = None

    range_match = DATE_RANGE_PATTERN.search(text)
    if range_match:
        start_month, start_day = int(range_match.group("sm")), int(range_match.group("sd"))
        end_month, end_day = int(range_match.group("em")), int(range_match.group("ed"))
        year = _infer_year(start_month, published_at)
        start = _safe_datetime(year, start_month, start_day, int(range_match.group("sh") or 0), int(range_match.group("smin") or 0), published_at)
        end_year = year if end_month >= start_month else year + 1
        end = _safe_datetime(end_year, end_month, end_day, int(range_match.group("eh") or 23), int(range_match.group("emin") or 59), published_at)

    candidates: list[tuple[str, datetime]] = []
    for pattern in TIME_PATTERNS:
        for match in pattern.finditer(text):
            dt = _build_datetime(match, published_at)
            if dt is None:
                continue
            snippet = text[max(0, match.start() - 12) : min(len(text), match.end() + 12)]
            candidates.append((snippet, dt))

    for snippet, dt in candidates:
        if deadline is None and any(hint in snippet for hint in DEADLINE_HINTS):
            deadline = dt
        elif start is None and any(hint in snippet for hint in START_HINTS):
            start = dt
        elif end is None and any(hint in snippet for hint in END_HINTS):
            end = dt

    if deadline is None and "截止" in text and candidates:
        deadline = candidates[0][1]
    if start is None and candidates:
        start = candidates[0][1]
    if end is None and len(candidates) >= 2:
        end = candidates[1][1]
    return TimeSignals(event_start_at=start, event_end_at=end, deadline_at=deadline)


def derive_time_status(signals: TimeSignals, now: datetime | None = None) -> tuple[TimeStatus, TimelinessLevel]:
    tz = _tzinfo(signals.deadline_at or signals.event_end_at or signals.event_start_at)
    now = now or datetime.now(tz=tz)
    if signals.deadline_at and signals.deadline_at < now:
        return TimeStatus.EXPIRED, TimelinessLevel.LOW
    if signals.event_end_at and signals.event_end_at < now:
        return TimeStatus.EXPIRED, TimelinessLevel.LOW
    if signals.event_start_at and signals.event_end_at and signals.event_start_at <= now <= signals.event_end_at:
        return TimeStatus.ONGOING, TimelinessLevel.NORMAL
    if signals.deadline_at and signals.deadline_at >= now:
        return TimeStatus.UPCOMING, TimelinessLevel.NORMAL
    if signals.event_start_at and signals.event_start_at > now:
        return TimeStatus.UPCOMING, TimelinessLevel.NORMAL
    return TimeStatus.UNDATED, TimelinessLevel.LOW


def derive_participation_status(*, content_type: ContentType, time_status: TimeStatus, text: str) -> ParticipationStatus:
    lowered = text.lower()
    if content_type == ContentType.NON_ACTIONABLE or _contains_any(lowered, list(NON_ACTIONABLE_PENALTIES)):
        return ParticipationStatus.NON_PARTICIPABLE
    if time_status == TimeStatus.EXPIRED:
        return ParticipationStatus.NON_PARTICIPABLE
    if _contains_any(lowered, PARTICIPABLE_HINTS):
        return ParticipationStatus.PARTICIPABLE
    return ParticipationStatus.UNCERTAIN


def compute_ranking_score(
    *,
    participation_status: ParticipationStatus,
    content_type: ContentType,
    primary_category: str,
    time_status: TimeStatus,
    deadline_at: datetime | None,
    published_at: datetime | None,
    now: datetime | None = None,
) -> float:
    now = now or datetime.now(tz=_tzinfo(published_at or deadline_at))
    score = 0.0
    score += {
        ParticipationStatus.PARTICIPABLE: 100,
        ParticipationStatus.UNCERTAIN: 40,
        ParticipationStatus.NON_PARTICIPABLE: -120,
    }[participation_status]
    score += {
        ContentType.ACTIONABLE: 30,
        ContentType.REFERENCE: 5,
        ContentType.NON_ACTIONABLE: -80,
        ContentType.UNKNOWN: 0,
    }[content_type]
    score += {
        "competition": 20,
        "recruitment": 20,
        "graduate_study": 20,
        "lecture": 15,
        "volunteer": 15,
        "exam_certification": 15,
        "campus_activity": 10,
    }.get(primary_category, 0)
    score += {
        TimeStatus.ONGOING: 25,
        TimeStatus.UPCOMING: 20,
        TimeStatus.UNDATED: -5,
        TimeStatus.EXPIRED: -100,
    }[time_status]
    if deadline_at:
        days = (deadline_at - now).total_seconds() / 86400
        if days <= 3:
            score += 25
        elif days <= 7:
            score += 15
        elif days <= 14:
            score += 8
    if published_at:
        age_days = max(0, (now - published_at).total_seconds() / 86400)
        if age_days <= 3:
            score += 8
        elif age_days <= 7:
            score += 5
        elif age_days <= 30:
            score += 2
    return float(score)


def build_summary(*, title: str, upstream_summary: str, llm_summary: str, content_text: str) -> str:
    if normalize_whitespace(upstream_summary):
        return normalize_whitespace(upstream_summary)
    if normalize_whitespace(llm_summary):
        return normalize_whitespace(llm_summary)

    candidates = [segment.strip() for segment in re.split(r"[。！？；!?;]", content_text) if segment.strip()]
    scored: list[tuple[int, str]] = []
    for segment in candidates[:10]:
        score = 0
        score += 3 if _contains_any(segment, DEADLINE_HINTS + ACTIONABLE_HINTS) else 0
        score += 2 if _contains_any(segment, ["面向", "对象", "学生", "同学", "学院"]) else 0
        score += 1 if _contains_any(segment, ["讲座", "比赛", "志愿", "招聘", "考试"]) else 0
        score -= 3 if _contains_any(segment, list(NON_ACTIONABLE_PENALTIES)) else 0
        scored.append((score, segment))
    scored.sort(key=lambda item: (item[0], len(item[1])), reverse=True)
    best = [segment for score, segment in scored if score >= 1][:2]
    summary = "。".join(best) if best else normalize_whitespace(title)
    return summary[:140]


VALID_CATEGORIES = set(CATEGORY_PRIORITY) | {"other"}
ISO_DATETIME_RE = re.compile(r"^\d{4}-\d{2}-\d{2}(T\d{2}:\d{2}(:\d{2})?)?$")


def _validate_llm_output(raw: dict) -> dict:
    result = {}

    title = str(raw.get("title") or "").strip()
    if title and len(title) <= 40:
        result["title"] = title

    summary = str(raw.get("summary") or "").strip()
    result["summary"] = summary[:200] if summary else ""

    category = str(raw.get("category") or "").strip()
    result["category"] = category if category in VALID_CATEGORIES else ""

    for field in ("is_opportunity", "is_recap"):
        val = raw.get(field)
        if isinstance(val, bool):
            result[field] = val
        elif isinstance(val, str):
            result[field] = val.lower() in ("true", "yes", "1")

    for field in ("event_type", "audience", "call_to_action", "deadline_text", "start_time_text", "end_time_text", "key_evidence"):
        val = str(raw.get(field) or "").strip()
        if val:
            result[field] = val

    for iso_field in ("deadline_iso", "start_iso", "end_iso"):
        val = str(raw.get(iso_field) or "").strip()
        if val and val.lower() not in ("null", "none", "n/a", ""):
            if ISO_DATETIME_RE.match(val):
                result[iso_field] = val

    return result


def parse_llm_payload(payload: str) -> dict:
    if not payload:
        return {}
    try:
        raw = json.loads(payload)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", payload, flags=re.DOTALL)
        if not match:
            return {}
        try:
            raw = json.loads(match.group(0))
        except json.JSONDecodeError:
            return {}
    if not isinstance(raw, dict):
        return {}
    return _validate_llm_output(raw)


def parse_iso_datetime(value: str, published_at: datetime | None) -> datetime | None:
    if not value:
        return None
    for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            dt = datetime.strptime(value[:19] if len(value) >= 19 else value, fmt)
            tz = published_at.tzinfo if published_at and published_at.tzinfo else None
            return dt.replace(tzinfo=tz)
        except (ValueError, IndexError):
            continue
    return None
