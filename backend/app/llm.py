"""Pluggable LLM layer: generates interview follow-up questions and reviews code.

Two providers are supported and selected with LLM_PROVIDER:

  anthropic — Claude. Uses native structured outputs (`messages.parse`), so the response
              is already a validated Pydantic object. Best quality follow-ups.
  deepseek  — DeepSeek via its OpenAI-compatible API. Roughly 30x cheaper; JSON mode plus
              manual Pydantic validation, since it has no strict-schema equivalent.

Design principle: **graceful degradation**. With LLM_PROVIDER=none (or a missing key) these
functions return empty results and the rest of the app keeps working — no hard dependency.
"""
from __future__ import annotations

import json
import logging
import re
from typing import TypeVar

from pydantic import BaseModel, Field, ValidationError

from .config import settings
from .constants import MISTAKE_TAGS

log = logging.getLogger(__name__)
T = TypeVar("T", bound=BaseModel)


# ---------------------------------------------------------------- schemas
class FollowUpItem(BaseModel):
    question: str = Field(description="A follow-up question an interviewer would ask, one sentence")
    hint: str = Field(description="Key points a good answer should cover, two or three sentences")


class FollowUpBundle(BaseModel):
    followups: list[FollowUpItem]


class CodeReview(BaseModel):
    summary: str = Field(description="One or two sentences: is it correct, what is the complexity")
    issues: list[str] = Field(description="Concrete problems, one sentence each; empty list if none")
    suggested_mistakes: list[str] = Field(
        description="IDs from the provided mistake-tag list that this code actually exhibits; empty if none"
    )


class ComplexityVerdict(BaseModel):
    actual_time: str = Field(description="Big-O time of THIS code as written, e.g. O(V + E)")
    actual_space: str = Field(description="Big-O auxiliary space of THIS code as written")
    time_correct: bool = Field(description="Does the candidate's stated time equal actual_time?")
    space_correct: bool = Field(description="Does the candidate's stated space equal actual_space?")
    optimal_time: str = Field(description="Best known time for this problem")
    optimal_space: str = Field(description="Space of that best-known solution")
    is_optimal: bool = Field(description="Is this code's time complexity optimal for the problem?")
    explanation: str = Field(
        description="Two or three sentences: define the variables, say where the dominant "
                    "cost comes from, and if the candidate was wrong, what they missed"
    )


def extract_json(raw: str) -> str:
    """Pull the JSON object out of a model reply.

    JSON mode is documented for DeepSeek, but not in combination with thinking mode, and
    third-party relays vary — so tolerate a markdown fence or a sentence around the object
    instead of failing the whole call over formatting.
    """
    text = raw.strip()
    fenced = re.search(r"```(?:json)?\s*(\{.*\})\s*```", text, re.DOTALL)
    if fenced:
        return fenced.group(1)
    start, end = text.find("{"), text.rfind("}")
    if start != -1 and end > start:
        return text[start:end + 1]
    return text


# ---------------------------------------------------------------- providers
class _Provider:
    """Common interface so the rest of the app never cares which vendor is behind it."""

    name = "none"

    def complete(self, prompt: str, schema: type[T]) -> T | None:  # pragma: no cover - interface
        raise NotImplementedError


class AnthropicProvider(_Provider):
    name = "anthropic"

    def __init__(self) -> None:
        import anthropic

        self._anthropic = anthropic
        self._client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

    def complete(self, prompt: str, schema: type[T]) -> T | None:
        a = self._anthropic
        try:
            res = self._client.messages.parse(
                model=settings.anthropic_model,
                max_tokens=4000,
                thinking={"type": "adaptive"},
                messages=[{"role": "user", "content": prompt}],
                output_format=schema,
            )
            return res.parsed_output
        except a.NotFoundError:
            log.warning("Anthropic: model not found or not accessible")
        except a.RateLimitError:
            log.warning("Anthropic: rate limited, try again later")
        except a.APIStatusError as e:
            log.warning("Anthropic: HTTP %s", e.status_code)
        except a.APIConnectionError:
            log.warning("Anthropic: could not reach the API")
        return None


