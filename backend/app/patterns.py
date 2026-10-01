"""Algorithm patterns — the axis an interviewer actually thinks along.

Chapters follow the NeetCode roadmap, which is a teaching order. Patterns cut across it:
239 lives in the Sliding Window chapter but is really a monotonic deque, and 787 lives in
Advanced Graphs but is really Bellman-Ford. Grouping proficiency by pattern answers
"which technique do I fumble" rather than "how far down the roadmap am I".
"""
from __future__ import annotations

# id -> (display label, one-line description)
PATTERNS: dict[str, tuple[str, str]] = {
    "array-scan":           ("Linear scan", "One pass with a running value or write pointer"),
    "hashmap":              ("Hash map / set", "Trade memory for O(1) lookup"),
    "counting":             ("Frequency counting", "Counter of characters or values"),
    "prefix-sum":           ("Prefix sum", "Precompute running totals to answer ranges in O(1)"),
    "sorting":              ("Sorting", "Sort first so a greedy or two-pointer pass works"),
    "two-pointers":         ("Two pointers", "Converge from both ends, or a read/write pair"),
    "fast-slow":            ("Fast & slow pointers", "Cycle detection and midpoint finding"),
    "sliding-window":       ("Sliding window", "Grow right, shrink left while invalid"),
    "monotonic-stack":      ("Monotonic stack / deque", "Keep the stack ordered; pop settles an answer"),
    "stack-simulation":     ("Stack simulation", "Nesting, matching and parsing"),
    "binary-search":        ("Binary search", "Halve a sorted search space"),
    "binary-search-answer": ("Binary search on the answer", "Guess a value, verify feasibility"),
    "linked-list":          ("Linked list surgery", "Pointer rewiring, dummy heads"),
    "tree-dfs":             ("Tree DFS", "Decide what the subproblem returns and how it merges"),
    "tree-bfs":             ("Tree BFS", "Level order with the range(len(q)) clock"),
    "bst":                  ("BST property", "Left < node < right narrows the search"),
    "trie":                 ("Trie", "Prefix tree over a character alphabet"),
    "heap":                 ("Heap / top-K", "Keep only what matters at the frontier"),
    "backtracking":         ("Backtracking", "Choose, recurse, undo"),
    "grid-dfs":             ("Grid DFS / flood fill", "Three guards, mark before recursing"),
    "graph-dfs":            ("Graph DFS / BFS", "Traversal over an adjacency list"),
    "bfs-shortest":         ("BFS shortest path", "Unweighted shortest path by layer"),
    "multi-source-bfs":     ("Multi-source BFS", "All sources enqueued at once, layers are the clock"),
    "union-find":           ("Union-Find", "Connectivity and cycle detection"),
    "topological-sort":     ("Topological sort", "Kahn's indegree peel, or DFS cycle detection"),
    "dijkstra":             ("Dijkstra", "Weighted shortest path with a heap"),
    "bellman-ford":         ("Bellman-Ford", "Edge relaxation with a snapshot per round"),
    "mst":                  ("Minimum spanning tree", "Kruskal or Prim"),
    "dp-1d":                ("1-D DP", "dp[i] from earlier entries"),
    "dp-knapsack":          ("Knapsack DP", "Items versus capacity"),
    "dp-grid":              ("Grid DP", "dp[i][j] from the cells above and to the left"),
    "dp-string":            ("Two-string DP", "Compare s1[i-1] with s2[j-1]"),
    "dp-interval":          ("Interval DP", "Enumerate by interval length"),
    "greedy":               ("Greedy", "Local best choice provably reaches the global best"),
    "intervals":            ("Intervals", "Sort by an endpoint, then merge or sweep"),
    "bit-manipulation":     ("Bit manipulation", "XOR, masks and shifts"),
    "math":                 ("Math", "Number theory, digits, closed forms"),
    "matrix":               ("Matrix simulation", "In-place rotation, spiral order, transpose"),
    "design":               ("Data structure design", "Compose structures to hit a complexity target"),
}

