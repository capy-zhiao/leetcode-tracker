"""Builds the daily queue.

Every day you get three things:
  1. Due reviews  — what SRS says is due, ranked by priority(), capped at N
  2. New problems — roadmap order (chapter, then number), one per chapter, Hards last
  3. A template   — one of the 15 algorithm templates, also on an SRS schedule

Key design decision: **overflow defers**. Twenty problems may be due on a day you can only
finish four. Rather than dumping all twenty, the queue hands you the N that matter most and
rolls the rest forward.

Second decision: **the day is interleaved**. Ranking alone clusters: failures concentrate
in whichever chapter was hardest, so the top four can all be graph problems. Four of the
same kind in a row means you know the technique before reading the problem, which skips
the step an interview actually tests — recognising it. pick_diverse() caps each chapter
and each primary pattern per day, then backfills so no slot goes unused.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from .config import settings
from .models import Problem, ReviewState
from .patterns import patterns_for
from .srs import priority


@dataclass
class QueueItem:
    problem: Problem
    reason: str                 # "due" | "new" | "template"
    priority_score: float = 0.0
    overdue_days: int = 0


@dataclass
class DailyQueue:
    reviews: list[QueueItem] = field(default_factory=list)
    new_problems: list[QueueItem] = field(default_factory=list)
    templates: list[QueueItem] = field(default_factory=list)
    total_due: int = 0          # how many are actually due (can exceed len(reviews))
    deferred: int = 0           # how many were pushed to a later day by the cap


def primary_pattern(problem) -> str | None:
    """The first pattern tag — the technique the problem is mainly testing."""
    tags = problem.patterns or patterns_for(problem.number, problem.chapter_num)
    return tags[0] if tags else None


def pick_diverse(
    items: list[QueueItem],
    cap: int,
    per_chapter: int,
    per_pattern: int,
) -> list[QueueItem]:
    """Take up to `cap` items in the given order, spreading across chapters and patterns.

    `items` must already be in preference order — by priority for reviews, by roadmap
    position for new problems — and the result keeps that order. An item is skipped when
    its chapter or its primary pattern already has its quota for the day; a limit of 0
    means unlimited. Skipped items then backfill any slot still empty, in that same order,
    so the rules only ever change which problems you get — never how many.

    Pure function (no database, no clock), so it is unit tested directly.
    """
    picked: list[tuple[int, QueueItem]] = []
    skipped: list[tuple[int, QueueItem]] = []
    by_chapter: Counter[int] = Counter()
    by_pattern: Counter[str] = Counter()

    for pos, item in enumerate(items):
        if len(picked) >= cap:
            break
        ch = item.problem.chapter_num
        pat = primary_pattern(item.problem)
        chapter_full = per_chapter > 0 and by_chapter[ch] >= per_chapter
        pattern_full = per_pattern > 0 and pat is not None and by_pattern[pat] >= per_pattern
        if chapter_full or pattern_full:
            skipped.append((pos, item))
            continue
        picked.append((pos, item))
        by_chapter[ch] += 1
        if pat is not None:
            by_pattern[pat] += 1

    # Everything skipped outranks everything not yet visited, so backfill from it first.
    for entry in skipped:
        if len(picked) >= cap:
            break
        picked.append(entry)

    picked.sort(key=lambda e: e[0])
    return [item for _, item in picked]


def new_problem_order(problem, hard_last: bool = True) -> tuple:
    """Sort key for unstarted problems: roadmap order, optionally with every Hard last."""
    held_back = hard_last and problem.difficulty == "Hard"
    return (held_back, problem.chapter_num, problem.number)


def _load(db: Session, kind: str) -> list[Problem]:
    stmt = (
        select(Problem)
        .options(selectinload(Problem.state))
        .where(Problem.kind == kind)
    )
    return list(db.scalars(stmt))


def build_today(
    db: Session,
    today: date | None = None,
    review_cap: int | None = None,
    new_cap: int | None = None,
) -> DailyQueue:
    today = today or date.today()
    review_cap = review_cap if review_cap is not None else settings.daily_review_cap
    new_cap = new_cap if new_cap is not None else settings.daily_new_cap

    problems = _load(db, "problem")
    queue = DailyQueue()

    # --- 1. Due reviews, ranked, capped ---
    due_items: list[QueueItem] = []
    for p in problems:
        st = p.state
        if st is None or st.due is None or st.due > today:
            continue
        s = st.to_srs()
        due_items.append(QueueItem(
            problem=p,
            reason="due",
            priority_score=priority(s, today, p.difficulty, p.chapter_num),
            overdue_days=(today - st.due).days,
        ))
    due_items.sort(key=lambda i: i.priority_score, reverse=True)
    queue.total_due = len(due_items)
    queue.reviews = pick_diverse(
        due_items, review_cap,
        settings.daily_per_chapter_cap, settings.daily_per_pattern_cap,
    )
    queue.deferred = len(due_items) - len(queue.reviews)

    # --- 2. New problems: roadmap order, one per chapter, Hards held back ---
    fresh = [p for p in problems if p.state is None or p.state.due is None]
    fresh.sort(key=lambda p: new_problem_order(p, settings.new_hard_last))
    queue.new_problems = pick_diverse(
        [QueueItem(problem=p, reason="new") for p in fresh], new_cap,
        settings.daily_new_per_chapter_cap, settings.daily_per_pattern_cap,
    )

    # --- 3. One template: the due one, otherwise whichever has gone longest untouched ---
    templates = _load(db, "template")
    t_due = [t for t in templates if t.state and t.state.due and t.state.due <= today]
    if t_due:
        t_due.sort(key=lambda t: (t.state.due, -t.state.lapses))
        pick = t_due[0]
    elif templates:
        pick = min(templates, key=lambda t: (
            t.state.last_attempt_at if t.state and t.state.last_attempt_at else 0,
        ))
    else:
        pick = None
    if pick is not None:
        queue.templates = [QueueItem(problem=pick, reason="template")]

    return queue


def forecast(db: Session, today: date | None = None, days: int = 14) -> list[dict]:
    """Review load for the next N days, so the UI can warn you before a pile-up."""
    today = today or date.today()
    counts = {today + timedelta(days=i): 0 for i in range(days)}
    overdue = 0
    for st in db.scalars(select(ReviewState).where(ReviewState.due.is_not(None))):
        if st.due < today:
            overdue += 1
        elif st.due in counts:
            counts[st.due] += 1
    out = [{"date": today.isoformat(), "count": counts[today] + overdue, "overdue": overdue}]
    out += [{"date": d.isoformat(), "count": c, "overdue": 0}
            for d, c in sorted(counts.items()) if d != today]
    return out
