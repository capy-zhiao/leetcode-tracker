"""Spaced Repetition Scheduling, tuned for coding problems.

Why not plain SM-2 (the Anki algorithm):
  - An Anki card takes 5 seconds and you can clear 200 a day; a LeetCode problem takes
    20-45 minutes and you can manage 6-8. => a daily cap plus priority ordering is
    mandatory (see priority()).
  - Anki asks you how well you remembered. Coding has harder signals: **time taken** and
    **whether you looked at the solution**. => suggest_grade() derives the grade from the
    timer instead of self-assessment.

Everything here is a **pure function**: no database access, no clock reads (`today` is a
parameter). That is what makes it fully unit-testable — see tests/test_srs.py.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import date, timedelta
from typing import Literal

Grade = Literal["again", "hard", "good", "easy"]
Difficulty = Literal["Easy", "Medium", "Hard"]

MIN_EASE, MAX_EASE, DEFAULT_EASE = 1.3, 3.0, 2.3
MAX_INTERVAL_DAYS = 365

# Interval (days) for the first review. After that it multiplies by `ease`.
FIRST_INTERVAL: dict[str, int] = {"again": 1, "hard": 2, "good": 4, "easy": 7}

# How each grade nudges the ease factor
EASE_DELTA: dict[str, float] = {"again": -0.20, "hard": -0.10, "good": 0.0, "easy": +0.10}

# Problem difficulty affects forgetting speed: hard problems decay faster, so shorter gaps
DIFFICULTY_FACTOR: dict[str, float] = {"Easy": 1.15, "Medium": 1.0, "Hard": 0.80}

# Weights used by priority()
W_OVERDUE, W_LAPSE, W_CHAPTER = 1.0, 3.0, 0.1
DIFFICULTY_PRIORITY = {"Easy": 0.0, "Medium": 1.0, "Hard": 2.0}


@dataclass(frozen=True)
class SrsState:
    """Review state for one problem.

    frozen=True means every review returns a *new* object instead of mutating in place,
    which keeps the function pure and the tests trivial.
    """
    interval_days: int = 0          # current gap between reviews
    ease: float = DEFAULT_EASE      # multiplier; higher = intervals grow faster
    reps: int = 0                   # consecutive successes (reset on a lapse)
    lapses: int = 0                 # lifetime failures (never reset; feeds priority)
    due: date | None = None         # next review date; None = not scheduled yet


def _clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


def review(
    state: SrsState,
    grade: Grade,
    difficulty: Difficulty = "Medium",
    today: date | None = None,
) -> SrsState:
    """Record one attempt and compute the next review state.

    Grades:
      again — didn't get it / looked at the solution -> back tomorrow, ease drops
      hard  — struggled >15 min or had bugs          -> interval barely grows
      good  — solved smoothly (5-15 min)             -> interval * ease
      easy  — nailed it (<5 min, first try)          -> interval * ease * 1.3, ease rises
    """
    if grade not in FIRST_INTERVAL:
        raise ValueError(f"unknown grade: {grade!r}")
    today = today or date.today()

    ease = _clamp(state.ease + EASE_DELTA[grade], MIN_EASE, MAX_EASE)

    if grade == "again":
        # Lapse: reset the interval to one day, clear reps, record the failure
        interval = 1
        reps = 0
        lapses = state.lapses + 1
    else:
        reps = state.reps + 1
        lapses = state.lapses
        if state.reps == 0 or state.interval_days == 0:
            interval = FIRST_INTERVAL[grade]        # first time, or just after a lapse
        elif grade == "hard":
            interval = max(1, round(state.interval_days * 1.2))
        elif grade == "good":
            interval = round(state.interval_days * ease)
        else:  # easy
            interval = round(state.interval_days * ease * 1.3)
        # Weight by problem difficulty: hard problems get ~20% shorter gaps
        interval = max(1, round(interval * DIFFICULTY_FACTOR.get(difficulty, 1.0)))

    interval = min(interval, MAX_INTERVAL_DAYS)
    return replace(
        state,
        interval_days=interval,
        ease=round(ease, 3),
        reps=reps,
        lapses=lapses,
        due=today + timedelta(days=interval),
    )


def suggest_grade(
    seconds: int,
    looked_at_solution: bool,
    had_bugs: bool = False,
    difficulty: Difficulty = "Medium",
) -> Grade:
    """Derive a grade from the timer and what actually happened.
    The UI pre-selects the result so grading is one click, not a judgement call.

    Thresholds scale with difficulty — 20 minutes on a Hard problem is fine,
    20 minutes on an Easy one means you were stuck.
    """
    if looked_at_solution:
        return "again"
    scale = {"Easy": 0.6, "Medium": 1.0, "Hard": 1.6}.get(difficulty, 1.0)
    minutes = seconds / 60
    if had_bugs or minutes > 15 * scale:
        return "hard"
    if minutes <= 5 * scale:
        return "easy"
    return "good"


def priority(
    state: SrsState,
    today: date,
    difficulty: Difficulty = "Medium",
    chapter_num: int = 1,
) -> float:
    """Ranking score for due problems (higher goes first).

    Twenty problems may come due on the same day when you can only do four, so the queue
    has to be ordered: the longer it is overdue, the more times you have failed it, the
    harder it is, and the earlier its chapter (foundations first), the sooner it surfaces.
    """
    if state.due is None:
        return 0.0
    overdue_days = (today - state.due).days
    return (
        overdue_days * W_OVERDUE
        + state.lapses * W_LAPSE
        + DIFFICULTY_PRIORITY.get(difficulty, 1.0)
        + (20 - chapter_num) * W_CHAPTER
    )


def is_due(state: SrsState, today: date) -> bool:
    return state.due is not None and state.due <= today
