"""共用的依赖和小工具。"""
from datetime import date, datetime, timezone

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from .config import settings
from .database import get_db
from .models import Problem, ReviewState


async def require_api_key(x_api_key: str | None = Header(default=None)) -> None:
    """部署到公网时用。settings.api_key 为空 = 本地开发,不校验。"""
    if settings.api_key and x_api_key != settings.api_key:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "无效的 API Key")


def get_problem(number: int, db: Session = Depends(get_db)) -> Problem:
    p = db.scalar(select(Problem).where(Problem.number == number))
    if p is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"找不到题目 {number}")
    return p


def ensure_state(db: Session, problem: Problem) -> ReviewState:
    """懒创建 SRS 状态 —— 题目第一次被做时才建行。"""
    if problem.state is None:
        st = ReviewState(problem_id=problem.id)
        db.add(st)
        db.flush()
        problem.state = st
    return problem.state


def today() -> date:
    return datetime.now(timezone.utc).date()
