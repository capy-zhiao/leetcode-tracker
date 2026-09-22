"""题库浏览 / 详情 / 笔记编辑。"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from ..constants import MISTAKE_TAGS
from ..database import get_db
from ..deps import get_problem
from ..models import Problem
from ..schemas import ProblemDetail, ProblemOut

router = APIRouter(prefix="/problems", tags=["problems"])


@router.get("", response_model=list[ProblemOut])
def list_problems(
    db: Session = Depends(get_db),
    chapter: int | None = Query(None, description="按章节号筛选"),
    difficulty: str | None = Query(None, description="Easy / Medium / Hard"),
    status_filter: str | None = Query(None, alias="status",
                                      description="new(没做过) / learning(做过但没掌握) / mastered(间隔≥21天)"),
    q: str | None = Query(None, description="标题或题号搜索"),
    kind: str = Query("problem", description="problem 或 template"),
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

    items = list(db.scalars(stmt.order_by(Problem.chapter_num, Problem.number)))

    if status_filter == "new":
        items = [p for p in items if not p.state or p.state.due is None]
    elif status_filter == "learning":
        items = [p for p in items if p.state and p.state.due and p.state.interval_days < 21]
    elif status_filter == "mastered":
        items = [p for p in items if p.state and p.state.interval_days >= 21]
    return items


@router.get("/mistake-tags")
def mistake_tags():
    """前端渲染「犯了什么错」选择器用。"""
    return MISTAKE_TAGS


@router.get("/{number}", response_model=ProblemDetail)
def problem_detail(problem: Problem = Depends(get_problem)):
    return problem


@router.patch("/{number}", response_model=ProblemDetail)
def update_problem(
    payload: dict,
    problem: Problem = Depends(get_problem),
    db: Session = Depends(get_db),
):
    """更新思路笔记或代码(做题页里随手记)。"""
    for field in ("notes", "code"):
        if field in payload:
            setattr(problem, field, payload[field] or "")
    db.commit()
    db.refresh(problem)
    return problem
