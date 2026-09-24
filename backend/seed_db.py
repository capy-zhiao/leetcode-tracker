"""Import data/seed.json into the database and register the 15 algorithm templates.

Usage:  python seed_db.py           incremental: add new problems, keep attempt history
        python seed_db.py --reset   wipe and start over

Problems already solved in the markdown notes start out "due today", so the very first
daily queue picks up where the manual study plan left off.
"""
from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path

from sqlalchemy import select

from app.database import Base, SessionLocal, engine
from app.models import Problem, ReviewState
from app.neetcode150 import NEETCODE_150
from app.patterns import patterns_for
from app.srs import DEFAULT_EASE

SEED = Path(__file__).resolve().parent.parent / "data" / "seed.json"

# Historic failure counts, migrated from the manual review plan. Without these every solved
# problem would share the same priority; with them the first queue surfaces the problems
# that were actually difficult.
KNOWN_LAPSES = {
    994: 3,   # Rotting Oranges: wrong counter, flag hack, -1 condition — three rewrites
    695: 3,   # Max Area of Island: type, pass-by-value, visited lookup, missing return
    261: 3,   # Graph Valid Tree: template copied wrong, flag overwrite, missing edge check
    130: 2,   # Surrounded Regions: digit zero vs letter O, missing guard on 'T'
    200: 2,   # Number of Islands: counter inside dfs, missing guard
    417: 2,   # Pacific Atlantic: both oceans shared one visited set
    207: 2,   # Course Schedule: adjacency direction reversed
    33:  1,   # Search in Rotated Sorted Array: only worked after heavy print debugging
    153: 1,
    424: 1,
    743: 1,   # Dijkstra: forgot to accumulate t1+t2, effectively wrote Prim
    853: 1,   # Car Fleet: "else if" instead of elif, missing return
    128: 1,   # Longest Consecutive Sequence: returned length instead of the max
}

# The 15 templates from the notes. They ride the same SRS machinery.
TEMPLATES = [
    (9001, "Union-Find", 11, "Graphs", "Hard"),
    (9002, "Grid DFS (three guards)", 11, "Graphs", "Medium"),
    (9003, "Multi-source BFS (level loop)", 11, "Graphs", "Medium"),
    (9004, "Topological sort (Kahn)", 11, "Graphs", "Medium"),
    (9005, "Backtracking skeleton", 10, "Backtracking", "Medium"),
    (9006, "Binary search (closed interval)", 5, "Binary Search", "Medium"),
    (9007, "Sliding window", 3, "Sliding Window", "Medium"),
    (9008, "Monotonic stack", 4, "Stack", "Medium"),
    (9009, "Linked list trio", 6, "Linked List", "Medium"),
    (9010, "Tree DFS and BFS", 7, "Trees", "Easy"),
    (9011, "Trie", 8, "Tries", "Medium"),
    (9012, "Heap (heapq)", 9, "Heap / Priority Queue", "Easy"),
    (9013, "Dijkstra / Prim / Bellman-Ford", 12, "Advanced Graphs", "Hard"),
    (9014, "DP three questions + memoization", 13, "1-D DP", "Medium"),
    (9015, "Interval merge + sweep line", 16, "Intervals", "Medium"),
]


def main() -> None:
    reset = "--reset" in sys.argv
    if reset:
        Base.metadata.drop_all(bind=engine)
        print("Dropped existing tables")
    Base.metadata.create_all(bind=engine)

    data = json.loads(SEED.read_text(encoding="utf-8"))
    today = date.today()
    db = SessionLocal()
    added = updated = with_state = 0

    try:
        existing = {p.number: p for p in db.scalars(select(Problem))}

        for item in data["problems"]:
            p = existing.get(item["number"])
            if p is None:
                p = Problem(
                    number=item["number"], title=item["title"],
                    difficulty=item["difficulty"], chapter_num=item["chapter_num"],
                    chapter=item["chapter"], url=item["url"],
                    in_neetcode150=item["number"] in NEETCODE_150, kind="problem",
                    notes=item["notes"], code=item["code"],
                    patterns=patterns_for(item["number"], item["chapter_num"]),
                )
                db.add(p)
                db.flush()
                added += 1
            else:
                # Refresh static fields without touching attempt history
                p.title, p.difficulty = item["title"], item["difficulty"]
                p.url = item["url"] or p.url
                # Pattern tags are derived data — always refresh them so retagging a
                # problem in patterns.py takes effect on the next run.
                p.patterns = patterns_for(item["number"], item["chapter_num"])
                # Same for the 150 flag: the official list wins over whatever the
                # markdown notes implied when the row was first created.
                p.in_neetcode150 = item["number"] in NEETCODE_150
                if item["notes"] and not p.notes:
                    p.notes = item["notes"]
                if item["code"] and not p.code:
                    p.code = item["code"]
                updated += 1

            # Already solved -> due today, so it enters the review queue immediately
            if item["solved"] and p.state is None:
                lapses = KNOWN_LAPSES.get(item["number"], 0)
                db.add(ReviewState(
                    problem_id=p.id, interval_days=1,
                    # Problems that caused trouble get a lower ease, so gaps grow slower
                    ease=max(1.3, DEFAULT_EASE - 0.2 * lapses),
                    reps=1, lapses=lapses, due=today, total_attempts=0,
                ))
                with_state += 1

        t_added = 0
        for num, name, ch_num, ch, diff in TEMPLATES:
            if num in existing:
                continue
            t = Problem(
                number=num, title=name, difficulty=diff, chapter_num=ch_num,
                chapter=ch, url="", in_neetcode150=False, kind="template",
                notes="Blind-write practice", code="", patterns=[],
            )
            db.add(t)
            db.flush()
            db.add(ReviewState(problem_id=t.id, interval_days=0, due=today))
            t_added += 1

        db.commit()
    finally:
        db.close()

    print("\nImport complete")
    print(f"  problems added: {added}   updated: {updated}")
    print(f"  solved -> due today: {with_state}")
    print(f"  templates: {t_added}")
    print(f"  pattern tags refreshed on {added + updated} problems")


if __name__ == "__main__":
    main()