class DeepSeekProvider(_Provider):
    """DeepSeek exposes an OpenAI-compatible endpoint, so we use the OpenAI SDK.

    It has JSON mode but no strict schema enforcement, so we embed the JSON schema in the
    prompt and validate the reply ourselves with Pydantic.
    """

    name = "deepseek"

    def __init__(self) -> None:
        import openai

        self._openai = openai
        self._client = openai.OpenAI(
            api_key=settings.deepseek_api_key,
            base_url=settings.deepseek_base_url,
            timeout=settings.llm_timeout_seconds,
        )

    @staticmethod
    def request_options() -> dict:
        """Thinking-mode parameters. They go in extra_body, which the SDK merges into the
        top level of the request JSON — reasoning_effort's values (low/high/max) are
        DeepSeek's own, so they are kept out of the SDK's typed arguments."""
        if settings.deepseek_thinking:
            return {
                "max_tokens": 16000,   # reasoning tokens count towards the limit
                "extra_body": {
                    "thinking": {"type": "enabled"},
                    "reasoning_effort": settings.deepseek_reasoning_effort,
                },
            }
        return {"max_tokens": 4000, "extra_body": {"thinking": {"type": "disabled"}}}

    def complete(self, prompt: str, schema: type[T]) -> T | None:
        o = self._openai
        shape = json.dumps(schema.model_json_schema(), ensure_ascii=False, indent=2)
        full = (
            f"{prompt}\n\n"
            f"Respond with a single JSON object matching this schema exactly. "
            f"Output JSON only, no markdown fences, no commentary.\n\n{shape}"
        )
        try:
            res = self._client.chat.completions.create(
                model=settings.deepseek_model,
                response_format={"type": "json_object"},
                messages=[{"role": "user", "content": full}],
                **self.request_options(),
            )
            raw = res.choices[0].message.content or ""
            u = getattr(res, "usage", None)
            if u is not None:
                details = getattr(u, "completion_tokens_details", None)
                log.info(
                    "DeepSeek usage: prompt=%s completion=%s (reasoning=%s)",
                    getattr(u, "prompt_tokens", "?"), getattr(u, "completion_tokens", "?"),
                    getattr(details, "reasoning_tokens", "?") if details else "?",
                )
        except o.NotFoundError:
            log.warning("DeepSeek: model not found — check DEEPSEEK_MODEL")
            return None
        except o.RateLimitError:
            log.warning("DeepSeek: rate limited, try again later")
            return None
        except o.APIStatusError as e:
            log.warning("DeepSeek: HTTP %s", e.status_code)
            return None
        except o.APIConnectionError:
            log.warning("DeepSeek: could not reach the API")
            return None

        try:
            return schema.model_validate_json(extract_json(raw))
        except ValidationError as e:
            log.warning("DeepSeek: reply did not match the schema (%s)", e.error_count())
            return None


_cached: _Provider | None = None


def get_provider() -> _Provider | None:
    """Build (and memoise) the configured provider, or None if AI features are off."""
    global _cached
    if _cached is not None:
        return _cached

    choice = settings.llm_provider.strip().lower()
    try:
        if choice == "anthropic" and settings.anthropic_api_key:
            _cached = AnthropicProvider()
        elif choice == "deepseek" and settings.deepseek_api_key:
            _cached = DeepSeekProvider()
        else:
            return None
    except ImportError as e:
        log.warning("LLM provider %r unavailable: %s", choice, e)
        return None
    return _cached


def is_enabled() -> bool:
    return get_provider() is not None


def provider_name() -> str:
    p = get_provider()
    return p.name if p else "none"


