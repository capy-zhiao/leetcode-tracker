"""Blind-write grading.

The load-bearing property is that grading tracks CORRECTNESS, not text similarity — a
renamed-but-correct implementation must pass, and a near-identical but broken one must not.
"""
import pytest

from app.blindwrite import grade, normalize, similarity, suggested_grade
from app.templates_ref import TEMPLATES


@pytest.mark.parametrize("tpl", TEMPLATES, ids=lambda t: f"{t.number}-{t.name}")
def test_reference_passes_its_own_checks(tpl):
    """A checkpoint the reference itself fails is a bug in the checkpoint."""
    result = grade(tpl.number, tpl.reference)
    assert result.passed, f"{tpl.name} reference misses: {result.missing}"
    assert result.similarity == pytest.approx(1.0)


def test_unknown_template_returns_none():
    assert grade(1234, "whatever") is None


def test_empty_submission_fails_cleanly():
    r = grade(9001, "")
    assert not r.passed
    assert r.similarity == 0.0
    assert "Nothing written" in r.verdict


def test_normalize_ignores_comments_and_blank_lines():
    a = normalize("x = 1\n\n# a comment\ny = 2\n")
    b = normalize("x = 1\ny = 2")
    assert a == b


def test_normalize_keeps_hash_inside_a_string():
    assert normalize("s = '# not a comment'") == ["s = '# not a comment'"]


def test_renamed_variables_still_pass():
    """Correct Union-Find with every identifier renamed — must pass despite low similarity."""
    written = """
par = [i for i in range(n)]
def root(v):
    while par[v] != v:
        par[v] = par[par[v]]
        v = par[v]
    return v
def join(u, v):
    ru, rv = root(u), root(v)
    if ru == rv:
        return False
    par[ru] = rv
    return True
"""
    r = grade(9001, written)
    assert r.passed, f"missing: {r.missing}"
    assert r.similarity < 0.6, "this is the point: it passes on checks, not on text match"


def test_union_find_with_if_instead_of_while_is_caught():
    """The real 261 bug: find() climbs one level and stops."""
    written = """
parent = list(range(n))
def find(x):
    if parent[x] != x:
        x = parent[x]
    return x

def union(a, b):
    ra, rb = find(a), find(b)
    if ra == rb:
        return False
    parent[ra] = rb
    return True
"""
    r = grade(9001, written)
    assert not r.passed
    assert any("while" in m for m in r.missing)
    assert r.similarity > 0.8, "near-identical text, still correctly rejected"


def test_grid_dfs_missing_visited_guard_is_caught():
    written = """
def dfs(r, c):
    if r < 0 or c < 0 or r >= ROWS or c >= COLS: return
    if grid[r][c] != TARGET: return
    dfs(r+1, c); dfs(r-1, c); dfs(r, c+1); dfs(r, c-1)
"""
    r = grade(9002, written)
    assert not r.passed
    assert any("visited" in m for m in r.missing)


def test_binary_search_without_plus_one_is_caught():
    written = """
left, right = 0, len(nums) - 1
while left <= right:
    mid = (left + right) // 2
    if nums[mid] == target: return mid
    elif nums[mid] < target: left = mid
    else: right = mid
return -1
"""
    r = grade(9006, written)
    assert not r.passed
    assert len(r.missing) == 2, "both the +1 and the -1 checkpoints should fire"


def test_suggested_grade_maps_onto_srs_grades():
    perfect = grade(9006, next(t for t in TEMPLATES if t.number == 9006).reference)
    assert suggested_grade(perfect) == "easy"

    broken = grade(9001, "def find(x):\n    return x")
    assert suggested_grade(broken) == "again"


def test_diff_is_produced_for_a_wrong_answer():
    r = grade(9006, "left = 0\nreturn -1")
    assert r.diff, "a failing attempt should come with something to read"
    assert any(line.startswith("-") for line in r.diff)
