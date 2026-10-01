"""LeetCode's Top Interview 150 study plan, and the app's full problem set.

The problem set is NeetCode 150 plus Top Interview 150 (223 problems; 77 are in both).
The list itself lives in data/top_interview_150.json, refreshed by
scripts/fetch_top_interview_150.py.
"""
from __future__ import annotations

import json
from pathlib import Path

from .neetcode150 import NEETCODE_150

DATA = Path(__file__).resolve().parents[2] / "data" / "top_interview_150.json"

TOP_150_PROBLEMS: list[dict] = json.loads(DATA.read_text())["problems"]
TOP_150: frozenset[int] = frozenset(p["number"] for p in TOP_150_PROBLEMS)
TOP_150_POSITION: dict[int, int] = {p["number"]: p["position"] for p in TOP_150_PROBLEMS}

PROBLEM_SET: frozenset[int] = NEETCODE_150 | TOP_150

CHAPTER_NAMES: dict[int, str] = {
    1: "Arrays & Hashing", 2: "Two Pointers", 3: "Sliding Window", 4: "Stack",
    5: "Binary Search", 6: "Linked List", 7: "Trees", 8: "Tries",
    9: "Heap / Priority Queue", 10: "Backtracking", 11: "Graphs", 12: "Advanced Graphs",
    13: "1-D DP", 14: "2-D DP", 15: "Greedy", 16: "Intervals",
    17: "Bit Manipulation", 18: "Math & Geometry",
}

# Study-plan group -> NeetCode roadmap chapter, for problems that aren't in NeetCode 150.
# Matrix goes to Math & Geometry because that's where NeetCode files 48 / 54 / 73.
GROUP_CHAPTER: dict[str, int] = {
    "Array / String": 1, "Hashmap": 1, "Two Pointers": 2, "Sliding Window": 3,
    "Stack": 4, "Binary Search": 5, "Linked List": 6,
    "Binary Tree General": 7, "Binary Tree BFS": 7, "Binary Search Tree": 7,
    "Trie": 8, "Heap": 9, "Backtracking": 10,
    "Graph General": 11, "Graph BFS": 11,
    "1D DP": 13, "Multidimensional DP": 14, "Kadane's Algorithm": 15, "Intervals": 16,
    "Bit Manipulation": 17, "Math": 18, "Matrix": 18,
}
# "Divide & Conquer" mixes topics, so those are placed one by one
CHAPTER_OVERRIDES: dict[int, int] = {108: 7, 148: 6, 427: 7, 23: 6}


def chapter_for(number: int, group: str) -> int:
    return CHAPTER_OVERRIDES.get(number) or GROUP_CHAPTER[group]


def leetcode_url(slug: str) -> str:
    return (f"https://leetcode.com/problems/{slug}/description/"
            f"?envType=study-plan-v2&envId=top-interview-150")
