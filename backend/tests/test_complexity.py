"""Complexity normalization and grading."""
import pytest

from app.complexity import COMPLEXITY_CHOICES, EXPECTED, check, matches, normalize


@pytest.mark.parametrize("a,b", [
    ("O(m * n)", "O(n*m)"),
    ("O(n log n)", "O(N * LogN)"),
    ("O(n^2)", "O(n**2)"),
    ("O(m + n)", "O(n + m)"),
    ("O(n)", "  o(N) "),
    ("O(sqrt n)", "O(SQRT N)"),
    # Typed without spaces around the +, which is how people actually write it
    ("O(V + E)", "O(V+E)"),
    ("O(m + n)", "O(m+n)"),
    ("O(m + n)", "O(N+M)"),
    ("O(log (m + n))", "O(log(m+n))"),
])
def test_equivalent_spellings_collapse(a, b):
    assert normalize(a) == normalize(b)


@pytest.mark.parametrize("a,b", [
    ("O(n)", "O(n^2)"),
    ("O(m + n)", "O(m * n)"),
    ("O(log n)", "O(n log n)"),
    ("O(1)", "O(n)"),
    ("O(2^n)", "O(n^2)"),
])
def test_distinct_complexities_stay_distinct(a, b):
    assert normalize(a) != normalize(b)


def test_every_picker_choice_parses():
    assert all(normalize(c) for c in COMPLEXITY_CHOICES)


def test_all_expected_answers_parse():
    """A reference answer that normalizes to nothing could never be matched."""
    for num, (times, spaces) in EXPECTED.items():
        for ans in times + spaces:
            assert normalize(ans), f"#{num}: {ans!r} normalizes to empty"


def test_grades_a_correct_answer():
    v = check(200, "O(m*n)", "O(m * n)")          # Number of Islands
    assert v["time_ok"] and v["space_ok"]


def test_grades_a_wrong_answer_and_reports_the_reference():
    v = check(200, "O(n)", "O(1)")
    assert not v["time_ok"] and not v["space_ok"]
    assert v["expected_time"] == "O(m * n)"


def test_ambiguous_answers_both_accepted():
    """3Sum's space is O(1) or O(n) depending on whether the sort counts. Accept both."""
    assert check(15, "O(n^2)", "O(1)")["space_ok"]
    assert check(15, "O(n^2)", "O(n)")["space_ok"]


def test_ungraded_problem_returns_none():
    assert check(999999, "O(n)", "O(n)") is None


def test_blank_answer_never_matches():
    assert not matches("", ["O(n)"])


def test_coverage_is_substantial():
    assert len(EXPECTED) >= 200, "most of the 250 should have a reference answer"


def test_clone_graph_space_is_the_visited_map_not_the_edges():
    """oldtonew holds V entries and the recursion is at most V deep: O(V), which is
    O(n) when n counts nodes. Time still has to include the edges."""
    v = check(133, "O(n)", "O(n)")
    assert v["space_ok"]
    assert not v["time_ok"], "a dense graph has ~V^2 edges; O(n) time understates it"
    assert check(133, "O(V+E)", "O(V)")["time_ok"]
    assert check(133, "O(V+E)", "O(V + E)")["space_ok"], "counting the output is fine too"


def test_union_find_problems_accept_the_parent_array_space():
    for num in (261, 323):
        assert check(num, "O(V + E)", "O(n)")["space_ok"], num


def test_graph_valid_tree_time_is_linear_after_the_edge_check():
    assert check(261, "O(n)", "O(n)")["time_ok"]
    assert not check(323, "O(n)", "O(n)")["time_ok"], "323 has no edge-count guard"
