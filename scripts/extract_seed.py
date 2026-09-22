"""
把 neetcode 笔记仓库的 markdown 抽成 seed.json,供 app 后端导入。

用法: python3 scripts/extract_seed.py
输出: data/seed.json
"""
import json, re, glob, os, urllib.request

NOTES_DIR = "/Users/zhiao/Desktop/Coding_interview/neetcode"
OUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
NC250_URL = ("https://raw.githubusercontent.com/ascherj/neetcode-250-guide/"
             "main/neetcode_250_complete.json")

CHAPTER_NAMES = {
    "01": "Arrays & Hashing", "02": "Two Pointers", "03": "Sliding Window",
    "04": "Stack", "05": "Binary Search", "06": "Linked List", "07": "Trees",
    "08": "Tries", "09": "Heap / Priority Queue", "10": "Backtracking",
    "11": "Graphs", "12": "Advanced Graphs", "13": "1-D DP", "14": "2-D DP",
    "15": "Greedy", "16": "Intervals", "17": "Bit Manipulation",
    "18": "Math & Geometry",
}
DIFF_MAP = {"🟢": "Easy", "🟡": "Medium", "🔴": "Hard"}


def fetch_nc250_difficulty():
    """从官方 250 清单取难度,用题目名做 key(markdown 表格没覆盖增补题)。"""
    try:
        with urllib.request.urlopen(NC250_URL, timeout=20) as r:
            data = json.loads(r.read())
        return {p["name"].strip().lower(): p["difficulty"] for p in data["problems"]}
    except Exception as e:
        print(f"  ⚠️  拉取 nc250 难度失败({e}),只用 markdown 表格里的难度")
        return {}


def parse_difficulty_table(text):
    """解析章节顶部的题目清单表 -> {题号: 难度}"""
    out = {}
    for line in text.splitlines():
        if not line.startswith("|"):
            continue
        m = re.match(r"^\|\s*(\d+)\s*\|.*?([🟢🟡🔴])", line)
        if m:
            out[int(m.group(1))] = DIFF_MAP[m.group(2)]
    return out


def parse_sections(text):
    """切出每道题的 section: (题号, 标题, 正文)"""
    # 以 '## 数字. 标题' 为界切分
    parts = re.split(r"^## (\d+)\.\s*(.+?)\s*$", text, flags=re.M)
    # parts = [前言, 号, 标题, 正文, 号, 标题, 正文, ...]
    for i in range(1, len(parts), 3):
        yield int(parts[i]), parts[i + 1].strip(), parts[i + 2]


def extract_block(body, label):
    """取 '**思路：**' 或 '**代码：**' 后面第一个 ``` 代码块的内容"""
    m = re.search(rf"\*\*{label}：?\*\*\s*\n+```(?:python)?\n(.*?)\n?```", body, re.S)
    return m.group(1).strip() if m else ""


def main():
    nc_diff = fetch_nc250_difficulty()
    problems, seen = [], {}

    for path in sorted(glob.glob(os.path.join(NOTES_DIR, "[0-1][0-9]_*.md"))):
        fname = os.path.basename(path)
        ch_num = fname[:2]
        text = open(path, encoding="utf-8").read()
        table_diff = parse_difficulty_table(text)
        is_extra_zone = False

        for num, title, body in parse_sections(text):
            if num in seen:                       # 同题重复出现(150 + 250 区)
                continue
            link = ""
            m = re.search(r"\*\*链接：?\*\*\s*(\S+)", body)
            if m:
                link = m.group(1)
            is_extra_zone = "list=neetcode250" in link

            notes = extract_block(body, "思路")
            code = extract_block(body, "代码")
            solved = bool(code) and "待补充" not in code
            if notes in ("待补充", ""):
                notes = ""

            difficulty = (table_diff.get(num)
                          or nc_diff.get(title.lower())
                          or "Medium")

            seen[num] = True
            problems.append({
                "number": num,
                "title": title,
                "difficulty": difficulty,
                "chapter_num": int(ch_num),
                "chapter": CHAPTER_NAMES[ch_num],
                "url": link,
                "in_neetcode150": not is_extra_zone,
                "solved": solved,          # 已写过代码 -> 导入后直接进 SRS 队列
                "notes": notes,            # 你的思路笔记
                "code": code if solved else "",
            })

    os.makedirs(OUT_DIR, exist_ok=True)
    out_path = os.path.join(OUT_DIR, "seed.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump({"problems": problems, "count": len(problems)},
                  f, ensure_ascii=False, indent=2)

    solved = sum(p["solved"] for p in problems)
    print(f"\n✅ 导出 {len(problems)} 题 -> {out_path}")
    print(f"   已解(带代码): {solved}    待做: {len(problems)-solved}")
    print(f"   带思路笔记:   {sum(bool(p['notes']) for p in problems)}")
    print("\n   按章节:")
    for ch in sorted({p["chapter_num"] for p in problems}):
        g = [p for p in problems if p["chapter_num"] == ch]
        s = sum(x["solved"] for x in g)
        bar = "█" * round(s / len(g) * 20)
        print(f"     {ch:>2} {CHAPTER_NAMES[f'{ch:02d}']:<22} {s:>2}/{len(g):<3} {bar}")


if __name__ == "__main__":
    main()
