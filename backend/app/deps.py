"""Shared dependencies and small helpers."""
from datetime import date, datetime, timezone
from zoneinfo import ZoneInfo

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


def _zone() -> ZoneInfo | None:
    """The configured study-day zone, or None meaning the machine's local zone."""
    if not settings.timezone:
        return None
    try:
        return ZoneInfo(settings.timezone)
    except Exception:                      # unknown zone name: fall back rather than crash
        return None


def today() -> date:
    """The current study day.

    Deliberately NOT the UTC date. Timestamps are stored in UTC, but a day boundary at
    00:00 UTC is 20:00 the previous evening in EDT, so an evening session would land on
    the next day: tomorrow's queue would appear at 8pm and the streak would break.
    """
    return datetime.now(_zone()).date()


def local_date(dt: datetime) -> date:
    """Which study day a stored timestamp belongs to.

    created_at is written as UTC but stored naive (the column has no timezone), so it has
    to be re-stamped as UTC before converting — otherwise astimezone() would read it as
    local time and shift it a second time.
    """
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(_zone()).date()
