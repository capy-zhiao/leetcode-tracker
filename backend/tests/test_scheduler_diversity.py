"""Interleaving in the daily review queue.

Pure-function tests use lightweight stand-ins for Problem, since pick_diverse only reads
chapter_num, number and patterns.
"""
from datetime import timedelta
from types import SimpleNamespace

from app.deps import today as study_today
from app.models import Problem, ReviewState
from app.scheduler import QueueItem, pick_diverse


def item(number, chapter, pattern, score):
    p = SimpleNamespace(number=number, chapter_num=chapter, patterns=[pattern])
    return QueueItem(problem=p, reason="due", priority_score=score)


def numbers(items):
    return [i.problem.number for i in items]


# The real queue from 2026-09-23: five graph problems outrank everything else.
GRAPH_HEAVY = [
    item(261, 11, "union-find",       11.9),
    item(200, 11, "grid-dfs",          8.9),
    item(417, 11, "grid-dfs",          8.9),
    item(130, 11, "grid-dfs",          8.9),
    item(207, 11, "topological-sort",  8.9),
    item(128, 1,  "hashmap",           6.9),
    item(424, 3,  "sliding-window",    6.7),
    item(853, 4,  "monotonic-stack",   6.6),
]


def test_one_chapter_cannot_take_every_slot():
    got = pick_diverse(GRAPH_HEAVY, cap=4, per_chapter=2, per_pattern=2)
    assert numbers(got) == [261, 200, 128, 424]


def test_pattern_limit_alone_does_not_stop_a_chapter_monopoly():
    """Why both limits exist: 207 is topological sort, so a pattern-only rule still
    fills all four slots with graph problems."""
    got = pick_diverse(GRAPH_HEAVY, cap=4, per_chapter=0, per_pattern=2)
    assert numbers(got) == [261, 200, 417, 207]
    assert all(i.problem.chapter_num == 11 for i in got)


def test_pattern_limit_applies_across_chapters():
    items = [
        item(27, 1, "two-pointers", 9.0),
        item(75, 1, "two-pointers", 8.0),     # chapter 1 now full
        item(125, 2, "two-pointers", 7.0),    # different chapter, same pattern -> skipped
        item(33, 5, "binary-search", 6.0),
    ]
    got = pick_diverse(items, cap=3, per_chapter=2, per_pattern=2)
    assert numbers(got) == [27, 75, 33]


def test_backfills_when_everything_due_is_one_chapter():
    """The limits change which problems you get, never how many."""
    only_graphs = GRAPH_HEAVY[:5]
    got = pick_diverse(only_graphs, cap=4, per_chapter=2, per_pattern=2)
    assert len(got) == 4
    assert numbers(got) == [261, 200, 417, 130]


def test_backfill_takes_the_highest_priority_skipped_items():
    items = [
        item(1, 11, "a", 10.0),
        item(2, 11, "b", 9.0),
        item(3, 11, "c", 8.0),     # skipped, higher priority
        item(4, 11, "d", 7.0),     # skipped, lower priority
    ]
    got = pick_diverse(items, cap=3, per_chapter=2, per_pattern=0)
    assert numbers(got) == [1, 2, 3]


def test_result_is_in_priority_order():
    got = pick_diverse(GRAPH_HEAVY, cap=4, per_chapter=1, per_pattern=0)
    scores = [i.priority_score for i in got]
    assert scores == sorted(scores, reverse=True)


def test_zero_disables_both_limits():
    got = pick_diverse(GRAPH_HEAVY, cap=4, per_chapter=0, per_pattern=0)
    assert numbers(got) == numbers(GRAPH_HEAVY[:4])


def test_fewer_items_than_the_cap():
    got = pick_diverse(GRAPH_HEAVY[:2], cap=4, per_chapter=1, per_pattern=1)
    assert numbers(got) == [261, 200]


def test_today_endpoint_interleaves_chapters(client, db_session):
    """End to end: three failing graph problems and one array problem, cap 3."""
    d = study_today()
    rows = [
        (261, 11, 3), (200, 11, 2), (417, 11, 2),   # graphs, many failures
        (128, 1, 1),                                # arrays, one failure
    ]
    for number, chapter, lapses in rows:
        p = Problem(number=number, title=f"P{number}", difficulty="Medium",
                    chapter_num=chapter, chapter=f"Ch{chapter}", url="", kind="problem")
        db_session.add(p)
        db_session.flush()
        db_session.add(ReviewState(problem_id=p.id, interval_days=1, reps=1,
                                   lapses=lapses, due=d - timedelta(days=1)))
    db_session.commit()

    q = client.get("/review/today", params={"review_cap": 3}).json()
    assert [i["problem"]["number"] for i in q["reviews"]] == [261, 200, 128]
    assert q["deferred"] == 1