# Deliberately hand-assigned rather than derived from the chapter, so cross-cutting
# problems land on the technique they actually test.
PROBLEM_PATTERNS: dict[int, tuple[str, ...]] = {
    # 1 Arrays & Hashing
    1: ("hashmap",), 6: ("array-scan",), 12: ("greedy", "math"), 14: ("array-scan",),
    27: ("two-pointers",), 28: ("array-scan",), 36: ("hashmap", "matrix"),
    49: ("hashmap", "counting"), 58: ("array-scan",), 68: ("array-scan", "greedy"),
    80: ("two-pointers",), 122: ("greedy",), 128: ("hashmap",), 151: ("array-scan",),
    169: ("counting",), 205: ("hashmap",), 217: ("hashmap",), 238: ("prefix-sum",),
    242: ("counting",), 271: ("design",), 274: ("sorting",), 290: ("hashmap",),
    334: ("greedy",), 345: ("two-pointers",), 347: ("counting", "heap"),
    380: ("design", "hashmap"), 383: ("counting",), 443: ("two-pointers",),
    605: ("greedy", "array-scan"), 724: ("prefix-sum",), 1207: ("counting", "hashmap"),
    1431: ("array-scan",), 1657: ("counting", "sorting"), 1732: ("prefix-sum",),
    2215: ("hashmap",), 2352: ("hashmap", "matrix"),
    # 2 Two Pointers
    11: ("two-pointers", "greedy"), 15: ("two-pointers", "sorting"), 26: ("two-pointers",),
    42: ("two-pointers", "monotonic-stack"), 88: ("two-pointers",), 125: ("two-pointers",),
    167: ("two-pointers",), 189: ("array-scan",), 283: ("two-pointers",),
    392: ("two-pointers",), 1679: ("two-pointers", "hashmap"), 1768: ("two-pointers",),
    # 3 Sliding Window
    3: ("sliding-window", "hashmap"), 30: ("sliding-window", "hashmap"),
    76: ("sliding-window", "counting"), 121: ("array-scan", "greedy"),
    209: ("sliding-window",), 219: ("sliding-window", "hashmap"),
    239: ("monotonic-stack", "sliding-window"), 424: ("sliding-window", "counting"),
    567: ("sliding-window", "counting"), 643: ("sliding-window",),
    1004: ("sliding-window",), 1456: ("sliding-window",), 1493: ("sliding-window",),
    # 4 Stack
    20: ("stack-simulation",), 22: ("backtracking",), 71: ("stack-simulation",),
    84: ("monotonic-stack",), 150: ("stack-simulation",),
    155: ("design", "stack-simulation"), 224: ("stack-simulation",),
    394: ("stack-simulation",), 735: ("stack-simulation",), 739: ("monotonic-stack",),
    853: ("monotonic-stack", "sorting"), 901: ("monotonic-stack", "design"),
    933: ("design",), 2390: ("stack-simulation",),
    # 5 Binary Search
    4: ("binary-search",), 33: ("binary-search",), 34: ("binary-search",),
    35: ("binary-search",), 69: ("binary-search-answer", "math"),
    74: ("binary-search", "matrix"), 153: ("binary-search",), 162: ("binary-search",),
    374: ("binary-search",), 704: ("binary-search",), 875: ("binary-search-answer",),
    981: ("binary-search", "design"), 2300: ("binary-search", "sorting"),
    # 6 Linked List
    2: ("linked-list",), 19: ("linked-list", "fast-slow"), 21: ("linked-list",),
    23: ("linked-list", "heap"), 25: ("linked-list",), 61: ("linked-list",),
    82: ("linked-list",), 86: ("linked-list",), 92: ("linked-list",),
    138: ("linked-list", "hashmap"), 141: ("fast-slow",), 143: ("linked-list", "fast-slow"),
    146: ("design", "linked-list", "hashmap"), 148: ("linked-list", "sorting"),
    206: ("linked-list",), 287: ("fast-slow",), 328: ("linked-list",),
    2095: ("fast-slow", "linked-list"), 2130: ("fast-slow", "linked-list"),
    # 7 Trees
    98: ("bst", "tree-dfs"), 100: ("tree-dfs",), 101: ("tree-dfs",), 102: ("tree-bfs",),
    103: ("tree-bfs",), 104: ("tree-dfs",), 105: ("tree-dfs",), 106: ("tree-dfs",),
    108: ("bst", "tree-dfs"), 110: ("tree-dfs",), 112: ("tree-dfs",), 114: ("tree-dfs",),
    117: ("tree-bfs",), 124: ("tree-dfs",), 129: ("tree-dfs",), 173: ("bst", "design"),
    199: ("tree-bfs",), 222: ("tree-dfs", "binary-search"), 226: ("tree-dfs",),
    230: ("bst", "tree-dfs"), 235: ("bst",), 236: ("tree-dfs",),
    297: ("tree-dfs", "design"), 427: ("tree-dfs", "matrix"),
    437: ("tree-dfs", "prefix-sum"), 450: ("bst",), 530: ("bst", "tree-dfs"),
    543: ("tree-dfs",), 572: ("tree-dfs",), 637: ("tree-bfs",), 700: ("bst",),
    872: ("tree-dfs",), 1161: ("tree-bfs",), 1372: ("tree-dfs",), 1448: ("tree-dfs",),
    # 8 Tries
    208: ("trie", "design"), 211: ("trie", "design", "backtracking"),
    212: ("trie", "backtracking", "grid-dfs"), 1268: ("trie",),
    # 9 Heap / Priority Queue
    215: ("heap",), 295: ("heap", "design"), 355: ("heap", "design"), 373: ("heap",),
    502: ("heap", "greedy"), 621: ("heap", "greedy", "counting"), 703: ("heap", "design"),
    973: ("heap", "sorting"), 1046: ("heap",), 2336: ("heap", "design"), 2462: ("heap",),
    2542: ("heap", "sorting"),
    # 10 Backtracking
    17: ("backtracking",), 39: ("backtracking",), 40: ("backtracking",),
    46: ("backtracking",), 51: ("backtracking",), 52: ("backtracking",),
    77: ("backtracking",), 78: ("backtracking",), 79: ("backtracking", "grid-dfs"),
    90: ("backtracking",), 131: ("backtracking",), 216: ("backtracking",),
    # 11 Graphs
    127: ("bfs-shortest",), 130: ("grid-dfs",), 133: ("graph-dfs", "hashmap"),
    200: ("grid-dfs",), 207: ("topological-sort",), 210: ("topological-sort",),
    261: ("union-find", "graph-dfs"), 286: ("multi-source-bfs",),
    323: ("union-find", "graph-dfs"), 399: ("graph-dfs", "union-find"), 417: ("grid-dfs",),
    433: ("bfs-shortest",), 547: ("union-find", "graph-dfs"), 684: ("union-find",),
    695: ("grid-dfs",), 841: ("graph-dfs",), 909: ("bfs-shortest",),
    994: ("multi-source-bfs",), 1466: ("graph-dfs",), 1926: ("bfs-shortest",),
    # 12 Advanced Graphs
    269: ("topological-sort",), 332: ("graph-dfs",), 743: ("dijkstra",),
    778: ("dijkstra", "binary-search-answer"), 787: ("bellman-ford",),
    1584: ("mst", "union-find"),
    # 13 1-D DP
    5: ("dp-string",), 70: ("dp-1d",), 91: ("dp-1d",), 139: ("dp-1d",), 152: ("dp-1d",),
    198: ("dp-1d",), 213: ("dp-1d",), 300: ("dp-1d",), 322: ("dp-knapsack",),
    416: ("dp-knapsack",), 647: ("dp-string",), 746: ("dp-1d",), 790: ("dp-1d",),
    1137: ("dp-1d",),
    # 14 2-D DP
    10: ("dp-string",), 62: ("dp-grid",), 63: ("dp-grid",), 64: ("dp-grid",),
    72: ("dp-string",), 97: ("dp-string",), 115: ("dp-string",), 120: ("dp-grid",),
    123: ("dp-1d",), 188: ("dp-1d",), 221: ("dp-grid", "matrix"), 309: ("dp-1d",),
    312: ("dp-interval",), 329: ("grid-dfs", "dp-grid"), 494: ("dp-knapsack",),
    518: ("dp-knapsack",), 714: ("dp-1d",), 1143: ("dp-string",),
    # 15 Greedy
    45: ("greedy",), 53: ("greedy", "dp-1d"), 55: ("greedy",), 134: ("greedy",),
    135: ("greedy",), 649: ("greedy", "stack-simulation"), 678: ("greedy",),
    763: ("greedy", "intervals"), 846: ("greedy", "counting"), 918: ("greedy", "dp-1d"),
    1899: ("greedy",),
    # 16 Intervals
    56: ("intervals", "sorting"), 57: ("intervals",), 228: ("array-scan", "intervals"),
    252: ("intervals", "sorting"), 253: ("intervals", "heap"), 435: ("intervals", "greedy"),
    452: ("intervals", "greedy"), 1851: ("intervals", "heap", "sorting"),
    # 17 Bit Manipulation
    7: ("math",), 67: ("bit-manipulation", "math"), 136: ("bit-manipulation",),
    137: ("bit-manipulation",), 190: ("bit-manipulation",), 191: ("bit-manipulation",),
    201: ("bit-manipulation",), 268: ("bit-manipulation", "math"),
    338: ("bit-manipulation", "dp-1d"), 371: ("bit-manipulation",),
    1318: ("bit-manipulation",),
    # 18 Math & Geometry
    9: ("math",), 13: ("hashmap", "math"), 43: ("math",), 48: ("matrix",), 50: ("math",),
    54: ("matrix",), 66: ("math", "array-scan"), 73: ("matrix",), 149: ("math", "hashmap"),
    172: ("math",), 202: ("fast-slow", "hashmap", "math"), 289: ("matrix",),
    1071: ("math",), 2013: ("design", "hashmap"),
}

