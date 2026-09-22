"""Mistake tags — derived from real bugs hit while practicing, not a generic checklist.

This is the most valuable feature of the app: after a few dozen attempts it can tell you
"40% of your bugs are X" and generate a personalised pre-submit checklist (see /stats/mistakes).
"""

MISTAKE_TAGS: list[dict[str, str]] = [
    {"id": "missing_visited_brake", "label": "Missing visited guard in DFS",
     "hint": "Three guards: out of bounds / invalid cell / already visited — the last one is the one you forget"},
    {"id": "type_confusion", "label": "Type confusion",
     "hint": "Is the grid int or str? '0' (zero) != 'O' (letter) — check the signature first"},
    {"id": "forgot_return", "label": "Forgot to return",
     "hint": "Printing instead of returning — the judge only looks at the return value"},
    {"id": "scope_confusion", "label": "Loop-local vs outer variable",
     "hint": "Inside the loop = this round's value, outside = the global one. Return the global one"},
    {"id": "direction_reversed", "label": "Direction or comparison reversed",
     "hint": "Edge direction, climb-vs-flow, < vs > — verify with the smallest example"},
    {"id": "off_by_one", "label": "Off-by-one / boundary",
     "hint": "mid +/- 1 in binary search, inclusive vs exclusive ranges, k vs k+1"},
    {"id": "shared_state", "label": "Shared state that should be separate",
     "hint": "Two questions need two ledgers (e.g. one visited set per ocean in Pacific Atlantic)"},
    {"id": "pass_by_value", "label": "Pass-by-value doesn't propagate",
     "hint": "Mutating an int parameter inside recursion is lost — use a return value or nonlocal"},
    {"id": "no_snapshot", "label": "Missing snapshot",
     "hint": "Step-limited DP/Bellman-Ford must read old, write new — otherwise one round jumps several edges"},
    {"id": "while_vs_if", "label": "Used if where while was needed",
     "hint": "Union-Find find, sliding-window shrink — these must loop, not check once"},
    {"id": "wrong_ds", "label": "Wrong data structure",
     "hint": "Shortest path needs BFS not DFS; frequent lookups need a set not a list"},
    {"id": "timeout", "label": "Time limit exceeded",
     "hint": "Missing memoization / missing pruning / wrong complexity analysis"},
    {"id": "misread_problem", "label": "Misread the problem",
     "hint": "Work through the smallest example by hand before writing code"},
    {"id": "left_debug_print", "label": "Left a debug print in",
     "hint": "At best it's slow, at worst it's Output Limit Exceeded"},
    {"id": "wrong_output_format", "label": "Wrong return format or order",
     "hint": "Smaller index first? Does it need sorting? Is the return type right?"},
]

MISTAKE_IDS = {t["id"] for t in MISTAKE_TAGS}

GRADE_LABELS = {
    "again": "Didn't get it / looked at solution",
    "hard": "Struggled or had bugs",
    "good": "Solved smoothly",
    "easy": "Nailed it",
}
