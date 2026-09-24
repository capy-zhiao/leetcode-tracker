"""Problem browsing, detail view and note editing."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from ..database import get_db
from ..deps import get_problem
from ..models import Problem
from ..scheduler import roadmap_key
from ..schemas import ProblemDetail, ProblemOut

router = APIRouter(prefix="/problems", tags=["problems"])


@router.get("", response_model=list[ProblemOut])
def list_problems(
    db: Session = Depends(get_db),
    chapter: int | None = Query(None, description="Filter by chapter number"),
    difficulty: str | None = Query(None, description="Easy / Medium / Hard"),
    status_filter: str | None = Query(
        None, alias="status",
        description="new (never attempted) / learning (attempted, interval < 21d) / mastered"),
    q: str | None = Query(None, description="Search by title or problem number"),
    pattern: str | None = Query(None, description="Filter by algorithm pattern id"),
    kind: str = Query("problem", description="problem or template"),
):
    stmt = select(Problem).options(selectinload(Problem.state)).where(Problem.kind == kind)
    if chapter is not None:
        stmt = stmt.where(Problem.chapter_num == chapter)
    if difficulty:
        stmt = stmt.where(Problem.difficulty == difficulty)
    if q:
        if q.strip().isdigit():
            stmt = stmt.where(Problem.number == int(q.strip()))
        else:
            stmt = stmt.where(Problem.title.ilike(f"%{q}%"))

    # NeetCode's own order within a chapter (70, 746, 198 ...), additions after — the
    # same order the new-problem queue follows.
    items = sorted(db.scalars(stmt), key=roadmap_key)

    if pattern:
        # patterns is a JSON column; filtering in Python keeps this portable across
        # SQLite and Postgres, and 250 rows is far too few for it to matter.
        items = [p for p in items if pattern in (p.patterns or [])]

    if status_filter == "new":
        items = [p for p in items if not p.state or p.state.due is None]
    elif status_filter == "learning":
        items = [p for p in items if p.state and p.state.due and p.state.interval_days < 21]
    elif status_filter == "mastered":
        items = [p for p in items if p.state and p.state.interval_days >= 21]
    return items


@router.get("/{number}", response_model=ProblemDetail)
def problem_detail(problem: Problem = Depends(get_problem)):
    return problem


@router.patch("/{number}", response_model=ProblemDetail)
def update_problem(
    payload: dict,
    problem: Problem = Depends(get_problem),
    db: Session = Depends(get_db),
):
    """Update the notes or the stored solution."""
    for field in ("notes", "code"):
        if field in payload:
            setattr(problem, field, payload[field] or "")
    db.commit()
    db.refresh(problem)
    return problem
