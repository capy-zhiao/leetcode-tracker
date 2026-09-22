"""Request/response shapes (Pydantic v2).

Deliberately separate from the ORM models so internal schema changes don't leak into the API.
"""
from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from .srs import Difficulty, Grade


class StateOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    interval_days: int
    ease: float
    reps: int
    lapses: int
    due: date | None
    total_attempts: int
    best_seconds: int | None


class ProblemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    number: int
    title: str
    difficulty: str
    chapter_num: int
    chapter: str
    url: str
    in_neetcode150: bool
    kind: str
    state: StateOut | None = None


class ProblemDetail(ProblemOut):
    notes: str = ""
    code: str = ""


class QueueItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    problem: ProblemOut
    reason: str
    priority_score: float = 0.0
    overdue_days: int = 0


class DailyQueueOut(BaseModel):
    date: date
    reviews: list[QueueItemOut]
    new_problems: list[QueueItemOut]
    templates: list[QueueItemOut]
    total_due: int
    deferred: int


class AttemptIn(BaseModel):
    """Payload for recording one attempt."""
    grade: Grade
    seconds: int = Field(0, ge=0)
    looked_at_solution: bool = False
    had_bugs: bool = False
    mistakes: list[str] = Field(default_factory=list)
    code: str = ""
    note: str = ""
    mode: str = "practice"


class AttemptOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    problem_id: int
    created_at: datetime
    grade: str
    seconds: int
    mistakes: list[str]
    note: str
    mode: str
    code: str = ""


class AttemptResult(BaseModel):
    """Returned after submitting: the new SRS state plus when this problem comes back."""
    attempt: AttemptOut
    state: StateOut
    next_due_in_days: int


class GradeSuggestion(BaseModel):
    grade: Grade
    reason: str


class MistakeStat(BaseModel):
    id: str
    label: str
    hint: str
    count: int
    pct: float


class ChapterStat(BaseModel):
    chapter_num: int
    chapter: str
    total: int
    started: int
    mastered: int          # interval >= 21 days counts as mastered


class StatsOut(BaseModel):
    total_problems: int
    started: int
    mastered: int
    due_today: int
    attempts_total: int
    attempts_7d: int
    streak_days: int
    avg_seconds: int
    by_chapter: list[ChapterStat]
    top_mistakes: list[MistakeStat]


class FollowUpOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    question: str
    hint: str


class MockStartOut(BaseModel):
    problem: ProblemDetail
    minutes: int
    followups_ready: bool


class CodeReviewOut(BaseModel):
    summary: str
    issues: list[str]
    suggested_mistakes: list[str]
