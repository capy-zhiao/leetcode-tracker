"""Stats dashboard. The mistake ranking is the most personally useful part."""
from collections import Counter
from datetime import timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from ..constants import MISTAKE_TAGS
from ..database import get_db
from ..deps import today as get_today
from ..models import Attempt, Problem
from ..schemas import ChapterStat, MistakeStat, StatsOut

router = APIRouter(prefix="/stats", tags=["stats"])

MASTERED_INTERVAL = 21   # an interval of 21+ days counts as "mastered"


def _streak(db: Session) -> int:
    """Consecutive days with at least one attempt, counting back from today."""
    days = {
        d for (d,) in db.execute(
            select(func.date(Attempt.created_at)).distinct()
        ) if d
    }
    days = {str(d)[:10] for d in days}
    if not days:
        return 0
    cur = get_today()
    if cur.isoformat() not in days:
        cur = cur - timedelta(days=1)      # nothing today yet, so start from yesterday
        if cur.isoformat() not in days:
            return 0
    n = 0
    while cur.isoformat() in days:
        n += 1
        cur -= timedelta(days=1)
    return n


@router.get("", response_model=StatsOut)
def overview(db: Session = Depends(get_db)):
    d = get_today()
    problems = list(db.scalars(
        select(Problem).options(selectinload(Problem.state)).where(Problem.kind == "problem")
    ))

    started = sum(1 for p in problems if p.state and p.state.due)
    mastered = sum(1 for p in problems if p.state and p.state.interval_days >= MASTERED_INTERVAL)
    due_today = sum(1 for p in problems if p.state and p.state.due and p.state.due <= d)

    attempts = list(db.scalars(select(Attempt)))
    week_ago = d - timedelta(days=7)
    attempts_7d = sum(1 for a in attempts if a.created_at.date() >= week_ago)
    timed = [a.seconds for a in attempts if a.seconds > 0]

    by_chapter: list[ChapterStat] = []
    for ch in sorted({p.chapter_num for p in problems}):
        g = [p for p in problems if p.chapter_num == ch]
        by_chapter.append(ChapterStat(
            chapter_num=ch, chapter=g[0].chapter, total=len(g),
            started=sum(1 for p in g if p.state and p.state.due),
            mastered=sum(1 for p in g if p.state and p.state.interval_days >= MASTERED_INTERVAL),
        ))

    return StatsOut(
        total_problems=len(problems), started=started, mastered=mastered,
        due_today=due_today, attempts_total=len(attempts), attempts_7d=attempts_7d,
        streak_days=_streak(db),
        avg_seconds=int(sum(timed) / len(timed)) if timed else 0,
        by_chapter=by_chapter,
        top_mistakes=mistake_ranking(db),
    )


@router.get("/mistakes", response_model=list[MistakeStat])
def mistake_ranking(db: Session = Depends(get_db)) -> list[MistakeStat]:
    """Your mistake ranking — with enough data this becomes a personal pre-submit checklist."""
    counter: Counter[str] = Counter()
    for a in db.scalars(select(Attempt)):
        counter.update(a.mistakes or [])
    total = sum(counter.values())
    meta = {t["id"]: t for t in MISTAKE_TAGS}
    return [
        MistakeStat(
            id=mid, label=meta[mid]["label"], hint=meta[mid]["hint"],
            count=cnt, pct=round(cnt / total * 100, 1) if total else 0.0,
        )
        for mid, cnt in counter.most_common()
        if mid in meta
    ]


@router.get("/heatmap")
def heatmap(db: Session = Depends(get_db), days: int = 90):
    """Attempts per day for the last N days — a GitHub-style contribution grid."""
    start = get_today() - timedelta(days=days)
    counter: Counter[str] = Counter()
    for a in db.scalars(select(Attempt)):
        day = a.created_at.date()
        if day >= start:
            counter[day.isoformat()] += 1
    return [{"date": k, "count": v} for k, v in sorted(counter.items())]
