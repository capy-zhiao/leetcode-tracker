"""SRS 算法单元测试。纯函数没有 DB 依赖,所以能这么干净地测。"""
from datetime import date, timedelta

import pytest

from app.srs import (
    DEFAULT_EASE, MAX_EASE, MIN_EASE, SrsState,
    is_due, priority, review, suggest_grade,
)

TODAY = date(2026, 1, 1)
NEW = SrsState()


# ---------- 首次复习 ----------
@pytest.mark.parametrize("grade,expected_days", [
    ("again", 1), ("hard", 2), ("good", 4), ("easy", 7),
])
def test_first_review_intervals(grade, expected_days):
    s = review(NEW, grade, "Medium", TODAY)
    assert s.interval_days == expected_days
    assert s.due == TODAY + timedelta(days=expected_days)


def test_first_review_hard_problem_gets_shorter_interval():
    """Hard 题忘得快,间隔要打折"""
    med = review(NEW, "good", "Medium", TODAY)
    hard = review(NEW, "good", "Hard", TODAY)
    easy = review(NEW, "good", "Easy", TODAY)
    assert hard.interval_days < med.interval_days < easy.interval_days


# ---------- 间隔增长 ----------
def test_interval_grows_with_repeated_good():
    s = NEW
    intervals = []
    for _ in range(5):
        s = review(s, "good", "Medium", TODAY)
        intervals.append(s.interval_days)
    assert intervals == sorted(intervals), "间隔应该单调不减"
    assert intervals[-1] > intervals[0] * 3, "连续答对后间隔要明显拉开"


def test_easy_grows_faster_than_good():
    warm = review(review(NEW, "good", "Medium", TODAY), "good", "Medium", TODAY)
    assert (review(warm, "easy", "Medium", TODAY).interval_days
            > review(warm, "good", "Medium", TODAY).interval_days)


def test_hard_barely_grows():
    warm = review(review(NEW, "good", "Medium", TODAY), "good", "Medium", TODAY)
    hard = review(warm, "hard", "Medium", TODAY)
    assert warm.interval_days <= hard.interval_days <= warm.interval_days * 1.5


# ---------- 翻车 ----------
def test_again_resets_interval_and_counts_lapse():
    s = NEW
    for _ in range(4):
        s = review(s, "good", "Medium", TODAY)
    assert s.interval_days > 10

    s2 = review(s, "again", "Medium", TODAY)
    assert s2.interval_days == 1, "翻车后明天必须再来"
    assert s2.reps == 0
    assert s2.lapses == s.lapses + 1
    assert s2.ease < s.ease


def test_ease_stays_in_bounds():
    s = NEW
    for _ in range(30):
        s = review(s, "again", "Medium", TODAY)
    assert s.ease == pytest.approx(MIN_EASE)

    s = NEW
    for _ in range(30):
        s = review(s, "easy", "Medium", TODAY)
    assert s.ease <= MAX_EASE


def test_interval_capped_at_one_year():
    s = NEW
    for _ in range(40):
        s = review(s, "easy", "Easy", TODAY)
    assert s.interval_days <= 365


# ---------- 评分推荐 ----------
def test_suggest_grade_from_timer():
    assert suggest_grade(60, looked_at_solution=True) == "again"
    assert suggest_grade(3 * 60, looked_at_solution=False) == "easy"
    assert suggest_grade(10 * 60, looked_at_solution=False) == "good"
    assert suggest_grade(25 * 60, looked_at_solution=False) == "hard"
    assert suggest_grade(8 * 60, looked_at_solution=False, had_bugs=True) == "hard"


def test_suggest_grade_scales_with_difficulty():
    """20 分钟做完 Hard 题算顺利,做完 Easy 题就是卡了"""
    assert suggest_grade(20 * 60, False, difficulty="Hard") == "good"
    assert suggest_grade(20 * 60, False, difficulty="Easy") == "hard"


# ---------- 优先级 ----------
def test_priority_prefers_overdue_and_lapsed():
    due_today = SrsState(interval_days=5, due=TODAY)
    overdue = SrsState(interval_days=5, due=TODAY - timedelta(days=7))
    lapsed = SrsState(interval_days=5, lapses=3, due=TODAY)

    assert priority(overdue, TODAY) > priority(due_today, TODAY)
    assert priority(lapsed, TODAY) > priority(due_today, TODAY)


def test_priority_prefers_hard_and_early_chapters():
    s = SrsState(interval_days=5, due=TODAY)
    assert priority(s, TODAY, "Hard", 1) > priority(s, TODAY, "Easy", 1)
    assert priority(s, TODAY, "Medium", 1) > priority(s, TODAY, "Medium", 15)


def test_never_scheduled_is_not_due():
    assert not is_due(NEW, TODAY)
    assert is_due(SrsState(due=TODAY), TODAY)
    assert not is_due(SrsState(due=TODAY + timedelta(days=1)), TODAY)


# ---------- 真实场景回归 ----------
def test_zhiao_rotting_oranges_scenario():
    """994 烂橘子:返工 3 版(连续 again),之后逐步做顺 —— 间隔应该爬得比没翻过车的慢"""
    troubled = NEW
    for _ in range(3):
        troubled = review(troubled, "again", "Medium", TODAY)
    for _ in range(3):
        troubled = review(troubled, "good", "Medium", TODAY)

    smooth = NEW
    for _ in range(3):
        smooth = review(smooth, "good", "Medium", TODAY)

    assert troubled.interval_days < smooth.interval_days
    assert troubled.lapses == 3
    assert priority(troubled, TODAY) > priority(smooth, TODAY), "翻过车的题要优先复习"