# Fallback for anything not listed above, so a new problem still lands somewhere sane.
CHAPTER_FALLBACK: dict[int, str] = {
    1: "hashmap", 2: "two-pointers", 3: "sliding-window", 4: "stack-simulation",
    5: "binary-search", 6: "linked-list", 7: "tree-dfs", 8: "trie", 9: "heap",
    10: "backtracking", 11: "graph-dfs", 12: "graph-dfs", 13: "dp-1d",
    14: "dp-grid", 15: "greedy", 16: "intervals", 17: "bit-manipulation",
    18: "math",
}

# Which template drills each pattern, so a weak pattern links to the drill that fixes it.
PATTERN_TEMPLATE: dict[str, int] = {
    "union-find": 9001, "grid-dfs": 9002, "multi-source-bfs": 9003,
    "bfs-shortest": 9003, "topological-sort": 9004, "backtracking": 9005,
    "binary-search": 9006, "binary-search-answer": 9006, "sliding-window": 9007,
    "monotonic-stack": 9008, "linked-list": 9009, "fast-slow": 9009,
    "tree-dfs": 9010, "tree-bfs": 9010, "bst": 9010, "trie": 9011, "heap": 9012,
    "dijkstra": 9013, "bellman-ford": 9013, "mst": 9013, "dp-1d": 9014,
    "dp-knapsack": 9014, "dp-grid": 9014, "dp-string": 9014, "dp-interval": 9014,
    "intervals": 9015,
}


def patterns_for(number: int, chapter_num: int) -> list[str]:
    tags = PROBLEM_PATTERNS.get(number)
    if tags:
        return list(tags)
    fallback = CHAPTER_FALLBACK.get(chapter_num)
    return [fallback] if fallback else []


def label(pattern_id: str) -> str:
    return PATTERNS.get(pattern_id, (pattern_id, ""))[0]


def describe(pattern_id: str) -> str:
    return PATTERNS.get(pattern_id, ("", ""))[1]
