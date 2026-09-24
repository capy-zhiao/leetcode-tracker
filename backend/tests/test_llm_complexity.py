"""AI complexity analysis: the DeepSeek request shape, reply parsing, and the endpoint.

No network: the provider's HTTP client and get_provider() are replaced with fakes.
"""
from types import SimpleNamespace

import pytest

from app import llm
from app.config import settings
from app.llm import ComplexityVerdict, DeepSeekProvider, extract_json


# ---------------------------------------------------------------- reply parsing

@pytest.mark.parametrize("raw", [
    '{"x": 1}',
    '```json\n{"x": 1}\n```',
    '```\n{"x": 1}\n```',
    'Sure, here it is: {"x": 1} — let me know.',
])
def test_extract_json_tolerates_fences_and_chatter(raw):
    assert extract_json(raw) == '{"x": 1}'


# ---------------------------------------------------------------- DeepSeek request

class FakeCompletions:
    def __init__(self, content):
        self.content, self.calls = content, []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        return SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content=self.content))],
            usage=SimpleNamespace(prompt_tokens=700, completion_tokens=1800,
                                  completion_tokens_details=SimpleNamespace(reasoning_tokens=1650)),
        )


def make_provider(monkeypatch, content):
    monkeypatch.setattr(settings, "deepseek_api_key", "test-key")
    provider = DeepSeekProvider()
    fake = FakeCompletions(content)
    provider._client = SimpleNamespace(chat=SimpleNamespace(completions=fake))
    return provider, fake


VERDICT_JSON = ('{"actual_time": "O(V + E)", "actual_space": "O(V)", "time_correct": false, '
                '"space_correct": true, "optimal_time": "O(V + E)", "optimal_space": "O(V)", '
                '"is_optimal": true, "explanation": "n = V."}')


def test_thinking_mode_is_requested(monkeypatch):
    monkeypatch.setattr(settings, "deepseek_thinking", True)
    monkeypatch.setattr(settings, "deepseek_reasoning_effort", "high")
    provider, fake = make_provider(monkeypatch, VERDICT_JSON)
    provider.complete("p", ComplexityVerdict)

    sent = fake.calls[0]
    assert sent["extra_body"]["thinking"] == {"type": "enabled"}
    assert sent["extra_body"]["reasoning_effort"] == "high"
    assert sent["max_tokens"] >= 16000, "reasoning tokens count towards max_tokens"


def test_thinking_can_be_switched_off(monkeypatch):
    monkeypatch.setattr(settings, "deepseek_thinking", False)
    provider, fake = make_provider(monkeypatch, VERDICT_JSON)
    provider.complete("p", ComplexityVerdict)
    assert fake.calls[0]["extra_body"] == {"thinking": {"type": "disabled"}}


def test_fenced_reply_still_parses(monkeypatch):
    provider, _ = make_provider(monkeypatch, f"```json\n{VERDICT_JSON}\n```")
    v = provider.complete("p", ComplexityVerdict)
    assert v is not None and v.actual_time == "O(V + E)"


def test_malformed_reply_returns_none(monkeypatch):
    provider, _ = make_provider(monkeypatch, "I think it's linear?")
    assert provider.complete("p", ComplexityVerdict) is None


# ---------------------------------------------------------------- endpoint

class StubProvider:
    name = "stub"

    def __init__(self, verdict):
        self.verdict, self.prompts = verdict, []

    def model_for(self, task="default"):
        return f"stub-{task}"

    def complete(self, prompt, schema, task="default"):
        self.tasks = getattr(self, "tasks", []) + [task]
        self.prompts.append(prompt)
        return self.verdict


def verdict(**over):
    base = dict(actual_time="O(m * n)", actual_space="O(m * n)", time_correct=True,
                space_correct=True, optimal_time="O(m * n)", optimal_space="O(m * n)",
                is_optimal=True, explanation="m, n = grid dimensions.")
    return ComplexityVerdict(**{**base, **over})


@pytest.fixture
def stub(monkeypatch):
    holder = {}

    def install(v):
        holder["p"] = StubProvider(v)
        monkeypatch.setattr(llm, "get_provider", lambda: holder["p"])
        return holder["p"]
    return install


def submit(client, number, code="def f(): pass", t="O(n)", s="O(n)"):
    r = client.post(f"/review/{number}/attempt", json={
        "grade": "good", "code": code, "time_complexity": t, "space_complexity": s})
    return r.json()["attempt"]["id"]


def test_ai_off_is_503(client, sample_problems):
    aid = submit(client, 200)
    assert client.post(f"/review/attempts/{aid}/complexity-ai").status_code == 503


def test_verdict_is_stored_and_decides_complexity_ok(client, sample_problems, stub):
    stub(verdict(time_correct=True, space_correct=False, actual_space="O(m * n)"))
    aid = submit(client, 200, t="O(m*n)", s="O(1)")

    body = client.post(f"/review/attempts/{aid}/complexity-ai").json()
    assert body["complexity_ai"]["actual_space"] == "O(m * n)"
    assert body["complexity_ok"] is False

    history = client.get("/review/200/attempts").json()
    assert history[0]["complexity_ai"]["time_correct"] is True


