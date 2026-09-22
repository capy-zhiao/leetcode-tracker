"""Claude API 集成:生成面试追问 + 给解法做 code review。

设计原则:**优雅降级**。没配 ANTHROPIC_API_KEY 时,这些功能返回空/None,
app 其余部分照常工作 —— 不会因为缺个 key 就起不来。

用的是结构化输出(client.messages.parse + Pydantic),所以拿到的直接是校验过的对象,
不用自己解析 JSON、不用担心模型多输出一段客套话。
"""
from __future__ import annotations

import logging

import anthropic
from pydantic import BaseModel, Field

from .config import settings
from .constants import MISTAKE_TAGS

log = logging.getLogger(__name__)

MODEL = "claude-opus-5"


# ---------- 结构化输出的 schema ----------
class FollowUpItem(BaseModel):
    question: str = Field(description="面试官会问的追问,一句话")
    hint: str = Field(description="回答要点提示,给自己复盘用,两三句")


class FollowUpBundle(BaseModel):
    followups: list[FollowUpItem]


class CodeReview(BaseModel):
    summary: str = Field(description="一两句总评")
    issues: list[str] = Field(description="具体问题,每条一句话;没问题就空列表")
    suggested_mistakes: list[str] = Field(
        description="从给定的错误标签 id 列表里挑出这份代码确实犯了的,没有就空列表"
    )


def _client() -> anthropic.Anthropic | None:
    if not settings.anthropic_api_key:
        return None
    return anthropic.Anthropic(api_key=settings.anthropic_api_key)


def _safe_parse(call, what: str):
    """统一的错误处理:按「具体 -> 泛化」的顺序接,任何失败都降级成 None。"""
    try:
        return call()
    except anthropic.NotFoundError:
        log.warning("%s 失败:模型不存在或无权访问", what)
    except anthropic.RateLimitError:
        log.warning("%s 失败:触发限流,稍后再试", what)
    except anthropic.APIStatusError as e:
        log.warning("%s 失败:HTTP %s", what, e.status_code)
    except anthropic.APIConnectionError:
        log.warning("%s 失败:连不上 API", what)
    return None


def generate_followups(
    title: str, number: int, difficulty: str, chapter: str, n: int = 3
) -> list[FollowUpItem]:
    """给一道题生成面试官追问。结果会被缓存进 DB,同一道题只生成一次。"""
    client = _client()
    if client is None:
        return []

    prompt = f"""你是一位资深的软件工程师面试官,正在面试一位准备北美 new grad 岗位的候选人。

候选人刚做完这道题:
  LeetCode {number}. {title}({difficulty},属于「{chapter}」)

请给出 {n} 个你会在候选人写完代码后追问的问题。要求:
- 真实面试里会问的那种,不是教科书式的复述题
- 覆盖不同角度:复杂度优化、边界与异常、需求变化(如数据量暴增/流式输入/并发)、其他解法的取舍
- 由浅入深排序
- 每个问题配一个「回答要点」,让候选人自己复盘时对照

用中文写问题和要点。"""

    result = _safe_parse(
        lambda: client.messages.parse(
            model=MODEL,
            max_tokens=4000,
            thinking={"type": "adaptive"},
            output_config={"effort": "medium"},
            messages=[{"role": "user", "content": prompt}],
            output_format=FollowUpBundle,
        ),
        f"生成 {number} 的 follow-up",
    )
    return result.parsed_output.followups if result else []


def review_code(
    title: str, number: int, difficulty: str, code: str, language: str = "Python"
) -> CodeReview | None:
    """给提交的代码做 review,并猜它犯了哪些「错误标签」—— 省得每次手动勾。"""
    client = _client()
    if client is None or not code.strip():
        return None

    tag_list = "\n".join(f"  - {t['id']}: {t['label']} —— {t['hint']}" for t in MISTAKE_TAGS)
    prompt = f"""审查这份 LeetCode 解法。

题目:{number}. {title}({difficulty})

```{language.lower()}
{code}
```

请:
1. 给一两句总评(是否正确、复杂度如何)
2. 列出具体问题,每条一句话。真没问题就返回空列表,**不要为了凑数编问题**
3. 从下面的错误标签里挑出这份代码**确实**犯了的(只返回 id,没有就空列表):

{tag_list}

用中文。评价要直接,不用客套。"""

    result = _safe_parse(
        lambda: client.messages.parse(
            model=MODEL,
            max_tokens=4000,
            thinking={"type": "adaptive"},
            messages=[{"role": "user", "content": prompt}],
            output_format=CodeReview,
        ),
        f"review {number} 的代码",
    )
    if not result:
        return None

    review = result.parsed_output
    # 防止模型返回不存在的标签 id
    valid = {t["id"] for t in MISTAKE_TAGS}
    review.suggested_mistakes = [m for m in review.suggested_mistakes if m in valid]
    return review


def is_enabled() -> bool:
    return bool(settings.anthropic_api_key)
