"""Mock interview:随机抽题 + 计时 + 面试官追问 + AI code review。

Follow-up 由 Claude 生成并缓存进 DB —— 同一道题只调一次 API。
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


@router.post("/start", response_model=MockStartOut)
def start_mock(
    db: Session = Depends(get_db),
    difficulty: str | None = Query(None, description="限定难度"),
    chapter: int | None = Query(None, description="限定章节"),
    only_solved: bool = Query(False, description="只抽做过的题(练讲解),默认全库"),
):
    """随机抽一道题开始模拟面试。"""
    stmt = select(Problem).options(selectinload(Problem.state)).where(Problem.kind == "problem")
    if difficulty:
        stmt = stmt.where(Problem.difficulty == difficulty)
    if chapter is not None:
        stmt = stmt.where(Problem.chapter_num == chapter)

    pool = list(db.scalars(stmt))
    if only_solved:
        pool = [p for p in pool if p.state and p.state.due]
    if not pool:
        raise HTTPException(404, "没有符合条件的题目")

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
    """拿这道题的面试官追问。首次调用时用 Claude 生成并缓存。"""
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
        # 没配 API key 或调用失败 —— 给一套通用追问兜底,功能不中断
        items = [
            llm.FollowUpItem(question="你的解法时间/空间复杂度是多少?能再优化吗?",
                             hint="先说清当前复杂度的来源,再讨论瓶颈在哪一步"),
            llm.FollowUpItem(question="有哪些边界情况?空输入、单元素、全部相同怎么处理?",
                             hint="当场举 2-3 个具体输入,说出各自的预期输出"),
            llm.FollowUpItem(question="如果输入规模变成 10 亿,你的方案还成立吗?",
                             hint="讨论内存约束、流式处理、分片或外部排序"),
        ]

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
    """把代码交给 Claude 审一遍,顺便让它猜你犯了哪些错误标签。"""
    code = (payload or {}).get("code", "")
    if not code.strip():
        raise HTTPException(400, "代码不能为空")
    if not llm.is_enabled():
        raise HTTPException(503, "未配置 ANTHROPIC_API_KEY,AI review 不可用")

    result = llm.review_code(problem.title, problem.number, problem.difficulty, code)
    if result is None:
        raise HTTPException(502, "调用 Claude 失败,请稍后再试")
    return CodeReviewOut(
        summary=result.summary,
        issues=result.issues,
        suggested_mistakes=result.suggested_mistakes,
    )
