"""Pattern taxonomy integrity.

These are cheap invariants that catch the realistic failure mode: editing patterns.py and
leaving a typo'd tag behind, which would silently create a phantom pattern in the UI.
"""

from app.patterns import (
    CHAPTER_FALLBACK, PATTERN_TEMPLATE, PATTERNS, PROBLEM_PATTERNS, patterns_for,
)
from app.templates_ref import BY_NUMBER

from app.study_plans import PROBLEM_SET


def test_every_tag_is_a_defined_pattern():
    used = {t for tags in PROBLEM_PATTERNS.values() for t in tags}
    assert used - set(PATTERNS) == set()


def test_every_problem_in_the_set_is_tagged():
    assert PROBLEM_SET - set(PROBLEM_PATTERNS) == set()


def test_no_tags_for_problems_outside_the_set():
    assert set(PROBLEM_PATTERNS) - PROBLEM_SET == set()


def test_no_orphan_patterns():
    """A pattern nothing maps to would render as an empty row."""
    used = {t for tags in PROBLEM_PATTERNS.values() for t in tags}
    assert set(PATTERNS) - used == set()


def test_fallback_targets_are_valid():
    assert set(CHAPTER_FALLBACK.values()) <= set(PATTERNS)


def test_pattern_template_links_point_at_real_templates():
    assert set(PATTERN_TEMPLATE) <= set(PATTERNS)
    assert set(PATTERN_TEMPLATE.values()) <= set(BY_NUMBER)


def test_cross_cutting_problems_are_tagged_by_technique_not_chapter():
    """The whole reason this axis exists."""
    assert "monotonic-stack" in patterns_for(239, 3)   # Sliding Window chapter
    assert "bellman-ford" in patterns_for(787, 12)     # Advanced Graphs chapter
    assert "backtracking" in patterns_for(22, 4)       # Stack chapter
    assert "fast-slow" in patterns_for(287, 6)         # Linked List chapter


def test_unknown_problem_falls_back_to_its_chapter():
    assert patterns_for(999999, 11) == ["graph-dfs"]
    assert patterns_for(999999, 999) == []
