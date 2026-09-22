"""把 data/seed.json 导入数据库,并把 15 个算法模板也建进去。

用法:  python seed_db.py           # 增量:只补新题,保留做题记录
       python seed_db.py --reset   # 清库重来

已解的题(markdown 里写过代码的)初始状态设为「今天到期」——
这样 app 第一天就会按优先级给你排复习队列,直接接管手工的二刷计划。
"""
from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path

from sqlalchemy import select

from app.database import Base, SessionLocal, engine
from app.models import Problem, ReviewState
from app.srs import DEFAULT_EASE

SEED = Path(__file__).resolve().parent.parent / "data" / "seed.json"

# 历史翻车次数 —— 从 REVIEW.md 的「错题盲写队列」迁移过来。
# 有了它,第一天的复习队列就会自动把你返工过的题顶到最前面,
# 而不是所有已解题挤在同一个优先级上。
KNOWN_LAPSES = {
    994: 3,   # 烂橘子:count 数错对象 -> flag 歪招 -> -1 判断,返工 3 版
    695: 3,   # 最大岛屿面积:类型/传参/visited 查错/缺 return
    261: 3,   # Graph Valid Tree:模板抄错 -> flag 覆盖 -> 缺边数检查
    130: 2,   # 被围绕区域:数字零 vs 字母 O、T 没刹车
    200: 2,   # 岛屿数量:count 放进 dfs、刹车缺失
    417: 2,   # 太平洋大西洋:两个海共用一个 visited
    207: 2,   # 课程表:adj 方向反了(DFS 版 + Kahn 版都要盲写)
    33:  1,   # 旋转数组搜索:当时靠大量 print 才调通
    153: 1,
    424: 1,
    743: 1,   # Dijkstra:忘了累计 t1+t2,写成了 Prim
    853: 1,   # Car Fleet:else if / 忘 return
    128: 1,   # 最长连续序列:返回 length 而非 max_
}

# 15 个算法模板,和 00_templates.md 对应。它们也走 SRS,定期盲写。
TEMPLATES = [
    (9001, "并查集 Union-Find", 11, "Graphs", "Hard"),
    (9002, "网格 DFS 三刹车", 11, "Graphs", "Medium"),
    (9003, "多源 BFS 层循环", 11, "Graphs", "Medium"),
    (9004, "拓扑排序 Kahn", 11, "Graphs", "Medium"),
    (9005, "回溯骨架", 10, "Backtracking", "Medium"),
    (9006, "二分查找闭区间", 5, "Binary Search", "Medium"),
    (9007, "滑动窗口", 3, "Sliding Window", "Medium"),
    (9008, "单调栈", 4, "Stack", "Medium"),
    (9009, "链表三件套", 6, "Linked List", "Medium"),
    (9010, "树 DFS 与 BFS", 7, "Trees", "Easy"),
    (9011, "Trie 前缀树", 8, "Tries", "Medium"),
    (9012, "堆 heapq", 9, "Heap / Priority Queue", "Easy"),
    (9013, "Dijkstra / Prim / Bellman-Ford", 12, "Advanced Graphs", "Hard"),
    (9014, "DP 三问 + 记忆化", 13, "1-D DP", "Medium"),
    (9015, "区间合并 + 扫描线", 16, "Intervals", "Medium"),
]


def main() -> None:
    reset = "--reset" in sys.argv
    if reset:
        Base.metadata.drop_all(bind=engine)
        print("🗑  已清空旧库")
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
                    in_neetcode150=item["in_neetcode150"], kind="problem",
                    notes=item["notes"], code=item["code"],
                )
                db.add(p)
                db.flush()
                added += 1
            else:
                # 增量更新静态字段,不碰做题记录
                p.title, p.difficulty = item["title"], item["difficulty"]
                p.url = item["url"] or p.url
                if item["notes"] and not p.notes:
                    p.notes = item["notes"]
                if item["code"] and not p.code:
                    p.code = item["code"]
                updated += 1

            # 已解的题 -> 立即到期,进复习队列
            if item["solved"] and p.state is None:
                lapses = KNOWN_LAPSES.get(item["number"], 0)
                db.add(ReviewState(
                    problem_id=p.id, interval_days=1,
                    # 翻过车的题 ease 调低,间隔涨得慢一些
                    ease=max(1.3, DEFAULT_EASE - 0.2 * lapses),
                    reps=1, lapses=lapses, due=today, total_attempts=0,
                ))
                with_state += 1

        # 模板
        t_added = 0
        for num, name, ch_num, ch, diff in TEMPLATES:
            if num in existing:
                continue
            t = Problem(
                number=num, title=name, difficulty=diff, chapter_num=ch_num,
                chapter=ch, url="", in_neetcode150=False, kind="template",
                notes="盲写练习:见 00_templates.md", code="",
            )
            db.add(t)
            db.flush()
            db.add(ReviewState(problem_id=t.id, interval_days=0, due=today))
            t_added += 1

        db.commit()
    finally:
        db.close()

    print(f"\n✅ 导入完成")
    print(f"   新增题目: {added}   更新: {updated}")
    print(f"   已解 -> 今日到期: {with_state}")
    print(f"   模板: {t_added}")


if __name__ == "__main__":
    main()