# ---------------------------------------------------------------- public API
def generate_followups(
    title: str, number: int, difficulty: str, chapter: str, n: int = 3
) -> list[FollowUpItem]:
    """Generate interviewer follow-ups for one problem. Results are cached in the DB,
    so each problem costs exactly one API call for its lifetime."""
    provider = get_provider()
    if provider is None:
        return []

    prompt = f"""You are a senior software engineer interviewing a new-grad candidate.

The candidate has just finished this problem:
  LeetCode {number}. {title} ({difficulty}, category: {chapter})

Give {n} follow-up questions you would ask after they finish coding. Requirements:
- Questions a real interviewer asks, not textbook recitation
- Cover different angles: complexity optimisation, edge cases and failure modes,
  changing requirements (huge input, streaming data, concurrency), trade-offs against
  alternative approaches
- Order them from easier to harder
- Pair each question with the key points a strong answer covers, so the candidate can
  self-assess afterwards"""

    result = provider.complete(prompt, FollowUpBundle)
    return result.followups if result else []


def review_code(
    title: str, number: int, difficulty: str, code: str, language: str = "Python"
) -> CodeReview | None:
    """Review a submitted solution and infer which mistake tags it exhibits,
    so the user does not have to tick them by hand."""
    provider = get_provider()
    if provider is None or not code.strip():
        return None

    tag_list = "\n".join(f"  - {t['id']}: {t['label']} — {t['hint']}" for t in MISTAKE_TAGS)
    prompt = f"""Review this LeetCode solution.

Problem: {number}. {title} ({difficulty})

```{language.lower()}
{code}
```

Please:
1. Give a one or two sentence verdict (is it correct, what is the complexity)
2. List concrete issues, one sentence each. If there genuinely are none, return an empty
   list — **do not invent problems to fill the quota**
3. From the mistake tags below, pick the ones this code **actually** exhibits
   (return ids only, empty list if none apply):

{tag_list}

Be direct — skip the pleasantries."""

    review = provider.complete(prompt, CodeReview)
    if review is None:
        return None

    valid = {t["id"] for t in MISTAKE_TAGS}
    review.suggested_mistakes = [m for m in review.suggested_mistakes if m in valid]
    return review


def analyze_complexity(
    title: str,
    number: int,
    code: str,
    stated_time: str,
    stated_space: str,
    reference: tuple[list[str], list[str]] | None = None,
) -> ComplexityVerdict | None:
    """Judge the candidate's stated complexity against the code they actually wrote.

    The lookup table in complexity.py compares against the textbook solution, so an honest
    O(n^2) analysis of a brute-force answer is marked wrong. This asks the model about the
    code itself, and separately whether it is optimal. The table's answer is passed along
    as a hint, not as the answer key.
    """
    provider = get_provider()
    if provider is None or not code.strip():
        return None

    ref = ""
    if reference:
        ref = (f"\nFor reference, the standard solution runs in {reference[0][0]} time and "
               f"{reference[1][0]} space. The candidate's code may use a different approach — "
               f"judge the code in front of you, not the standard solution.\n")

    prompt = f"""You are grading a new-grad candidate's complexity analysis in a coding interview.

Problem: LeetCode {number}. {title}

Their code:
```python
{code}
```

They stated: time {stated_time or "(blank)"}, space {stated_space or "(blank)"}.
{ref}
Rules:
- Analyse the code AS WRITTEN, including any inefficiency it has.
- Space means auxiliary space (recursion stack, hash maps, queues), excluding the returned
  output — but if the candidate's answer is only right when the output is counted, and
  that is a reasonable reading, accept it and say so.
- Accept equivalent notation: O(n) for O(V) when n is the node count, O(m*n) for O(n*m),
  a stated bound that differs only by a constant.
- Do not accept a looser or tighter bound: O(n) is wrong for O(n log n), and O(n^2) is
  wrong for O(n) unless the code really is quadratic.
- Name your variables in the explanation (n = ..., V = ..., E = ...)."""

    return provider.complete(prompt, ComplexityVerdict)
