"""Code-aware mock interview: questions about the submitted code, graded written answers.
No network — get_provider() is replaced with a stub that answers per schema."""
import pytest

from app import llm
from app.llm import AnswerGrade, FollowUpBundle, FollowUpItem

CODE = "def minCostClimbingStairs(cost):\n    dp = [0] * (len(cost) + 1)\n    ..."


class StubProvider:
    name = "stub"

    def __init__(self, replies):
        self.replies, self.prompts = replies, []

    def model_for(self, task="default"):
        return f"stub-{task}"

    def complete(self, prompt, schema, task="default"):
        self.tasks = getattr(self, "tasks", []) + [task]
        self.prompts.append((schema, prompt))
        return self.replies.get(schema)


@pytest.fixture
def stub(monkeypatch):
    def install(replies):
        p = StubProvider(replies)
        monkeypatch.setattr(llm, "get_provider", lambda: p)
        return p
    return install


QUESTIONS = FollowUpBundle(followups=[
    FollowUpItem(question="Your dp array has n+1 slots. Can you do better on space?",
                 hint="dp[i] reads only dp[i-1] and dp[i-2]; keep two variables: O(1)."),
    FollowUpItem(question="What does this return for a two-element cost array?",
                 hint="min of the two, since you may start at either step."),
    FollowUpItem(question="What if you could climb 1, 2 or 3 steps?",
                 hint="Three terms in the recurrence, three rolling variables."),
])
STRONG = AnswerGrade(score=4, feedback="Exactly right.", missing=[],
                     model_answer="Each state only needs the previous two, so two variables do.")


def start(client, code=CODE):
    return client.post("/mock/746/interview", json={
        "code": code, "time_complexity": "O(n)", "space_complexity": "O(n)"})


@pytest.fixture
def problem_746(db_session):
    from app.models import Problem
    p = Problem(number=746, title="Min Cost Climbing Stairs", difficulty="Easy",
                chapter_num=13, chapter="1-D DP", url="", kind="problem")
    db_session.add(p)
    db_session.commit()
    return p


def test_ai_off_is_503(client, problem_746):
    assert start(client).status_code == 503


def test_questions_are_about_the_submitted_code(client, problem_746, stub):
    s = stub({FollowUpBundle: QUESTIONS})
    r = start(client)
    assert r.status_code == 200
    body = r.json()
    assert [q["question"] for q in body][0].startswith("Your dp array")
    assert all(set(q) == {"id", "question"} for q in body), "key points must stay hidden"

    schema, prompt = s.prompts[0]
    assert "dp = [0] * (len(cost) + 1)" in prompt
    assert "time O(n), space O(n)" in prompt


def test_empty_code_is_400(client, problem_746, stub):
    stub({FollowUpBundle: QUESTIONS})
    assert start(client, code="  ").status_code == 400


def test_generation_failure_is_502(client, problem_746, stub):
    stub({})
    assert start(client).status_code == 502


def test_answer_is_graded_and_key_points_revealed(client, problem_746, stub, db_session):
    s = stub({FollowUpBundle: QUESTIONS, AnswerGrade: STRONG})
    qid = start(client).json()[0]["id"]

    r = client.post(f"/mock/qa/{qid}/answer", json={"answer": "Two rolling variables, O(1)."})
    assert r.status_code == 200
    g = r.json()
    assert g["score"] == 4 and g["missing"] == []
    assert "two variables" in g["key_points"]

    schema, prompt = s.prompts[-1]
    assert schema is AnswerGrade
    assert "Two rolling variables, O(1)." in prompt
    assert "dp[i] reads only dp[i-1]" in prompt, "the grader must see the key points"

    from app.models import InterviewQA
    row = db_session.get(InterviewQA, qid)
    assert row.answer.startswith("Two rolling") and row.grade["score"] == 4
    assert row.answered_at is not None


def test_answering_again_replaces_the_grade(client, problem_746, stub, db_session):
    s = stub({FollowUpBundle: QUESTIONS, AnswerGrade: STRONG})
    qid = start(client).json()[0]["id"]
    client.post(f"/mock/qa/{qid}/answer", json={"answer": "no idea"})
    s.replies[AnswerGrade] = AnswerGrade(score=1, feedback="Off track.", missing=["x"],
                                         model_answer="y")
    assert client.post(f"/mock/qa/{qid}/answer", json={"answer": "still no idea"}).json()["score"] == 1


def test_empty_answer_is_400(client, problem_746, stub):
    stub({FollowUpBundle: QUESTIONS, AnswerGrade: STRONG})
    qid = start(client).json()[0]["id"]
    assert client.post(f"/mock/qa/{qid}/answer", json={"answer": " "}).status_code == 400


def test_unknown_question_is_404(client, stub):
    stub({AnswerGrade: STRONG})
    assert client.post("/mock/qa/9999/answer", json={"answer": "x"}).status_code == 404


def test_failed_grading_is_502_and_saves_nothing(client, problem_746, stub, db_session):
    s = stub({FollowUpBundle: QUESTIONS})
    qid = start(client).json()[0]["id"]
    assert client.post(f"/mock/qa/{qid}/answer", json={"answer": "x"}).status_code == 502
    from app.models import InterviewQA
    row = db_session.get(InterviewQA, qid)
    assert row.answer == "" and row.grade is None


def test_score_is_bounded():
    with pytest.raises(Exception):
        AnswerGrade(score=5, feedback="", missing=[], model_answer="")



def test_interview_questions_and_grading_use_the_interview_task(client, problem_746, stub):
    s = stub({FollowUpBundle: QUESTIONS, AnswerGrade: STRONG})
    qid = start(client).json()[0]["id"]
    client.post(f"/mock/qa/{qid}/answer", json={"answer": "two variables"})
    assert s.tasks == ["interview", "interview"]
