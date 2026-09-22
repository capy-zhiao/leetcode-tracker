"""Reference implementations for the 15 algorithm templates, plus the checkpoints that
matter most when blind-writing them.

`checks` is the pedagogically interesting half. Each one encodes a mistake that actually
cost time in practice ("find must loop, not branch once"), so a blind-write is graded on
whether the load-bearing line is present, not just on textual similarity.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Check:
    id: str
    label: str                       # what we look for
    why: str                         # why it matters — shown when it is missing
    patterns: list[str] = field(default_factory=list)   # any regex matching = pass


@dataclass(frozen=True)
class TemplateRef:
    number: int
    name: str
    reference: str
    checks: list[Check]


TEMPLATES: list[TemplateRef] = [
    TemplateRef(9001, "Union-Find", '''parent = list(range(n))

def find(x):
    while parent[x] != x:
        parent[x] = parent[parent[x]]
        x = parent[x]
    return x

def union(a, b):
    ra, rb = find(a), find(b)
    if ra == rb:
        return False
    parent[ra] = rb
    return True''', [
        Check("uf_while", "find climbs with while, not if",
              "if only climbs one level, so you never reach the root (this cost you 261)",
              [r"while\s+\w+\[\s*\w+\s*\]\s*!="]),
        Check("uf_compress", "path compression",
              "parent[x] = parent[parent[x]] hangs the node on its grandparent",
              [r"\w+\[\s*\w+\s*\]\s*=\s*\w+\[\s*\w+\[\s*\w+\s*\]\s*\]"]),
        Check("uf_roots", "union merges roots, not the raw nodes",
              "parent[ra] = rb. Writing ra = parent[rb] leaves the ledger untouched",
              [r"=\s*find\s*\(.*\)\s*,\s*find\s*\(", r"\w+\[\s*r\w+\s*\]\s*=\s*r\w+"]),
        Check("uf_cycle", "same root returns False",
              "connecting two nodes already in the same set creates a cycle",
              [r"if\s+r\w+\s*==\s*r\w+", r"return\s+False"]),
    ]),

    TemplateRef(9002, "Grid DFS (three guards)", '''def dfs(r, c):
    if r < 0 or c < 0 or r >= ROWS or c >= COLS:
        return
    if grid[r][c] != TARGET:
        return
    if (r, c) in visited:
        return
    visited.add((r, c))
    dfs(r + 1, c)
    dfs(r - 1, c)
    dfs(r, c + 1)
    dfs(r, c - 1)''', [
        Check("dfs_bounds", "guard 1: out of bounds, checked first",
              "any other order indexes the grid before knowing the index is legal",
              [r"r\s*<\s*0", r">=\s*ROWS", r">=\s*rows", r"0\s*<=\s*r\s*<"]),
        Check("dfs_target", "guard 2: not the cell we want",
              "exclusion style — 'anything that isn't mine returns' beats a whitelist if",
              [r"!=\s*", r"not\s+in\s+"]),
        Check("dfs_visited", "guard 3: already visited",
              "the guard you forget. Without it you recurse forever (you have hit this 3x)",
              [r"in\s+visit\w*", r"visit\w*\[", r"==\s*['\"]?T['\"]?"]),
        Check("dfs_mark", "mark before recursing",
              "add to visited before the four calls, otherwise the neighbour re-enters",
              [r"visit\w*\.add", r"visit\w*\[.*\]\s*=", r"grid\[\s*r\s*\]\[\s*c\s*\]\s*="]),
        Check("dfs_four", "all four directions",
              "r+1, r-1, c+1, c-1 — or a direction list",
              [r"(dfs\s*\(.*\)[\s;]*){4}", r"\[\s*\(\s*1\s*,\s*0\s*\)", r"for\s+dr\s*,\s*dc\s+in"]),
    ]),

    TemplateRef(9003, "Multi-source BFS (level loop)", '''q = deque(all_sources)
steps = 0
while q and fresh > 0:
    for _ in range(len(q)):
        r, c = q.popleft()
        for dr, dc in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < ROWS and 0 <= nc < COLS and grid[nr][nc] == TARGET:
                grid[nr][nc] = NEW_STATE
                fresh -= 1
                q.append((nr, nc))
    steps += 1
return steps if fresh == 0 else -1''', [
        Check("bfs_level", "level loop pins the current layer",
              "for _ in range(len(q)) IS the clock. Without it steps counts nodes, not layers",
              [r"for\s+\w+\s+in\s+range\s*\(\s*len\s*\(\s*\w+\s*\)\s*\)"]),
        Check("bfs_steps_outside", "steps increments outside the level loop",
              "one increment per layer, not per node",
              [r"steps\s*\+=\s*1", r"\w+\s*\+=\s*1"]),
        Check("bfs_guard", "while guard covers an empty target",
              "while q and fresh > 0 — stops counting one layer too many",
              [r"while\s+\w+\s+and\s+\w+\s*>\s*0"]),
        Check("bfs_bounds_first", "bounds checked before indexing",
              "0 <= nr < ROWS goes first in the and-chain; a negative index silently wraps",
              [r"0\s*<=\s*n?r\w*\s*<", r"n?r\w*\s*>=\s*0"]),
        Check("bfs_mark_then_push", "mutate the cell, then enqueue",
              "changing the value IS the visited mark",
              [r"grid\[\s*\w+\s*\]\[\s*\w+\s*\]\s*="]),
    ]),

    TemplateRef(9004, "Topological sort (Kahn)", '''indegree = [0] * n
adj = defaultdict(list)
for crs, pre in prerequisites:
    indegree[crs] += 1
    adj[pre].append(crs)

q = deque(c for c in range(n) if indegree[c] == 0)
finished = 0
while q:
    cur = q.popleft()
    finished += 1
    for nxt in adj[cur]:
        indegree[nxt] -= 1
        if indegree[nxt] == 0:
            q.append(nxt)
return finished == n''', [
        Check("kahn_direction", "edge points prerequisite -> course",
              "adj[pre].append(crs). You reversed this once and every answer flipped",
              [r"adj\s*\[\s*pre\w*\s*\]\s*\.\s*append", r"\[\s*\w*pre\w*\s*\]\s*\.\s*append"]),
        Check("kahn_indegree", "indegree counts prerequisites",
              "indegree[crs] += 1 — the course owes, the prerequisite is owed",
              [r"indegree\s*\[\s*\w+\s*\]\s*\+=\s*1", r"\w+\s*\[\s*\w+\s*\]\s*\+=\s*1"]),
        Check("kahn_seed", "seed the queue over range(n)",
              "isolated courses also have indegree 0 and must start in the queue",
              [r"range\s*\(\s*n\w*\s*\)"]),
        Check("kahn_zero", "enqueue only when it hits exactly 0",
              "decrement then test == 0, otherwise a course enters twice",
              [r"==\s*0"]),
        Check("kahn_count", "finish condition compares the count to n",
              "anything inside a cycle never leaves the queue",
              [r"\w+\s*==\s*n\w*", r"len\s*\(\s*\w+\s*\)\s*==\s*n"]),
    ]),

    TemplateRef(9005, "Backtracking skeleton", '''def backtrack(start):
    if is_done:
        res.append(path[:])
        return
    for i in range(start, len(nums)):
        if i > start and nums[i] == nums[i - 1]:
            continue
        path.append(nums[i])
        backtrack(i + 1)
        path.pop()''', [
        Check("bt_copy", "append a copy of path, not path itself",
              "path[:] or list(path). Appending the object itself gets mutated later",
              [r"path\s*\[\s*:\s*\]", r"list\s*\(\s*path\s*\)", r"\.copy\s*\(\s*\)", r"\[\s*:\s*\]\s*\)"]),
        Check("bt_pop", "undo with pop after the recursive call",
              "append -> recurse -> pop. Dropping the pop leaks state into the next branch",
              [r"\.pop\s*\(\s*\)", r"\.remove\s*\("]),
        Check("bt_start", "pass the right index onwards",
              "combinations pass i+1, reuse passes i, permutations use a used[] array instead",
              [r"backtrack\s*\(\s*i\s*\+\s*1\s*\)", r"backtrack\s*\(\s*i\s*\)", r"used\s*\["]),
        Check("bt_dedup", "duplicate skip needs a sort first",
              "if i > start and nums[i] == nums[i-1]: continue",
              [r"i\s*>\s*start", r"continue"]),
    ]),

    TemplateRef(9006, "Binary search (closed interval)", '''left, right = 0, len(nums) - 1
while left <= right:
    mid = (left + right) // 2
    if nums[mid] == target:
        return mid
    elif nums[mid] < target:
        left = mid + 1
    else:
        right = mid - 1
return -1''', [
        Check("bs_equals", "while left <= right, with the equals sign",
              "a closed interval still has one candidate when left == right",
              [r"while\s+\w+\s*<=\s*\w+"]),
        Check("bs_plus_one", "left = mid + 1",
              "leaving off the +1 loops forever when left and mid collide",
              [r"=\s*mid\s*\+\s*1"]),
        Check("bs_minus_one", "right = mid - 1",
              "same trap on the other side",
              [r"=\s*mid\s*-\s*1"]),
        Check("bs_mid", "mid computed inside the loop",
              "computing it once above the loop never narrows anything",
              [r"mid\s*=.*//\s*2"]),
    ]),

    TemplateRef(9007, "Sliding window", '''left = 0
best = 0
for right in range(len(s)):
    # s[right] enters the window, update state
    while not_valid(state):
        # s[left] leaves the window, update state
        left += 1
    best = max(best, right - left + 1)
return best''', [
        Check("sw_while", "shrink with while, not if",
              "one step of shrinking is often not enough to restore validity",
              [r"while\s+"]),
        Check("sw_after", "update the answer after shrinking",
              "inside the shrink loop the window is still illegal",
              [r"best\s*=\s*max", r"res\s*=\s*max", r"=\s*max\s*\("]),
        Check("sw_width", "window width is right - left + 1",
              "the classic off-by-one",
              [r"right\s*-\s*left\s*\+\s*1", r"r\s*-\s*l\s*\+\s*1"]),
        Check("sw_symmetric", "state is maintained on both ends",
              "whatever you add when right enters, you subtract when left leaves",
              [r"left\s*\+=\s*1", r"l\s*\+=\s*1"]),
    ]),

    TemplateRef(9008, "Monotonic stack", '''stack = []
result = [0] * len(nums)
for i, x in enumerate(nums):
    while stack and nums[stack[-1]] < x:
        j = stack.pop()
        result[j] = i - j
    stack.append(i)
return result''', [
        Check("ms_index", "store indices, not values",
              "you need the index to compute a distance",
              [r"stack\s*\.\s*append\s*\(\s*i\s*\)", r"\.append\s*\(\s*\w*i\w*\s*\)"]),
        Check("ms_while", "pop with while",
              "one new element can settle several stacked ones",
              [r"while\s+stack\s+and", r"while\s+\w+\s+and"]),
        Check("ms_settle", "settle the popped element",
              "the moment you pop is the moment its answer is known",
              [r"\.pop\s*\(\s*\)"]),
        Check("ms_push_self", "push the current index afterwards",
              "easy to forget once the while loop is written",
              [r"\.append\s*\("]),
    ]),

    TemplateRef(9009, "Linked list trio", '''# 1. reverse
prev, cur = None, head
while cur:
    nxt = cur.next
    cur.next = prev
    prev, cur = cur, nxt
return prev

# 2. dummy head
dummy = ListNode(0, head)
# ... work on dummy ...
return dummy.next

# 3. fast / slow
slow = fast = head
while fast and fast.next:
    slow = slow.next
    fast = fast.next.next''', [
        Check("ll_save_next", "save next before rewiring",
              "cur.next = prev destroys the forward link; grab nxt first",
              [r"n\w*t\w*\s*=\s*\w+\.next"]),
        Check("ll_return_prev", "reverse returns prev, not cur",
              "when the loop ends cur is None and prev is the new head",
              [r"return\s+prev"]),
        Check("ll_dummy", "dummy node and dummy.next",
              "use it whenever the head itself might be removed or replaced",
              [r"dummy", r"return\s+\w+\.next"]),
        Check("ll_fast_guard", "while fast and fast.next",
              "checking only fast crashes on fast.next.next for even-length lists",
              [r"while\s+fast\s+and\s+fast\s*\.\s*next"]),
    ]),

    TemplateRef(9010, "Tree DFS and BFS", '''# DFS
def dfs(node):
    if not node:
        return 0
    left, right = dfs(node.left), dfs(node.right)
    return 1 + max(left, right)

# BFS by level
q = deque([root])
while q:
    for _ in range(len(q)):
        node = q.popleft()
        if node.left:
            q.append(node.left)
        if node.right:
            q.append(node.right)''', [
        Check("tree_base", "null check is the base case",
              "if not node: return <identity value>",
              [r"if\s+not\s+\w+\s*:", r"if\s+\w+\s+is\s+None"]),
        Check("tree_combine", "combine the two children's return values",
              "decide what the subproblem returns and how it merges — that IS tree DFS",
              [r"return\s+.*(left|l)\b.*", r"max\s*\(", r"\+\s*1"]),
        Check("tree_no_int_param", "carry results by return value or nonlocal",
              "mutating an int parameter inside recursion does not propagate (you hit this)",
              [r"return\s+", r"nonlocal\s+"]),
        Check("tree_level", "BFS pins the layer with range(len(q))",
              "same clock as multi-source BFS",
              [r"range\s*\(\s*len\s*\(\s*\w+\s*\)\s*\)"]),
    ]),

    TemplateRef(9011, "Trie", '''class TrieNode:
    def __init__(self):
        self.children = {}
        self.is_end = False

def insert(word):
    cur = root
    for ch in word:
        if ch not in cur.children:
            cur.children[ch] = TrieNode()
        cur = cur.children[ch]
    cur.is_end = True

def search(word):
    cur = root
    for ch in word:
        if ch not in cur.children:
            return False
        cur = cur.children[ch]
    return cur.is_end          # startsWith is identical but returns True here''', [
        Check("trie_children", "each node owns a children dict",
              "children maps one character to the next node",
              [r"children"]),
        Check("trie_is_end", "is_end flag set at the end of insert",
              "the classic omission — without it search always returns False",
              [r"is_?end\w*\s*=\s*True"]),
        Check("trie_walk", "walk down, creating missing nodes",
              "if ch not in cur.children: create, then descend",
              [r"not\s+in\s+\w+\.children", r"cur\s*=\s*cur\s*\.\s*children"]),
        Check("trie_search_vs_prefix", "search returns is_end, startsWith returns True",
              "the only difference between the two methods is that last line",
              [r"return\s+\w*\.?is_?end", r"return\s+True"]),
    ]),

    TemplateRef(9012, "Heap (heapq)", '''heap = []
for num in nums:
    heapq.heappush(heap, num)
    if len(heap) > k:
        heapq.heappop(heap)
return heap[0]''', [
        Check("heap_size_k", "keep the heap at size k",
              "kth largest = min-heap of size k; the root is the answer",
              [r"len\s*\(\s*\w+\s*\)\s*>\s*k", r">\s*k\s*:"]),
        Check("heap_pop_excess", "pop as soon as it overflows",
              "push then pop — that is what keeps the k largest",
              [r"heappop"]),
        Check("heap_root", "the answer is heap[0]",
              "Python's heapq is a min-heap, so the root is the smallest of the k kept",
              [r"heap\s*\[\s*0\s*\]", r"\w+\s*\[\s*0\s*\]"]),
        Check("heap_max_negate", "max-heap means pushing negatives",
              "Python has no max-heap; push -x and negate on the way out",
              [r"heappush", r"-\s*\w+"]),
    ]),

    TemplateRef(9013, "Dijkstra / Prim / Bellman-Ford", '''# Dijkstra
dist = {}
heap = [(0, src)]
while heap:
    d, node = heapq.heappop(heap)
    if node in dist:
        continue
    dist[node] = d
    for nei, w in graph[node]:
        if nei not in dist:
            heapq.heappush(heap, (d + w, nei))
return dist

# Bellman-Ford with k stops: snapshot each round
for _ in range(k + 1):
    tmp = dist[:]
    for u, v, w in flights:
        if dist[u] != INF and dist[u] + w < tmp[v]:
            tmp[v] = dist[u] + w
    dist = tmp''', [
        Check("dij_tuple_order", "heap entries are (distance, node)",
              "distance first, or the heap sorts by node id",
              [r"\(\s*0\s*,\s*\w+\s*\)", r"\(\s*d\w*\s*\+\s*w\w*\s*,"]),
        Check("dij_skip_stale", "skip a node already finalised",
              "first pop is the shortest; later pops are stale duplicates",
              [r"if\s+\w+\s+in\s+dist\s*:\s*continue", r"in\s+(dist|visit\w*)"]),
        Check("dij_accumulate", "push the accumulated distance d + w",
              "pushing just w turns Dijkstra into Prim (you did exactly this on 743)",
              [r"d\w*\s*\+\s*w"]),
        Check("bf_snapshot", "Bellman-Ford reads dist and writes tmp",
              "without the snapshot one round jumps several edges, breaking the k-stop limit",
              [r"tmp\s*=\s*dist\s*\[\s*:\s*]", r"tmp\s*=\s*.*cop|tmp\s*=\s*list\s*\(", r"tmp\s*\["]),
    ]),

    TemplateRef(9014, "DP three questions + memoization", '''# bottom-up
dp = [0] * (n + 1)
dp[0], dp[1] = 1, 1
for i in range(2, n + 1):
    dp[i] = dp[i - 1] + dp[i - 2]
return dp[n]

# rolling variables
prev2, prev1 = 1, 1
for _ in range(2, n + 1):
    prev2, prev1 = prev1, prev1 + prev2
return prev1

# top-down
@cache
def dfs(i):
    if i <= 1:
        return 1
    return dfs(i - 1) + dfs(i - 2)''', [
        Check("dp_table", "allocate the table with room for the boundary",
              "n+1 entries so dp[0] is the empty case and you skip a pile of special cases",
              [r"\*\s*\(\s*n\w*\s*\+\s*1\s*\)", r"range\s*\(\s*\w+\s*\+\s*1\s*\)"]),
        Check("dp_base", "set the base values explicitly",
              "question 3 of the three questions — answer it before writing the loop",
              [r"dp\s*\[\s*0\s*\]", r"prev\w*\s*,", r"if\s+i\s*<="]),
        Check("dp_transition", "write the recurrence",
              "question 2 — dp[i] in terms of earlier entries",
              [r"dp\s*\[\s*i\s*\]\s*=", r"return\s+\w+\s*\(\s*i\s*-\s*1\s*\)"]),
        Check("dp_memo", "memoize the top-down version",
              "@cache or a dict. Without it you are back to exponential",
              [r"@cache", r"@lru_cache", r"memo"]),
    ]),

    TemplateRef(9015, "Interval merge + sweep line", '''intervals.sort(key=lambda x: x[0])
merged = [intervals[0]]
for s, e in intervals[1:]:
    if s <= merged[-1][1]:
        merged[-1][1] = max(merged[-1][1], e)
    else:
        merged.append([s, e])
return merged''', [
        Check("iv_sort", "sort first — by start to merge",
              "merging sorts by start (56/57); keeping the most non-overlapping sorts by end (435)",
              [r"\.sort\s*\(", r"sorted\s*\("]),
        Check("iv_key", "sort key picks the right endpoint",
              "key=lambda x: x[0] for merge, x[1] for the greedy variant",
              [r"key\s*=\s*lambda"]),
        Check("iv_overlap", "overlap test against the last kept interval",
              "s <= merged[-1][1]",
              [r"\[\s*-\s*1\s*\]\s*\[\s*1\s*\]"]),
        Check("iv_extend", "extend with max, do not overwrite",
              "the incoming interval may end earlier than the one already there",
              [r"max\s*\("]),
    ]),
]

BY_NUMBER: dict[int, TemplateRef] = {t.number: t for t in TEMPLATES}