def test_ai_overrides_the_table_for_an_honest_brute_force(client, sample_problems, stub):
    """The point of the feature: O(n^2) is right for a quadratic solution even though the
    textbook answer is O(n) — the table marks it wrong, the AI marks it right."""
    stub(verdict(actual_time="O(n^2)", time_correct=True, is_optimal=False,
                 optimal_time="O(n)", actual_space="O(1)", space_correct=True))
    aid = submit(client, 1, t="O(n^2)", s="O(1)")        # Two Sum, nested loops
    assert client.get("/review/1/attempts").json()[0]["complexity_ok"] is False  # table

    body = client.post(f"/review/attempts/{aid}/complexity-ai").json()
    assert body["complexity_ok"] is True
    assert body["complexity_ai"]["is_optimal"] is False

    stats = client.get("/stats/complexity").json()
    assert stats["graded"] == 1 and stats["both_correct"] == 1


def test_prompt_carries_the_code_the_answer_and_the_reference(client, sample_problems, stub):
    p = stub(verdict())
    aid = submit(client, 200, code="def numIslands(grid): ...", t="O(m*n)", s="O(m*n)")
    client.post(f"/review/attempts/{aid}/complexity-ai")
    prompt = p.prompts[0]
    assert "def numIslands(grid)" in prompt
    assert "time O(m*n), space O(m*n)" in prompt
    assert "standard solution runs in O(m * n)" in prompt


def test_attempt_without_code_is_400(client, sample_problems, stub):
    stub(verdict())
    aid = submit(client, 200, code="   ")
    assert client.post(f"/review/attempts/{aid}/complexity-ai").status_code == 400


def test_unknown_attempt_is_404(client, stub):
    stub(verdict())
    assert client.post("/review/attempts/99999/complexity-ai").status_code == 404


def test_failed_ai_call_is_502_and_changes_nothing(client, sample_problems, stub):
    stub(None)
    aid = submit(client, 200, t="O(m*n)", s="O(m*n)")
    assert client.post(f"/review/attempts/{aid}/complexity-ai").status_code == 502
    a = client.get("/review/200/attempts").json()[0]
    assert a["complexity_ai"] is None and a["complexity_ok"] is True


# ---------------------------------------------------------------- relay quirks

from app.llm import AnswerGrade, FollowUpBundle, describe_fields, json_candidates, parse_reply

ECHOED = '''{"properties": {"score": {"type": "integer"}}, "required": ["score"], "type": "object"}
```json
{"score": 3, "feedback": "Good.", "missing": [], "model_answer": "Keep two {rolling} values."}
```'''


def test_reply_that_echoes_the_schema_first_still_parses():
    """Seen on a relay: the schema is repeated verbatim, then the real answer is fenced."""
    g = parse_reply(ECHOED, AnswerGrade)
    assert g is not None and g.score == 3


def test_braces_inside_strings_do_not_split_objects():
    raw = '{"score": 2, "feedback": "use {x}", "missing": ["a } b"], "model_answer": "m"}'
    assert json_candidates(raw) == [raw]
    assert parse_reply(raw, AnswerGrade).missing == ["a } b"]


def test_no_valid_object_returns_none():
    assert parse_reply('{"nope": 1} and {"also": 2}', AnswerGrade) is None


def test_field_list_is_sent_instead_of_raw_schema():
    listing = describe_fields(AnswerGrade)
    assert '"score" (integer (1..4))' in listing
    assert '"missing" (array of string)' in listing
    assert '"properties"' not in listing


def test_nested_item_fields_are_described(monkeypatch):
    provider, fake = make_provider(monkeypatch, '{"followups": []}')
    provider.complete("P", FollowUpBundle)
    content = fake.calls[0]["messages"][0]["content"]
    assert 'Each element of "followups"' in content and '"hint" (string)' in content



# ---------------------------------------------------------------- per-task models

def test_complexity_can_run_on_a_cheaper_model(monkeypatch):
    monkeypatch.setattr(settings, "deepseek_model", "deepseek-v4-pro")
    monkeypatch.setattr(settings, "deepseek_complexity_model", "deepseek-v4-flash")
    provider, fake = make_provider(monkeypatch, VERDICT_JSON)
    provider.complete("p", ComplexityVerdict, task="complexity")
    provider.complete("p", ComplexityVerdict, task="interview")
    assert [c["model"] for c in fake.calls] == ["deepseek-v4-flash", "deepseek-v4-pro"]


def test_empty_override_falls_back_to_the_default_model(monkeypatch):
    monkeypatch.setattr(settings, "deepseek_model", "deepseek-v4-pro")
    monkeypatch.setattr(settings, "deepseek_complexity_model", "")
    provider, _ = make_provider(monkeypatch, VERDICT_JSON)
    assert provider.model_for("complexity") == "deepseek-v4-pro"


def test_stored_verdict_records_the_model_that_judged_it(client, sample_problems, stub):
    p = stub(verdict())
    aid = submit(client, 200, t="O(m*n)", s="O(m*n)")
    body = client.post(f"/review/attempts/{aid}/complexity-ai").json()
    assert body["complexity_ai"]["model"] == "stub-complexity"
    assert p.tasks == ["complexity"]
