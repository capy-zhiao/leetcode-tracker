"""每日队列生成。

每天给你三样东西(结构照搬你手工维护的 REVIEW.md,但自动算):
  1. 到期复习 —— SRS 说今天该复习的,按 priority 排序后取前 N 道
  2. 新题     —— 按 NeetCode roadmap 顺序(章节 -> 题号)往下推
  3. 模板盲写 —— 15 个算法模板,同样走 SRS

关键设计:**溢出顺延**。某天可能 20 道同时到期,但你做不完 20 道。
所以不是「全给你」,而是「按优先级给你最该做的 N 道」,剩下的自动顺延到明天。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

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
    total_due: int = 0          # 今天实际到期多少道(可能 > len(reviews))
    deferred: int = 0           # 因为超上限被顺延的道数


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

    # --- 1. 到期复习:按优先级排,取前 N ---
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

    # --- 2. 新题:没做过的,按 roadmap 顺序 ---
    fresh = [p for p in problems if p.state is None or p.state.due is None]
    fresh.sort(key=lambda p: (p.chapter_num, p.number))
    queue.new_problems = [QueueItem(problem=p, reason="new") for p in fresh[:new_cap]]

    # --- 3. 模板盲写:到期的取 1 个,没到期的就轮一个最久没写的 ---
    templates = _load(db, "template")
    t_due = [t for t in templates if t.state and t.state.due and t.state.due <= today]
    if t_due:
        t_due.sort(key=lambda t: (t.state.due, -t.state.lapses))
        pick = t_due[0]
    elif templates:
        # 没到期的话挑一个「最久没碰」的保温
        pick = min(templates, key=lambda t: (
            t.state.last_attempt_at if t.state and t.state.last_attempt_at else 0,
        ))
    else:
        pick = None
    if pick is not None:
        queue.templates = [QueueItem(problem=pick, reason="template")]

    return queue


def forecast(db: Session, today: date | None = None, days: int = 14) -> list[dict]:
    """未来 N 天的复习负载预测 —— 前端画个小柱状图,让你知道哪天会爆。"""
    from datetime import timedelta

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
