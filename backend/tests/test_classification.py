from app.application.classification import classify_categories, classify_content_type, derive_display_level
from app.domain.enums import ContentType, DisplayLevel


def test_classify_categories_matches_activity():
    assert "activity" in classify_categories("校园活动报名通知", "")


def test_classify_content_type_prefers_non_actionable():
    content_type = classify_content_type("活动回顾与报名总结", "")
    assert content_type == ContentType.NON_ACTIONABLE


def test_derive_display_level_for_actionable():
    assert derive_display_level(ContentType.ACTIONABLE) == DisplayLevel.NORMAL

