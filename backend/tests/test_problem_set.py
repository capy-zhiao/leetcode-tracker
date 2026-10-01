"""The problem set (NeetCode 150 + Top Interview 150) and how seed_db.py builds it."""
import os
import sqlite3
import subprocess
import sys
from pathlib import Path

from app.neetcode150 import NEETCODE_150
from app.top_interview_150 import (
    GROUP_CHAPTER, CHAPTER_OVERRIDES, PROBLEM_SET, TOP_150, TOP_150_POSITION, TOP_150_PROBLEMS,
)

BACKEND = Path(__file__).resolve().parents[1]


def test_top150_list_is_complete_and_ordered():
    assert len(TOP_150_PROBLEMS) == 150 == len(TOP_150)
    assert sorted(TOP_150_POSITION.values()) == list(range(150))


def test_every_top150_problem_has_a_chapter():
    for p in TOP_150_PROBLEMS:
        assert p["number"] in CHAPTER_OVERRIDES or p["group"] in GROUP_CHAPTER, p


def test_problem_set_is_the_union():
    assert PROBLEM_SET == NEETCODE_150 | TOP_150
    assert len(PROBLEM_SET) == 223


def run_seed(db: Path) -> str:
    env = {**os.environ, "DATABASE_URL": f"sqlite:///{db}", "LLM_PROVIDER": "none"}
    r = subprocess.run([sys.executable, "seed_db.py"], cwd=BACKEND, env=env,
                       capture_output=True, text=True, check=True)
    return r.stdout


def test_seed_builds_the_set_and_prunes_only_untouched_problems(tmp_path):
    db = tmp_path / "t.db"
    run_seed(db)
    con = sqlite3.connect(db)
    nums = {n for (n,) in con.execute("SELECT number FROM problems WHERE kind='problem'")}
    assert nums == PROBLEM_SET
    assert con.execute("SELECT COUNT(*) FROM problems WHERE kind='template'").fetchone()[0] == 15
    # flags and links for a Top-150-only problem
    top_only = con.execute(
        "SELECT in_neetcode150, in_top150, url FROM problems WHERE number=380").fetchone()
    assert top_only[:2] == (0, 1) and "leetcode.com/problems/insert-delete-getrandom-o1" in top_only[2]
    # in both lists -> LeetCode; NeetCode 150 only -> stays on neetcode.io
    url = dict(con.execute("SELECT number, url FROM problems WHERE number IN (1, 217)").fetchall())
    assert "leetcode.com/problems/two-sum/" in url[1]
    assert "neetcode.io" in url[217]
    links = con.execute("SELECT SUM(url LIKE '%leetcode.com%') FROM problems "
                        "WHERE kind='problem' AND in_top150").fetchone()[0]
    assert links == 150, "every Top 150 problem links to LeetCode"

    # Two problems outside the set: one practised, one never touched
    con.execute("INSERT INTO problems (number,title,difficulty,chapter_num,chapter,url,"
                "in_neetcode150,in_top150,kind,notes,code,patterns) VALUES "
                "(1406,'Stone Game III','Hard',13,'1-D DP','',0,0,'problem','','','[]'),"
                "(877,'Stone Game','Medium',14,'2-D DP','',0,0,'problem','','','[]')")
    pid = con.execute("SELECT id FROM problems WHERE number=1406").fetchone()[0]
    con.execute("INSERT INTO attempts (problem_id,created_at,grade,seconds,looked_at_solution,"
                "had_bugs,mistakes,code,note,mode,time_complexity,space_complexity) "
                "VALUES (?,'2026-09-01','good',60,0,0,'[]','','','practice','','')", (pid,))
    con.commit()

    out = run_seed(db)
    left = {n for (n,) in con.execute("SELECT number FROM problems WHERE kind='problem'")}
    assert 877 not in left, "untouched problem outside the set is removed"
    assert 1406 in left, "a problem with practice history is never deleted"
    assert "kept (has practice history): [1406]" in out
