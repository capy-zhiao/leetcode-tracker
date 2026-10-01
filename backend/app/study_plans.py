"""LeetCode study plans and the app's full problem set.

The problem set is NeetCode 150 plus two LeetCode study plans, Top Interview 150 and
LeetCode 75 — 272 problems, since the lists overlap. Each plan lives in data/<plan>.json,
refreshed by scripts/fetch_study_plans.py.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from .neetcode150 import NEETCODE_150

DATA = Path(__file__).resolve().parents[2] / "data"


@dataclass(frozen=True)
class StudyPlan:
    slug: str                       # LeetCode's id, e.g. "top-interview-150"
    name: str
    label: str                      # short tag shown in the problem list
    problems: tuple[dict, ...]
    numbers: frozenset[int] = field(init=False)
    position: dict[int, int] = field(init=False)   # order within the plan

    def __post_init__(self):
        object.__setattr__(self, "numbers", frozenset(p["number"] for p in self.problems))
        object.__setattr__(self, "position", {p["number"]: p["position"] for p in self.problems})

    def url(self, problem_slug: str) -> str:
        return (f"https://leetcode.com/problems/{problem_slug}/description/"
                f"?envType=study-plan-v2&envId={self.slug}")


def _load(filename: str, label: str) -> StudyPlan:
    d = json.loads((DATA / filename).read_text())
    return StudyPlan(slug=d["slug"], name=d["plan"], label=label, problems=tuple(d["problems"]))


TOP_150_PLAN = _load("top_interview_150.json", "LC 150")
LC_75_PLAN = _load("leetcode_75.json", "LC 75")
# Order matters: new problems come from NeetCode 150, then these plans in this order.
# A problem in several plans belongs to the first one (its link and its place in line).
PLANS: tuple[StudyPlan, ...] = (TOP_150_PLAN, LC_75_PLAN)

TOP_150 = TOP_150_PLAN.numbers
LC_75 = LC_75_PLAN.numbers
PROBLEM_SET: frozenset[int] = NEETCODE_150 | TOP_150 | LC_75

CHAPTER_NAMES: dict[int, str] = {
    1: "Arrays & Hashing", 2: "Two Pointers", 3: "Sliding Window", 4: "Stack",
    5: "Binary Search", 6: "Linked List", 7: "Trees", 8: "Tries",
    9: "Heap / Priority Queue", 10: "Backtracking", 11: "Graphs", 12: "Advanced Graphs",
    13: "1-D DP", 14: "2-D DP", 15: "Greedy", 16: "Intervals",
    17: "Bit Manipulation", 18: "Math & Geometry",
}

# Study-plan group -> NeetCode roadmap chapter, for problems that aren't in NeetCode 150
# or the notes. Matrix goes to Math & Geometry because that's where NeetCode files
# 48 / 54 / 73; Queue and Monotonic Stack join Stack.
GROUP_CHAPTER: dict[str, int] = {
    # Top Interview 150
    "Array / String": 1, "Hashmap": 1, "Two Pointers": 2, "Sliding Window": 3,
    "Stack": 4, "Binary Search": 5, "Linked List": 6,
    "Binary Tree General": 7, "Binary Tree BFS": 7, "Binary Search Tree": 7,
    "Trie": 8, "Heap": 9, "Backtracking": 10,
    "Graph General": 11, "Graph BFS": 11,
    "1D DP": 13, "Multidimensional DP": 14, "Kadane's Algorithm": 15, "Intervals": 16,
    "Bit Manipulation": 17, "Math": 18, "Matrix": 18,
    # LeetCode 75
    "Prefix Sum": 1, "Hash Map / Set": 1, "Queue": 4, "Monotonic Stack": 4,
    "Binary Tree - DFS": 7, "Binary Tree - BFS": 7, "Heap / Priority Queue": 9,
    "Graphs - DFS": 11, "Graphs - BFS": 11, "DP - 1D": 13, "DP - Multidimensional": 14,
}
# "Divide & Conquer" mixes topics, so those are placed one by one
CHAPTER_OVERRIDES: dict[int, int] = {108: 7, 148: 6, 427: 7, 23: 6}


def chapter_for(number: int, group: str) -> int:
    return CHAPTER_OVERRIDES.get(number) or GROUP_CHAPTER[group]


def first_plan(number: int) -> StudyPlan | None:
    """The first plan (in PLANS order) that contains this problem."""
    return next((plan for plan in PLANS if number in plan.numbers), None)


def plan_entry(number: int) -> tuple[StudyPlan, dict] | None:
    plan = first_plan(number)
    if plan is None:
        return None
    return plan, next(p for p in plan.problems if p["number"] == number)
