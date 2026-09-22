"""Builds the daily queue.

Every day you get three things:
  1. Due reviews  — what SRS says is due, ranked by priority(), capped at N
  2. New problems — the next items in NeetCode roadmap order (chapter, then number)
  3. A template   — one of the 15 algorithm templates, also on an SRS schedule

Key design decision: **overflow defers**. Twenty problems may be due on a day you can only
finish four. Rather than dumping all twenty, the queue hands you the N that matter most and
rolls the rest forward.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from .config import settings
from .models import Problem, ReviewState
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
    queue.reviews = due_items[:review_cap]
    queue.deferred = max(0, len(due_items) - review_cap)

    # --- 2. New problems, in roadmap order ---
    fresh = [p for p in problems if p.state is None or p.state.due is None]
    fresh.sort(key=lambda p: (p.chapter_num, p.number))
    queue.new_problems = [QueueItem(problem=p, reason="new") for p in fresh[:new_cap]]

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
