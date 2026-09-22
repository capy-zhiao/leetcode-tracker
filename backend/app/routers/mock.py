"""Mock interview: random problem, timer, interviewer follow-ups, AI code review.

Follow-ups are generated once by the configured LLM and cached in the database,
so each problem costs a single API call for its lifetime.
"""
import random

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from .. import llm
from ..database import get_db
from ..deps import get_problem
from ..models import FollowUp, Problem
from ..schemas import CodeReviewOut, FollowUpOut, MockStartOut, ProblemDetail

router = APIRouter(prefix="/mock", tags=["mock"])

DEFAULT_MINUTES = {"Easy": 20, "Medium": 35, "Hard": 45}

# Used when no LLM provider is configured, so the feature still works offline.
GENERIC_FOLLOWUPS = [
    ("What is the time and space complexity of your solution? Can it be improved?",
     "State where the current complexity comes from, then identify the bottleneck step."),
    ("What are the edge cases? Empty input, a single element, all elements identical?",
     "Name two or three concrete inputs and say what each should return."),
    ("If the input grew to a billion elements, would your approach still hold?",
     "Discuss memory limits, streaming, sharding, or an external-sort style approach."),
]


@router.post("/start", response_model=MockStartOut)
def start_mock(
    db: Session = Depends(get_db),
    difficulty: str | None = Query(None, description="Restrict to a difficulty"),
    chapter: int | None = Query(None, description="Restrict to a chapter"),
    only_solved: bool = Query(False, description="Only draw problems you have solved before"),
):
    """Draw a random problem and start a mock interview."""
    stmt = select(Problem).options(selectinload(Problem.state)).where(Problem.kind == "problem")
    if difficulty:
        stmt = stmt.where(Problem.difficulty == difficulty)
    if chapter is not None:
        stmt = stmt.where(Problem.chapter_num == chapter)

    pool = list(db.scalars(stmt))
    if only_solved:
        pool = [p for p in pool if p.state and p.state.due]
    if not pool:
        raise HTTPException(404, "No problems match those filters")

    p = random.choice(pool)
    return MockStartOut(
        problem=ProblemDetail.model_validate(p),
        minutes=DEFAULT_MINUTES.get(p.difficulty, 35),
        followups_ready=bool(p.followups) or llm.is_enabled(),
    )


@router.get("/{number}/followups", response_model=list[FollowUpOut])
def get_followups(
    problem: Problem = Depends(get_problem),
    db: Session = Depends(get_db),
    regenerate: bool = Query(False),
):
    """Fetch follow-ups for a problem, generating and caching them on first request."""
    if problem.followups and not regenerate:
        return problem.followups

    if regenerate:
        for f in problem.followups:
            db.delete(f)
        db.flush()

    items = llm.generate_followups(
        problem.title, problem.number, problem.difficulty, problem.chapter
    )
    if not items:
        # No provider configured, or the call failed — fall back so the flow never breaks
        items = [llm.FollowUpItem(question=q, hint=h) for q, h in GENERIC_FOLLOWUPS]

    rows = [FollowUp(problem_id=problem.id, question=i.question, hint=i.hint) for i in items]
    db.add_all(rows)
    db.commit()
    for r in rows:
        db.refresh(r)
    return rows


@router.post("/{number}/review-code", response_model=CodeReviewOut)
def ai_code_review(
    payload: dict,
    problem: Problem = Depends(get_problem),
):
    """Send the solution to the configured LLM for review, including which mistake tags apply."""
    code = (payload or {}).get("code", "")
    if not code.strip():
        raise HTTPException(400, "Code cannot be empty")
    if not llm.is_enabled():
        raise HTTPException(503, "AI review unavailable — set LLM_PROVIDER and the matching API key")

    result = llm.review_code(problem.title, problem.number, problem.difficulty, code)
    if result is None:
        raise HTTPException(502, "The LLM call failed, please try again")
    return CodeReviewOut(
        summary=result.summary,
        issues=result.issues,
        suggested_mistakes=result.suggested_mistakes,
    )
