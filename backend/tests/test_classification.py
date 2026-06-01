from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.application.classification import (
    TimeSignals,
    _validate_llm_output,
    classify_categories,
    classify_content_type,
    compute_ranking_score,
    derive_display_level,
    derive_participation_status,
    derive_time_status,
    extract_time_signals,
    parse_iso_datetime,
    prescreen_post,
)
from app.domain.enums import ContentType, DisplayLevel, ParticipationStatus, TimeStatus, TimelinessLevel


def test_prescreen_recap_hits_with_multiple_signals():
    decision = prescreen_post(
        title="活动回顾 | 校园志愿服务精彩回顾",
        summary="让我们一起回顾本次活动的精彩瞬间",
        source_name="校园服务中心",
    )
    assert decision.discard is True
    assert decision.reason == "recap"


def test_prescreen_tutorial_blocks_even_with_action_word():
    decision = prescreen_post(
        title="报名教程：手把手教你如何进行申请",
        summary="第一步注册，第二步提交材料",
        source_name="学院通知",
    )
    assert decision.discard is True
    assert decision.reason == "tutorial"


def test_prescreen_garbled_hidden_source_blocks_noise():
    decision = prescreen_post(
        title="锟斤拷锟斤拷x9A@@",
        summary="",
        source_name="",
    )
    assert decision.discard is True
    assert decision.reason == "garbled_hidden_source"


def test_prescreen_does_not_block_normal_english_title():
    decision = prescreen_post(
        title="IEEE AI Hackathon Registration Opens",
        summary="Students may register before May 28.",
        source_name="College Innovation Center",
    )
    assert decision.discard is False


def test_classify_categories_matches_new_taxonomy():
    categories = classify_categories("创新创业比赛报名通知", "面向全校学生开放")
    assert categories == ["competition"]


def test_classify_categories_returns_one_volunteer_category():
    categories = classify_categories("志愿者招募活动报名", "面向全校同学")
    assert categories == ["volunteer"]


def test_classify_categories_excludes_lecture_from_campus_activity():
    categories = classify_categories("校园活动讲座报名", "面向全校同学")
    assert categories == ["lecture"]


def test_classify_categories_maps_graduate_study():
    categories = classify_categories("研究生招生夏令营申请", "推免和留学申请材料说明")
    assert categories == ["graduate_study"]


def test_classify_categories_prioritizes_lecture_before_graduate_study():
    categories = classify_categories("考研讲座报名", "研究生升学经验分享")
    assert categories == ["lecture"]


def test_classify_categories_maps_exam_certification():
    categories = classify_categories("普通话水平测试报名通知", "请按要求完成报名")
    assert categories == ["exam_certification"]


def test_classify_categories_prioritizes_certification_before_lecture():
    categories = classify_categories("CFA考试经验分享会", "证书考试报名说明")
    assert categories == ["exam_certification"]


def test_classify_categories_excludes_school_exam_notice():
    categories = classify_categories("期末考试安排通知", "请查询考场安排")
    assert categories == ["other"]


def test_classify_categories_maps_campus_activity():
    categories = classify_categories("社团招新活动报名", "面向全校同学")
    assert categories == ["campus_activity"]


def test_classify_categories_uses_other_for_notice_only():
    categories = classify_categories("停水停电温馨提醒", "请各位同学提前做好准备")
    assert categories == ["other"]


def test_classify_categories_uses_content_when_headline_is_ambiguous():
    categories = classify_categories(
        "报名开启",
        "面向全校同学",
        "本次活动为数学建模学科竞赛，请同学们组队参赛并提交作品。",
    )
    assert categories == ["competition"]


def test_classify_categories_blocks_competition_result_notice():
    categories = classify_categories("挑战杯获奖名单结果公示", "赛事回顾如下")
    assert categories == ["other"]


def test_classify_categories_does_not_return_multiple_categories():
    categories = classify_categories("志愿服务活动报名", "面向全校同学")
    assert categories == ["volunteer"]
    assert len(categories) == 1


def test_classify_categories_uses_configured_priority_for_ties():
    categories = classify_categories("社团招新学科竞赛报名", "")
    assert categories == ["competition"]


def test_classify_categories_excludes_volunteer_from_campus_activity():
    categories = classify_categories("艺术节志愿者招募", "校园艺术节现场服务人员招募")
    assert categories == ["volunteer"]


def test_classify_categories_excludes_recruitment_from_campus_activity():
    categories = classify_categories("校园招聘宣讲会", "企业岗位投递开放")
    assert categories == ["recruitment"]


def test_classify_categories_excludes_internship_from_campus_activity():
    categories = classify_categories("社团招新实习岗位", "简历投递开放")
    assert categories == ["recruitment"]


def test_classify_categories_excludes_competition_from_student_activity():
    categories = classify_categories("学生会数学建模竞赛报名", "参赛队伍请提交作品")
    assert categories == ["competition"]


def test_classify_categories_keeps_field_practice_as_campus_activity_without_other_signals():
    categories = classify_categories("外出实践活动报名", "学生组织开展文化交流活动")
    assert categories == ["campus_activity"]


def test_classify_content_type_actionable_for_opportunity():
    content_type = classify_content_type("讲座报名通知", "报名截止时间为5月28日")
    assert content_type == ContentType.ACTIONABLE


