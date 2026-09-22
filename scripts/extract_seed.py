"""Extract the NeetCode markdown notes into seed.json for the backend to import.

Usage:  python3 scripts/extract_seed.py
Output: data/seed.json
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
    """Pull difficulty from the official 250 list, keyed by title.

    The per-chapter markdown tables do not cover the problems appended later.
    """
    try:
        with urllib.request.urlopen(NC250_URL, timeout=20) as r:
            data = json.loads(r.read())
        return {p["name"].strip().lower(): p["difficulty"] for p in data["problems"]}
    except Exception as e:
        print(f"  warning: could not fetch the nc250 list ({e}); using markdown tables only")
        return {}


def parse_difficulty_table(text):
    """Parse the problem table at the top of a chapter file -> {number: difficulty}."""
    out = {}
    for line in text.splitlines():
        if not line.startswith("|"):
            continue
        m = re.match(r"^\|\s*(\d+)\s*\|.*?([🟢🟡🔴])", line)
        if m:
            out[int(m.group(1))] = DIFF_MAP[m.group(2)]
    return out


def parse_sections(text):
    """Split the file into per-problem sections: (number, title, body)."""
    # Split on '## <number>. <title>' headings
    parts = re.split(r"^## (\d+)\.\s*(.+?)\s*$", text, flags=re.M)
    # parts = [preamble, num, title, body, num, title, body, ...]
    for i in range(1, len(parts), 3):
        yield int(parts[i]), parts[i + 1].strip(), parts[i + 2]


# The source markdown notes use Chinese section labels, so the parser matches those
# literals. They are data, not UI text, and must stay as-is for extraction to work.
LABEL_APPROACH, LABEL_CODE, PLACEHOLDER = "思路", "代码", "待补充"


def extract_block(body, label):
    """Grab the first fenced block following the given label heading."""
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
            if num in seen:                       # same problem in both the 150 and 250 sections
                continue
            link = ""
            m = re.search(r"\*\*链接：?\*\*\s*(\S+)", body)   # "link:" label in the notes
            if m:
                link = m.group(1)
            is_extra_zone = "list=neetcode250" in link

            notes = extract_block(body, LABEL_APPROACH)
            code = extract_block(body, LABEL_CODE)
            solved = bool(code) and PLACEHOLDER not in code
            if notes in (PLACEHOLDER, ""):
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
                "solved": solved,          # has code -> enters the SRS queue on import
                "notes": notes,            # the approach notes written while solving
                "code": code if solved else "",
            })

    os.makedirs(OUT_DIR, exist_ok=True)
    out_path = os.path.join(OUT_DIR, "seed.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump({"problems": problems, "count": len(problems)},
                  f, ensure_ascii=False, indent=2)

    solved = sum(p["solved"] for p in problems)
    print(f"\nExported {len(problems)} problems -> {out_path}")
    print(f"  solved (with code): {solved}    remaining: {len(problems)-solved}")
    print(f"  with notes:         {sum(bool(p['notes']) for p in problems)}")
    print("\n  by chapter:")
    for ch in sorted({p["chapter_num"] for p in problems}):
        g = [p for p in problems if p["chapter_num"] == ch]
        s = sum(x["solved"] for x in g)
        bar = "█" * round(s / len(g) * 20)
        print(f"     {ch:>2} {CHAPTER_NAMES[f'{ch:02d}']:<22} {s:>2}/{len(g):<3} {bar}")


if __name__ == "__main__":
    main()
