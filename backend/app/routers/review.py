"""Daily queue and attempt submission — the entry point into the SRS engine."""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import ensure_state, get_problem, today as get_today
from ..models import Attempt, Problem
from ..schemas import (
    AttemptIn, AttemptOut, AttemptResult, DailyQueueOut,
    GradeSuggestion, StateOut,
)
from ..scheduler import build_today, forecast
from ..srs import review as srs_review, suggest_grade

router = APIRouter(prefix="/review", tags=["review"])


@router.get("/today", response_model=DailyQueueOut)
def today_queue(
    db: Session = Depends(get_db),
    review_cap: int | None = Query(None, ge=0, le=50),
    new_cap: int | None = Query(None, ge=0, le=50),
):
    """What to work on today — this powers the home screen."""
    d = get_today()
    q = build_today(db, d, review_cap, new_cap)
    return DailyQueueOut(
        date=d,
        reviews=q.reviews, new_problems=q.new_problems, templates=q.templates,
        total_due=q.total_due, deferred=q.deferred,
    )


@router.get("/forecast")
def review_forecast(db: Session = Depends(get_db), days: int = Query(14, ge=1, le=60)):
    """Upcoming review load, rendered as a bar chart in the UI."""
    return forecast(db, get_today(), days)


@router.get("/suggest-grade", response_model=GradeSuggestion)
def grade_suggestion(
    seconds: int = Query(..., ge=0),
    looked_at_solution: bool = False,
    had_bugs: bool = False,
    difficulty: str = "Medium",
):
    """Called when the timer stops; the UI pre-selects the returned grade."""
    g = suggest_grade(seconds, looked_at_solution, had_bugs, difficulty)  # type: ignore[arg-type]
    mins = seconds / 60
    reason = {
        "again": "Looked at the solution — back tomorrow",
        "hard": f"Took {mins:.0f} min or hit bugs — interval grows only slightly",
        "good": f"Solved smoothly in {mins:.0f} min",
        "easy": f"Nailed it in {mins:.0f} min — interval stretches a lot",
    }[g]
    return GradeSuggestion(grade=g, reason=reason)


@router.post("/{number}/attempt", response_model=AttemptResult)
def submit_attempt(
    payload: AttemptIn,
    problem: Problem = Depends(get_problem),
    db: Session = Depends(get_db),
):
    """Record an attempt and let SRS compute the next review date."""
    d = get_today()
    st = ensure_state(db, problem)

    # 1. Store this attempt
    attempt = Attempt(
        problem_id=problem.id,
        grade=payload.grade,
        seconds=payload.seconds,
        looked_at_solution=payload.looked_at_solution,
        had_bugs=payload.had_bugs,
        mistakes=payload.mistakes,
        code=payload.code,
        note=payload.note,
        mode=payload.mode,
    )
    db.add(attempt)

    # 2. Run the SRS step (pure function, easy to test)
    new_state = srs_review(st.to_srs(), payload.grade, problem.difficulty, d)  # type: ignore[arg-type]
    st.apply(new_state)
    st.total_attempts += 1
    st.last_attempt_at = datetime.now(timezone.utc)
    if payload.seconds > 0 and (st.best_seconds is None or payload.seconds < st.best_seconds):
        st.best_seconds = payload.seconds

    # 3. Keep the latest solution on the problem so the next pass can diff against it
    if payload.code.strip():
        problem.code = payload.code

    db.commit()
    db.refresh(attempt)
    db.refresh(st)
    return AttemptResult(
        attempt=AttemptOut.model_validate(attempt),
        state=StateOut.model_validate(st),
        next_due_in_days=new_state.interval_days,
    )


@router.get("/{number}/attempts", response_model=list[AttemptOut])
def attempt_history(problem: Problem = Depends(get_problem)):
    """History for this problem — lets you diff this attempt against the previous one."""
    return problem.attempts