def test_extract_time_signals_and_status():
    published_at = datetime(2026, 5, 20, tzinfo=timezone.utc)
    signals = extract_time_signals(
        "讲座报名通知",
        "报名截止5月28日18:00，活动时间5月30日",
        "",
        published_at,
    )
    status, timeliness = derive_time_status(signals, now=datetime(2026, 5, 21, tzinfo=timezone.utc))
    assert signals.deadline_at is not None
    assert status == TimeStatus.UPCOMING
    assert timeliness == TimelinessLevel.NORMAL


def test_participation_and_display_for_actionable_content():
    participation = derive_participation_status(
        content_type=ContentType.ACTIONABLE,
        time_status=TimeStatus.UPCOMING,
        text="面向全校学生开放报名，截止本周五",
    )
    display_level = derive_display_level(ContentType.ACTIONABLE, TimelinessLevel.NORMAL)
    assert participation == ParticipationStatus.PARTICIPABLE
    assert display_level.value == "normal"


def test_expired_actionable_content_is_low_priority_but_visible():
    status, timeliness = derive_time_status(
        TimeSignals(
            event_start_at=None,
            event_end_at=None,
            deadline_at=datetime(2026, 5, 24, tzinfo=timezone.utc),
        ),
        now=datetime(2026, 5, 25, tzinfo=timezone.utc),
    )
    display_level = derive_display_level(ContentType.ACTIONABLE, timeliness)
    participation = derive_participation_status(
        content_type=ContentType.ACTIONABLE,
        time_status=status,
        text="registration open",
    )

    assert status == TimeStatus.EXPIRED
    assert timeliness == TimelinessLevel.LOW
    assert display_level == DisplayLevel.NORMAL
    assert participation == ParticipationStatus.NON_PARTICIPABLE


def test_compute_ranking_score_rewards_near_deadline():
    now = datetime.now(timezone.utc)
    score = compute_ranking_score(
        participation_status=ParticipationStatus.PARTICIPABLE,
        content_type=ContentType.ACTIONABLE,
        primary_category="competition",
        time_status=TimeStatus.UPCOMING,
        deadline_at=now + timedelta(days=2),
        published_at=now - timedelta(days=1),
        now=now,
    )
    assert score >= 170


# --- LLM output validation tests ---

def test_validate_llm_output_happy_path():
    raw = {
        "title": "英语写作大赛报名",
        "summary": "第四届英文写作大赛正在报名中，截止5月29日。",
        "category": "competition",
        "is_opportunity": True,
        "is_recap": False,
        "event_type": "竞赛",
        "audience": "全体在校生",
        "call_to_action": "立即报名",
        "deadline_text": "5月29日中午12点",
        "start_time_text": "",
        "end_time_text": "",
        "key_evidence": "",
        "deadline_iso": "2026-05-29T12:00:00",
        "start_iso": None,
        "end_iso": None,
    }
    result = _validate_llm_output(raw)
    assert result["title"] == "英语写作大赛报名"
    assert result["category"] == "competition"
    assert result["deadline_iso"] == "2026-05-29T12:00:00"
    assert "start_iso" not in result


def test_validate_llm_output_rejects_oversized_title():
    raw = {"title": "A" * 50, "summary": "ok", "category": "other"}
    result = _validate_llm_output(raw)
    assert "title" not in result


def test_validate_llm_output_rejects_invalid_category():
    raw = {"title": "ok", "summary": "ok", "category": "party"}
    result = _validate_llm_output(raw)
    assert result["category"] == ""


def test_validate_llm_output_rejects_bad_iso():
    raw = {"title": "ok", "summary": "ok", "deadline_iso": "not-a-date"}
    result = _validate_llm_output(raw)
    assert "deadline_iso" not in result


def test_validate_llm_output_rejects_null_strings():
    raw = {"title": "ok", "summary": "ok", "start_iso": "null", "end_iso": "None"}
    result = _validate_llm_output(raw)
    assert "start_iso" not in result
    assert "end_iso" not in result


def test_validate_llm_output_truncates_long_summary():
    raw = {"title": "ok", "summary": "x" * 500, "category": "other"}
    result = _validate_llm_output(raw)
    assert len(result["summary"]) <= 200


# --- Non-campus content filtering tests ---

def test_prescreen_blocks_non_campus_source():
    result = prescreen_post(
        title="深圳周末相亲活动",
        summary="优质单身青年交友活动",
        source_name="深圳恋爱相亲",
    )
    assert result.discard is True
    assert result.reason == "non_campus"


def test_prescreen_blocks_non_campus_content():
    result = prescreen_post(
        title="单身派对交友大会",
        summary="脱单活动等你来",
        source_name="深圳大学社团",
    )
    assert result.discard is True
    assert result.reason == "non_campus"


def test_prescreen_allows_campus_content():
    result = prescreen_post(
        title="深圳大学数学竞赛报名",
        summary="数学竞赛面向全校学生",
        source_name="深圳大学教务部",
    )
    assert result.discard is False


# --- parse_iso_datetime tests ---

def test_parse_iso_datetime_full():
    dt = parse_iso_datetime("2026-05-29T12:00:00", None)
    assert dt is not None
    assert dt.year == 2026 and dt.month == 5 and dt.day == 29

def test_parse_iso_datetime_date_only():
    dt = parse_iso_datetime("2026-06-15", None)
    assert dt is not None
    assert dt.month == 6

def test_parse_iso_datetime_invalid():
    assert parse_iso_datetime("not-a-date", None) is None
    assert parse_iso_datetime("", None) is None
    assert parse_iso_datetime(None, None) is None
