"""API 端到端测试。"""
from datetime import date, timedelta


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_today_queue_orders_by_priority(client, sample_problems):
    """逾期久 + 翻车多的题要排在最前面 —— 994 应该压过 200。"""
    r = client.get("/review/today")
    assert r.status_code == 200
    q = r.json()

    numbers = [i["problem"]["number"] for i in q["reviews"]]
    assert numbers[0] == 994, f"994 该排第一,实际顺序 {numbers}"
    assert q["total_due"] == 2
    assert q["reviews"][0]["overdue_days"] == 5

    # 没做过的题进「新题」组
    assert [i["problem"]["number"] for i in q["new_problems"]] == [1]


def test_daily_cap_defers_overflow(client, sample_problems):
    r = client.get("/review/today", params={"review_cap": 1})
    q = r.json()
    assert len(q["reviews"]) == 1
    assert q["total_due"] == 2
    assert q["deferred"] == 1, "超出上限的要顺延,不是丢掉"


def test_submit_attempt_updates_srs(client, sample_problems):
    r = client.post("/review/1/attempt", json={
        "grade": "good", "seconds": 600, "mistakes": ["forgot_return"],
        "code": "class Solution: pass", "note": "字典存补数",
    })
    assert r.status_code == 200, r.text
    body = r.json()

    # 首次 good = 4 天,Two Sum 是 Easy -> ×1.15 -> 5 天(Easy 题忘得慢,间隔更长)
    assert body["next_due_in_days"] == 5
    assert body["state"]["reps"] == 1
    assert body["state"]["total_attempts"] == 1
    assert body["state"]["best_seconds"] == 600
    assert body["state"]["due"] == (date.today() + timedelta(days=5)).isoformat()

    # 做完后不该再出现在今天的复习队列里
    nums = [i["problem"]["number"] for i in client.get("/review/today").json()["reviews"]]
    assert 1 not in nums


def test_again_grade_resets_and_counts_lapse(client, sample_problems):
    r = client.post("/review/200/attempt", json={
        "grade": "again", "seconds": 1800, "looked_at_solution": True,
        "mistakes": ["missing_visited_brake", "type_confusion"],
    })
    body = r.json()
    assert body["next_due_in_days"] == 1
    assert body["state"]["lapses"] == 1
    assert body["state"]["reps"] == 0


def test_grade_suggestion_from_timer(client):
    r = client.get("/review/suggest-grade",
                   params={"seconds": 200, "difficulty": "Medium"})
    assert r.json()["grade"] == "easy"

    r = client.get("/review/suggest-grade",
                   params={"seconds": 1500, "difficulty": "Medium"})
    assert r.json()["grade"] == "hard"


def test_mistake_stats_aggregate(client, sample_problems):
    client.post("/review/1/attempt", json={"grade": "good", "mistakes": ["forgot_return"]})
    client.post("/review/200/attempt", json={"grade": "hard",
                                             "mistakes": ["forgot_return", "type_confusion"]})
    stats = client.get("/stats/mistakes").json()
    assert stats[0]["id"] == "forgot_return"
    assert stats[0]["count"] == 2
    assert stats[0]["pct"] > 60
    assert stats[0]["label"]                     # 带上人话标签和提示
    assert stats[0]["hint"]


def test_overview_stats(client, sample_problems):
    client.post("/review/1/attempt", json={"grade": "good", "seconds": 300})
    s = client.get("/stats").json()
    assert s["total_problems"] == 3
    assert s["attempts_total"] == 1
    assert s["streak_days"] == 1
    assert s["avg_seconds"] == 300
    assert any(c["chapter_num"] == 11 for c in s["by_chapter"])


def test_attempt_history_for_diff(client, sample_problems):
    client.post("/review/1/attempt", json={"grade": "again", "code": "v1"})
    client.post("/review/1/attempt", json={"grade": "good", "code": "v2"})
    hist = client.get("/review/1/attempts").json()
    assert len(hist) == 2
    assert hist[0]["code"] == "v2"               # 最新的在前,方便 diff


def test_problem_filters(client, sample_problems):
    assert len(client.get("/problems", params={"chapter": 11}).json()) == 2
    assert len(client.get("/problems", params={"difficulty": "Easy"}).json()) == 1
    assert len(client.get("/problems", params={"status": "new"}).json()) == 1
    assert client.get("/problems", params={"q": "island"}).json()[0]["number"] == 200


def test_followups_fallback_without_api_key(client, sample_problems):
    """没配 ANTHROPIC_API_KEY 时要降级成通用追问,不能报错。"""
    r = client.get("/mock/1/followups")
    assert r.status_code == 200
    items = r.json()
    assert len(items) >= 3
    assert all(i["question"] for i in items)


def test_mock_start(client, sample_problems):
    r = client.post("/mock/start", params={"difficulty": "Medium"})
    assert r.status_code == 200
    body = r.json()
    assert body["problem"]["difficulty"] == "Medium"
    assert body["minutes"] == 35
