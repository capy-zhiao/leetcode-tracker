"""数据库表结构(SQLAlchemy 2.0 风格)。

三张核心表:
  Problem     — 250 道题的静态信息
  ReviewState — 每道题的 SRS 状态(1:1),srs.SrsState 的持久化版本
  Attempt     — 每次做题的记录(1:N),统计和 diff 都靠它
"""
from __future__ import annotations

from datetime import date, datetime, timezone

from sqlalchemy import JSON, Boolean, Date, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base
from .srs import DEFAULT_EASE, SrsState


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Problem(Base):
    __tablename__ = "problems"

    id: Mapped[int] = mapped_column(primary_key=True)
    number: Mapped[int] = mapped_column(Integer, unique=True, index=True)  # LeetCode 题号
    title: Mapped[str] = mapped_column(String(200))
    difficulty: Mapped[str] = mapped_column(String(10))          # Easy / Medium / Hard
    chapter_num: Mapped[int] = mapped_column(Integer, index=True)
    chapter: Mapped[str] = mapped_column(String(60))
    url: Mapped[str] = mapped_column(String(300), default="")
    in_neetcode150: Mapped[bool] = mapped_column(Boolean, default=True)
    kind: Mapped[str] = mapped_column(String(20), default="problem")  # problem | template
    notes: Mapped[str] = mapped_column(Text, default="")         # 从 markdown 迁移过来的思路
    code: Mapped[str] = mapped_column(Text, default="")          # 最近一次 AC 的代码

    state: Mapped["ReviewState"] = relationship(
        back_populates="problem", uselist=False, cascade="all, delete-orphan"
    )
    attempts: Mapped[list["Attempt"]] = relationship(
        back_populates="problem", cascade="all, delete-orphan",
        order_by="Attempt.created_at.desc()",
    )
    followups: Mapped[list["FollowUp"]] = relationship(
        back_populates="problem", cascade="all, delete-orphan"
    )


class ReviewState(Base):
    """SRS 状态。字段和 srs.SrsState 一一对应。"""
    __tablename__ = "review_states"

    problem_id: Mapped[int] = mapped_column(ForeignKey("problems.id"), primary_key=True)
    interval_days: Mapped[int] = mapped_column(Integer, default=0)
    ease: Mapped[float] = mapped_column(Float, default=DEFAULT_EASE)
    reps: Mapped[int] = mapped_column(Integer, default=0)
    lapses: Mapped[int] = mapped_column(Integer, default=0)
    due: Mapped[date | None] = mapped_column(Date, nullable=True, index=True)
    last_attempt_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    total_attempts: Mapped[int] = mapped_column(Integer, default=0)
    best_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)

    problem: Mapped[Problem] = relationship(back_populates="state")

    def to_srs(self) -> SrsState:
        """转成纯函数用的不可变对象 —— DB 和算法之间的桥。"""
        return SrsState(
            interval_days=self.interval_days, ease=self.ease,
            reps=self.reps, lapses=self.lapses, due=self.due,
        )

    def apply(self, s: SrsState) -> None:
        self.interval_days, self.ease = s.interval_days, s.ease
        self.reps, self.lapses, self.due = s.reps, s.lapses, s.due


class Attempt(Base):
    __tablename__ = "attempts"

    id: Mapped[int] = mapped_column(primary_key=True)
    problem_id: Mapped[int] = mapped_column(ForeignKey("problems.id"), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, index=True)
    grade: Mapped[str] = mapped_column(String(10))               # again/hard/good/easy
    seconds: Mapped[int] = mapped_column(Integer, default=0)
    looked_at_solution: Mapped[bool] = mapped_column(Boolean, default=False)
    had_bugs: Mapped[bool] = mapped_column(Boolean, default=False)
    mistakes: Mapped[list] = mapped_column(JSON, default=list)   # constants.MISTAKE_TAGS 的 id
    code: Mapped[str] = mapped_column(Text, default="")
    note: Mapped[str] = mapped_column(Text, default="")          # 「为什么卡住」一句话
    mode: Mapped[str] = mapped_column(String(10), default="practice")  # practice | mock

    problem: Mapped[Problem] = relationship(back_populates="attempts")


class FollowUp(Base):
    """面试官追问。由 Claude 预生成并缓存,mock 模式用。"""
    __tablename__ = "followups"

    id: Mapped[int] = mapped_column(primary_key=True)
    problem_id: Mapped[int] = mapped_column(ForeignKey("problems.id"), index=True)
    question: Mapped[str] = mapped_column(Text)
    hint: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)

    problem: Mapped[Problem] = relationship(back_populates="followups")
