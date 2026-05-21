from __future__ import annotations

from app.domain.enums import ContentType, DisplayLevel

CATEGORY_RULES = {
    "lecture": ["讲座", "报告", "论坛", "学术", "分享会", "研讨会", "宣讲"],
    "activity": ["活动", "比赛", "竞赛", "挑战", "沙龙", "文化节", "运动会"],
    "volunteer": ["志愿", "义工", "服务时", "公益"],
    "exam": ["考试", "四六级", "报名", "截止", "选课", "补考", "缓考"],
    "recruitment": ["招聘", "实习", "春招", "秋招", "就业", "宣讲会", "招聘会"],
    "scholarship": ["奖学金", "助学金", "资助", "助贷", "勤工"],
}

CONTENT_TYPE_RULES = {
    ContentType.ACTIONABLE: [
        "报名", "招募", "招新", "征集", "预告", "开始",
        "申请", "征稿", "志愿者", "宣讲会", "讲座预告",
        "活动预告", "报名通道", "截止", "通知",
    ],
    ContentType.NON_ACTIONABLE: [
        "回顾", "总结", "圆满结束", "顺利举办", "精彩回顾",
        "活动纪实", "风采展示", "获奖名单", "喜报", "成果展示",
        "会议新闻", "表彰",
    ],
    ContentType.REFERENCE: [
        "攻略", "指南", "合集", "清单", "一览", "活动日历", "须知",
    ],
}

DISPLAY_LEVEL_MAP = {
    ContentType.ACTIONABLE: DisplayLevel.NORMAL,
    ContentType.REFERENCE: DisplayLevel.LOW,
    ContentType.NON_ACTIONABLE: DisplayLevel.HIDDEN,
    ContentType.UNKNOWN: DisplayLevel.LOW,
}


def classify_categories(title: str, summary: str = "") -> list[str]:
    text = f"{title} {summary}".lower()
    matched: list[str] = []
    for category, keywords in CATEGORY_RULES.items():
        if any(keyword.lower() in text for keyword in keywords):
            matched.append(category)
    return matched or ["other"]


def classify_content_type(title: str, summary: str = "") -> ContentType:
    text = f"{title} {summary}".lower()
    for content_type in (
        ContentType.NON_ACTIONABLE,
        ContentType.ACTIONABLE,
        ContentType.REFERENCE,
    ):
        if any(keyword.lower() in text for keyword in CONTENT_TYPE_RULES[content_type]):
            return content_type
    return ContentType.UNKNOWN


def derive_display_level(content_type: ContentType) -> DisplayLevel:
    return DISPLAY_LEVEL_MAP.get(content_type, DisplayLevel.LOW)

