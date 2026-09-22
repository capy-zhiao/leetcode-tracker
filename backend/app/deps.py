"""Shared dependencies and small helpers."""
from datetime import date, datetime, timezone

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from .config import settings
from .database import get_db
from .models import Problem, ReviewState


async def require_api_key(x_api_key: str | None = Header(default=None)) -> None:
    """Used when deployed publicly. An empty settings.api_key means local dev: no auth."""
    if settings.api_key and x_api_key != settings.api_key:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid API key")


def get_problem(number: int, db: Session = Depends(get_db)) -> Problem:
    p = db.scalar(select(Problem).where(Problem.number == number))
    if p is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"No problem numbered {number}")
    return p


def ensure_state(db: Session, problem: Problem) -> ReviewState:
    """Lazily create the SRS row the first time a problem is attempted."""
    if problem.state is None:
        st = ReviewState(problem_id=problem.id)
        db.add(st)
        db.flush()
        problem.state = st
    return problem.state


def today() -> date:
    return datetime.now(timezone.utc).date()
