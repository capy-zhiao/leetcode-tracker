"""
SRS(Spaced Repetition Scheduling)—— 刷题版记忆曲线。

为什么不直接用 Anki 的 SM-2:
  - Anki 一张卡 5 秒,一天能过 200 张;刷题一道 20-45 分钟,一天顶多 6-8 道
    => 必须有每日上限 + 优先级排序(见 priority())
  - Anki 靠自评「记得多牢」;刷题有更硬的信号:**用时** 和 **是否看了答案**
    => suggest_grade() 直接从计时器数据推荐评分

本模块是**纯函数**:不碰数据库、不读时钟(today 作参数传入)。
好处是能完整单元测试,见 tests/test_srs.py。
"""
from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import date, timedelta
from typing import Literal

Grade = Literal["again", "hard", "good", "easy"]
Difficulty = Literal["Easy", "Medium", "Hard"]

MIN_EASE, MAX_EASE, DEFAULT_EASE = 1.3, 3.0, 2.3
MAX_INTERVAL_DAYS = 365

# 首次复习的间隔(天)。之后按 ease 倍增。
FIRST_INTERVAL: dict[str, int] = {"again": 1, "hard": 2, "good": 4, "easy": 7}

# 每次评分对「容易度」的调整
EASE_DELTA: dict[str, float] = {"again": -0.20, "hard": -0.10, "good": 0.0, "easy": +0.10}

# 题目本身的难度会影响遗忘速度:Hard 题忘得快,间隔打折
DIFFICULTY_FACTOR: dict[str, float] = {"Easy": 1.15, "Medium": 1.0, "Hard": 0.80}

# 优先级权重(见 priority())
W_OVERDUE, W_LAPSE, W_CHAPTER = 1.0, 3.0, 0.1
DIFFICULTY_PRIORITY = {"Easy": 0.0, "Medium": 1.0, "Hard": 2.0}


@dataclass(frozen=True)
class SrsState:
    """一道题的复习状态。frozen=True:每次复习返回新对象,不原地改,方便测试和回溯。"""
    interval_days: int = 0          # 当前间隔
    ease: float = DEFAULT_EASE      # 容易度系数,越高间隔涨得越快
    reps: int = 0                   # 连续答对次数(答错归零)
    lapses: int = 0                 # 历史翻车总次数(永不归零,用于优先级)
    due: date | None = None         # 下次到期日;None = 还没排进复习


def _clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


def review(
    state: SrsState,
    grade: Grade,
    difficulty: Difficulty = "Medium",
    today: date | None = None,
) -> SrsState:
    """做完一道题,算出新的复习状态。

    grade 含义:
      again — 不会 / 看了答案      -> 明天再来,ease 降
      hard  — 卡壳 >15min 或有 bug -> 间隔只涨一点点
      good  — 顺利(5-15min)       -> 间隔 × ease
      easy  — 秒杀(<5min 一遍过)  -> 间隔 × ease × 1.3,ease 升
    """
    if grade not in FIRST_INTERVAL:
        raise ValueError(f"未知的 grade: {grade!r}")
    today = today or date.today()

    ease = _clamp(state.ease + EASE_DELTA[grade], MIN_EASE, MAX_EASE)

    if grade == "again":
        # 翻车:间隔重置为 1 天,reps 归零,lapses 累加
        interval = 1
        reps = 0
        lapses = state.lapses + 1
    else:
        reps = state.reps + 1
        lapses = state.lapses
        if state.reps == 0 or state.interval_days == 0:
            interval = FIRST_INTERVAL[grade]        # 第一次(或刚翻过车)
        elif grade == "hard":
            interval = max(1, round(state.interval_days * 1.2))
        elif grade == "good":
            interval = round(state.interval_days * ease)
        else:  # easy
            interval = round(state.interval_days * ease * 1.3)
        # 题目难度加权:Hard 题间隔打八折
        interval = max(1, round(interval * DIFFICULTY_FACTOR.get(difficulty, 1.0)))

    interval = min(interval, MAX_INTERVAL_DAYS)
    return replace(
        state,
        interval_days=interval,
        ease=round(ease, 3),
        reps=reps,
        lapses=lapses,
        due=today + timedelta(days=interval),
    )


def suggest_grade(
    seconds: int,
    looked_at_solution: bool,
    had_bugs: bool = False,
    difficulty: Difficulty = "Medium",
) -> Grade:
    """根据计时器和实际表现推荐一个 grade,前端拿它当默认选中项。

    时间阈值按题目难度缩放 —— Hard 题 20 分钟做出来算快,Easy 题 20 分钟就是卡了。
    """
    if looked_at_solution:
        return "again"
    scale = {"Easy": 0.6, "Medium": 1.0, "Hard": 1.6}.get(difficulty, 1.0)
    minutes = seconds / 60
    if had_bugs or minutes > 15 * scale:
        return "hard"
    if minutes <= 5 * scale:
        return "easy"
    return "good"


def priority(
    state: SrsState,
    today: date,
    difficulty: Difficulty = "Medium",
    chapter_num: int = 1,
) -> float:
    """到期题目的排队优先级(越大越先做)。

    某天可能有 20 道同时到期但你只做得完 4 道,所以要排序:
      逾期越久 + 历史翻车越多 + 越难 + 章节越靠前(先补地基) => 越优先
    """
    if state.due is None:
        return 0.0
    overdue_days = (today - state.due).days
    return (
        overdue_days * W_OVERDUE
        + state.lapses * W_LAPSE
        + DIFFICULTY_PRIORITY.get(difficulty, 1.0)
        + (20 - chapter_num) * W_CHAPTER
    )


def is_due(state: SrsState, today: date) -> bool:
    return state.due is not None and state.due <= today
