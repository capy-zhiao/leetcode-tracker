"""Fetch LeetCode's Top Interview 150 study plan into data/top_interview_150.json.

The study plan page is rendered client-side, so this asks LeetCode's public GraphQL API
for the same data the page loads. Re-run it if LeetCode changes the plan.

    python3 scripts/fetch_top_interview_150.py
"""
import json
import urllib.request
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "data" / "top_interview_150.json"
QUERY = """query studyPlanDetail($slug: String!) {
  studyPlanV2Detail(planSlug: $slug) {
    name
    planSubGroups { name questions { questionFrontendId title titleSlug difficulty } }
  }
}"""


def main() -> None:
    body = json.dumps({"query": QUERY, "variables": {"slug": "top-interview-150"}}).encode()
    req = urllib.request.Request(
        "https://leetcode.com/graphql", data=body,
        headers={"Content-Type": "application/json",
                 "Referer": "https://leetcode.com/studyplan/top-interview-150/",
                 # LeetCode answers 403 to urllib's default "Python-urllib/x.y" agent
                 "User-Agent": "Mozilla/5.0 (leetcode-tracker study-plan fetch)"},
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        plan = json.load(r)["data"]["studyPlanV2Detail"]

    problems = []
    for group in plan["planSubGroups"]:
        for q in group["questions"]:
            problems.append({
                "position": len(problems),        # order within the study plan
                "number": int(q["questionFrontendId"]),
                "title": q["title"],
                "slug": q["titleSlug"],
                "difficulty": q["difficulty"].capitalize(),
                "group": group["name"],
            })

    OUT.write_text(json.dumps({"plan": plan["name"], "count": len(problems),
                               "problems": problems}, indent=2) + "\n")
    print(f"{plan['name']}: {len(problems)} problems -> {OUT}")


if __name__ == "__main__":
    main()
