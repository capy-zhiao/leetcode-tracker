"""Complexity self-check.

Interviewers ask for time and space on essentially every problem, but nothing in the
practice loop forced an answer. Now the submit form does.

Two design choices worth noting:
  * answers are normalized before comparison, so "O(m * n)" == "O(n*m)" == "O(N M)"
  * each problem accepts a LIST of answers, because several are genuinely ambiguous
    (3Sum's space is O(1) or O(n) depending on whether the sort counts)
The first entry is the canonical one shown as "the expected answer".
"""
from __future__ import annotations

import re

# Offered in the picker. Free text is still allowed — it is just recorded, not graded.
COMPLEXITY_CHOICES: list[str] = [
    "O(1)", "O(log n)", "O(h)", "O(sqrt n)", "O(n)", "O(n log n)",
    "O(n log k)", "O(n log m)", "O(n sqrt n)", "O(n^2)", "O(n^2 log n)", "O(n^3)",
    "O(m + n)", "O(m * n)", "O(n * k)", "O(k * E)", "O(V)", "O(V + E)",
    "O(E log V)", "O(E log E)", "O(log (m + n))", "O(log (m * n))",
    "O(2^n)", "O(n * 2^n)", "O(n * 4^n)", "O(n!)", "O(n * n!)",
]


def normalize(text: str) -> str:
    """Canonical form, so equivalent spellings compare equal.

    O(n*m) / O(M N) / O(m * n)  -> "m * n"
    O(n log n) / O(N*LogN)      -> "log n * n"
    O(V+E) / O(E + V)           -> "e + v"
    """
    s = (text or "").strip().lower()
    s = s.replace("²", "^2").replace("³", "^3").replace("**", "^")
    s = re.sub(r"^o\s*\(", "", s)
    s = re.sub(r"\)$", "", s)
    s = s.replace("*", " ")
    s = re.sub(r"\s*\+\s*", " + ", s)          # "m+n" -> "m + n", so it tokenizes as a sum
    s = re.sub(r"log\s*", "log ", s)            # "logn" -> "log n"
    s = re.sub(r"\s+", " ", s).strip()
    if not s:
        return ""

    # Merge "log" with the token it applies to, then sort so factor order stops mattering.
    words = s.split(" ")
    terms: list[str] = []
    i = 0
    while i < len(words):
        if words[i] in ("log", "sqrt") and i + 1 < len(words):
            terms.append(f"{words[i]} {words[i + 1]}")
            i += 2
        else:
            terms.append(words[i])
            i += 1
    # A sum like "m + n" is order-insensitive too, but must not be reordered against a product.
    if "+" in terms:
        parts = sorted(t for t in terms if t != "+")
        return " + ".join(parts)
    return " * ".join(sorted(terms))


def matches(answer: str, accepted: list[str]) -> bool:
    n = normalize(answer)
    return bool(n) and any(n == normalize(a) for a in accepted)


# number -> (accepted time answers, accepted space answers)
# Only problems whose canonical solution has an unambiguous complexity are listed. Anything
# absent is still recorded, just not graded — better silent than confidently wrong.
#
# Graph problems: space is the auxiliary space (visited map, parent array, recursion
# stack), so O(V) — O(V + E) is also accepted for counting an adjacency list or the cloned
# output. Where the problem's n IS the node count (133 / 261 / 323), O(n) means O(V).
# 261's time also accepts O(n): it returns early unless len(edges) == n - 1, so E < V.
EXPECTED: dict[int, tuple[list[str], list[str]]] = {
    # --- 1 Arrays & Hashing ---
    217: (["O(n)"], ["O(n)"]),            242: (["O(n)"], ["O(1)", "O(n)"]),
    1:   (["O(n)"], ["O(n)"]),            49:  (["O(m * n)"], ["O(m * n)"]),
    347: (["O(n)"], ["O(n)"]),            271: (["O(n)"], ["O(n)"]),
    238: (["O(n)"], ["O(1)", "O(n)"]),    128: (["O(n)"], ["O(n)"]),
    169: (["O(n)"], ["O(1)"]),            27:  (["O(n)"], ["O(1)"]),
    122: (["O(n)"], ["O(1)"]),
    # --- 2 Two Pointers ---
    125: (["O(n)"], ["O(1)"]),            167: (["O(n)"], ["O(1)"]),
    15:  (["O(n^2)"], ["O(1)", "O(n)"]),  11:  (["O(n)"], ["O(1)"]),            42:  (["O(n)"], ["O(1)"]),
    26:  (["O(n)"], ["O(1)"]),            88:  (["O(m + n)"], ["O(1)"]),
    189: (["O(n)"], ["O(1)"]),
    # --- 3 Sliding Window ---
    121: (["O(n)"], ["O(1)"]),            3:   (["O(n)"], ["O(n)"]),
    424: (["O(n)"], ["O(1)", "O(n)"]),    567: (["O(n)"], ["O(1)"]),
    76:  (["O(n)", "O(m + n)"], ["O(n)"]), 239: (["O(n)"], ["O(n)"]),
    209: (["O(n)"], ["O(1)"]),            219: (["O(n)"], ["O(n)"]),
    # --- 4 Stack ---
    20:  (["O(n)"], ["O(n)"]),            155: (["O(1)"], ["O(n)"]),
    150: (["O(n)"], ["O(n)"]),            739: (["O(n)"], ["O(n)"]),
    853: (["O(n log n)"], ["O(n)"]),      84:  (["O(n)"], ["O(n)"]),
    71:  (["O(n)"], ["O(n)"]),            # --- 5 Binary Search ---
    704: (["O(log n)"], ["O(1)"]),        74:  (["O(log (m * n))", "O(log n)"], ["O(1)"]),
    875: (["O(n log m)"], ["O(1)"]),      153: (["O(log n)"], ["O(1)"]),
    33:  (["O(log n)"], ["O(1)"]),        981: (["O(log n)"], ["O(n)"]),
    4:   (["O(log (m + n))"], ["O(1)"]),  35:  (["O(log n)"], ["O(1)"]),
    69:  (["O(log n)"], ["O(1)"]),        # --- 6 Linked List ---
    206: (["O(n)"], ["O(1)"]),            21:  (["O(m + n)"], ["O(1)"]),
    143: (["O(n)"], ["O(1)"]),            19:  (["O(n)"], ["O(1)"]),
    138: (["O(n)"], ["O(n)"]),            2:   (["O(m + n)"], ["O(1)", "O(n)"]),
    141: (["O(n)"], ["O(1)"]),            287: (["O(n)"], ["O(1)"]),
    146: (["O(1)"], ["O(n)"]),            23:  (["O(n log k)"], ["O(n * k)", "O(n)"]),
    25:  (["O(n)"], ["O(1)"]),            92:  (["O(n)"], ["O(1)"]),
    # --- 7 Trees ---
    226: (["O(n)"], ["O(h)", "O(n)"]),    104: (["O(n)"], ["O(h)", "O(n)"]),
    543: (["O(n)"], ["O(h)", "O(n)"]),    110: (["O(n)"], ["O(h)", "O(n)"]),
    100: (["O(n)"], ["O(h)", "O(n)"]),    572: (["O(m * n)"], ["O(h)", "O(n)"]),
    235: (["O(h)", "O(log n)"], ["O(1)"]),102: (["O(n)"], ["O(n)"]),
    199: (["O(n)"], ["O(n)"]),            1448:(["O(n)"], ["O(h)", "O(n)"]),
    98:  (["O(n)"], ["O(h)", "O(n)"]),    230: (["O(n)", "O(h)"], ["O(h)", "O(n)"]),
    105: (["O(n)"], ["O(n)"]),            124: (["O(n)"], ["O(h)", "O(n)"]),
    297: (["O(n)"], ["O(n)"]),            # --- 8 Tries ---
    208: (["O(n)"], ["O(m * n)", "O(n)"]),# --- 9 Heap ---
    703: (["O(log k)", "O(log n)"], ["O(k)"]), 1046:(["O(n log n)"], ["O(n)"]),
    973: (["O(n log k)"], ["O(k)"]),      215: (["O(n log k)", "O(n)"], ["O(k)"]),
    621: (["O(n)"], ["O(1)"]),            295: (["O(log n)"], ["O(n)"]),
    502: (["O(n log n)"], ["O(n)"]),
    # --- 10 Backtracking ---
    78:  (["O(n * 2^n)"], ["O(n)"]),      39:  (["O(2^n)", "O(n * 2^n)"], ["O(n)"]),
    46:  (["O(n * n!)"], ["O(n)"]),       90:  (["O(n * 2^n)"], ["O(n)"]),
    40:  (["O(n * 2^n)"], ["O(n)"]),      131: (["O(n * 2^n)"], ["O(n)"]),
    17:  (["O(n * 4^n)"], ["O(n)"]),      51:  (["O(n!)"], ["O(n^2)", "O(n)"]),
    52:  (["O(n!)"], ["O(n)"]),           # --- 11 Graphs ---
    200: (["O(m * n)"], ["O(m * n)"]),    695: (["O(m * n)"], ["O(m * n)"]),
    133: (["O(V + E)"], ["O(V)", "O(n)", "O(V + E)"]),    286: (["O(m * n)"], ["O(m * n)"]),
    994: (["O(m * n)"], ["O(m * n)"]),    417: (["O(m * n)"], ["O(m * n)"]),
    130: (["O(m * n)"], ["O(m * n)"]),    207: (["O(V + E)"], ["O(V + E)"]),
    210: (["O(V + E)"], ["O(V + E)"]),    261: (["O(V + E)", "O(n)"], ["O(V)", "O(n)", "O(V + E)"]),
    323: (["O(V + E)"], ["O(V)", "O(n)", "O(V + E)"]),    684: (["O(n)"], ["O(n)"]),
    # --- 12 Advanced Graphs ---
    743: (["O(E log V)"], ["O(V + E)"]),  787: (["O(k * E)"], ["O(V + E)", "O(n)"]),
    1584:(["O(n^2 log n)"], ["O(n^2)"]),  778: (["O(n^2 log n)"], ["O(n^2)"]),
    332: (["O(E log E)"], ["O(V + E)"]),
    # --- 13 1-D DP ---
    70:  (["O(n)"], ["O(1)"]),            746: (["O(n)"], ["O(1)"]),
    198: (["O(n)"], ["O(1)"]),            213: (["O(n)"], ["O(1)"]),
    5:   (["O(n^2)"], ["O(1)"]),          647: (["O(n^2)"], ["O(1)"]),
    91:  (["O(n)"], ["O(1)", "O(n)"]),    322: (["O(n * m)"], ["O(n)"]),
    152: (["O(n)"], ["O(1)"]),            139: (["O(n * m)"], ["O(n)"]),
    300: (["O(n^2)", "O(n log n)"], ["O(n)"]), 416: (["O(n * m)"], ["O(n)"]),
    # --- 14 2-D DP ---
    62:  (["O(m * n)"], ["O(n)", "O(m * n)"]), 1143:(["O(m * n)"], ["O(m * n)", "O(n)"]),
    309: (["O(n)"], ["O(1)", "O(n)"]),    518: (["O(n * m)"], ["O(n)"]),
    494: (["O(n * m)"], ["O(n * m)"]),    97:  (["O(m * n)"], ["O(m * n)", "O(n)"]),
    72:  (["O(m * n)"], ["O(m * n)", "O(n)"]), 329: (["O(m * n)"], ["O(m * n)"]),
    115: (["O(m * n)"], ["O(m * n)", "O(n)"]), 312: (["O(n^3)"], ["O(n^2)"]),
    10:  (["O(m * n)"], ["O(m * n)"]),    63:  (["O(m * n)"], ["O(n)", "O(m * n)"]),
    64:  (["O(m * n)"], ["O(n)", "O(m * n)"]), # --- 15 Greedy ---
    53:  (["O(n)"], ["O(1)"]),            55:  (["O(n)"], ["O(1)"]),
    45:  (["O(n)"], ["O(1)"]),            134: (["O(n)"], ["O(1)"]),
    846: (["O(n log n)"], ["O(n)"]),      1899:(["O(n)"], ["O(1)"]),
    763: (["O(n)"], ["O(1)"]),            678: (["O(n)"], ["O(1)"]),
    135: (["O(n)"], ["O(n)"]),            918: (["O(n)"], ["O(1)"]),
    # --- 16 Intervals ---
    57:  (["O(n)"], ["O(n)"]),            56:  (["O(n log n)"], ["O(n)"]),
    435: (["O(n log n)"], ["O(1)", "O(n)"]), 252: (["O(n log n)"], ["O(1)", "O(n)"]),
    253: (["O(n log n)"], ["O(n)"]),      1851:(["O(n log n)"], ["O(n)"]),
    # --- 17 Bit Manipulation ---
    136: (["O(n)"], ["O(1)"]),            191: (["O(1)", "O(n)"], ["O(1)"]),
    338: (["O(n)"], ["O(n)"]),            190: (["O(1)"], ["O(1)"]),
    268: (["O(n)"], ["O(1)"]),            371: (["O(1)"], ["O(1)"]),
    7:   (["O(1)", "O(log n)"], ["O(1)"]),67:  (["O(m + n)"], ["O(m + n)"]),
    201: (["O(1)", "O(log n)"], ["O(1)"]),
    # --- 18 Math & Geometry ---
    13:  (["O(n)"], ["O(1)"]),            66:  (["O(n)"], ["O(1)", "O(n)"]),
    202: (["O(log n)"], ["O(1)", "O(log n)"]), 48:  (["O(n^2)"], ["O(1)"]),          54:  (["O(m * n)"], ["O(1)", "O(m * n)"]),
    73:  (["O(m * n)"], ["O(1)"]),        43:  (["O(m * n)"], ["O(m + n)"]),
    50:  (["O(log n)"], ["O(log n)"]),    2013:(["O(n)"], ["O(n)"]),
    # --- Top Interview 150 additions ---
    80: (["O(n)"], ["O(1)"]), 274: (["O(n log n)", "O(n)"], ["O(1)", "O(n)"]),
    380: (["O(1)"], ["O(n)"]), 12: (["O(1)"], ["O(1)"]), 58: (["O(n)"], ["O(1)"]),
    151: (["O(n)"], ["O(n)"]), 6: (["O(n)"], ["O(n)"]),
    28: (["O(m * n)", "O(m + n)"], ["O(1)", "O(n)"]), 392: (["O(n)", "O(m + n)"], ["O(1)"]),
    289: (["O(m * n)"], ["O(1)", "O(m * n)"]), 383: (["O(m + n)", "O(n)"], ["O(1)"]),
    205: (["O(n)"], ["O(1)", "O(n)"]), 290: (["O(n)", "O(m + n)"], ["O(n)"]),
    228: (["O(n)"], ["O(1)", "O(n)"]), 452: (["O(n log n)"], ["O(1)", "O(n)"]),
    224: (["O(n)"], ["O(n)"]), 82: (["O(n)"], ["O(1)"]), 61: (["O(n)"], ["O(1)"]),
    86: (["O(n)"], ["O(1)"]), 101: (["O(n)"], ["O(h)", "O(n)"]), 106: (["O(n)"], ["O(n)"]),
    117: (["O(n)"], ["O(1)", "O(n)"]), 114: (["O(n)"], ["O(1)", "O(h)", "O(n)"]),
    112: (["O(n)"], ["O(h)", "O(n)"]), 129: (["O(n)"], ["O(h)", "O(n)"]),
    173: (["O(1)"], ["O(h)"]), 236: (["O(n)"], ["O(h)", "O(n)"]), 637: (["O(n)"], ["O(n)"]),
    103: (["O(n)"], ["O(n)"]), 530: (["O(n)"], ["O(h)", "O(n)"]),
    909: (["O(n^2)"], ["O(n^2)"]), 108: (["O(n)"], ["O(log n)", "O(h)", "O(n)"]),
    148: (["O(n log n)"], ["O(log n)", "O(1)", "O(n)"]), 162: (["O(log n)"], ["O(1)"]),
    34: (["O(log n)"], ["O(1)"]), 373: (["O(k log k)"], ["O(k)"]),
    137: (["O(n)"], ["O(1)"]), 9: (["O(log n)", "O(1)"], ["O(1)"]),
    172: (["O(log n)"], ["O(1)"]), 149: (["O(n^2)"], ["O(n)"]),
    120: (["O(n^2)"], ["O(n)", "O(n^2)"]), 123: (["O(n)"], ["O(1)"]),
    188: (["O(n * k)"], ["O(k)", "O(n * k)"]), 221: (["O(m * n)"], ["O(n)", "O(m * n)"]),
    # --- LeetCode 75 additions ---
    1768: (["O(m + n)"], ["O(m + n)"]), 1071: (["O(m + n)"], ["O(m + n)"]),
    735: (["O(n)"], ["O(n)"]), 394: (["O(n)"], ["O(n)"]), 649: (["O(n)"], ["O(n)"]),
    450: (["O(h)", "O(log n)"], ["O(h)"]), 374: (["O(log n)"], ["O(1)"]),
    1137: (["O(n)"], ["O(1)"]), 1431: (["O(n)"], ["O(1)", "O(n)"]),
    605: (["O(n)"], ["O(1)"]), 345: (["O(n)"], ["O(n)", "O(1)"]), 334: (["O(n)"], ["O(1)"]),
    443: (["O(n)"], ["O(1)"]), 283: (["O(n)"], ["O(1)"]),
    1679: (["O(n)", "O(n log n)"], ["O(n)", "O(1)"]), 643: (["O(n)"], ["O(1)"]),
    1456: (["O(n)"], ["O(1)"]), 1004: (["O(n)"], ["O(1)"]), 1493: (["O(n)"], ["O(1)"]),
    1732: (["O(n)"], ["O(1)"]), 724: (["O(n)"], ["O(1)"]),
    2215: (["O(m + n)"], ["O(m + n)"]), 1207: (["O(n)"], ["O(n)"]),
    1657: (["O(n)", "O(n log n)"], ["O(1)", "O(n)"]), 2352: (["O(n^2)"], ["O(n^2)"]),
    2390: (["O(n)"], ["O(n)"]), 2095: (["O(n)"], ["O(1)"]), 328: (["O(n)"], ["O(1)"]),
    2130: (["O(n)"], ["O(1)", "O(n)"]), 1372: (["O(n)"], ["O(h)", "O(n)"]),
    1161: (["O(n)"], ["O(n)"]), 841: (["O(V + E)", "O(n)"], ["O(V)", "O(n)"]),
    547: (["O(n^2)"], ["O(n)"]), 1466: (["O(n)"], ["O(n)"]),
    1926: (["O(m * n)"], ["O(m * n)"]), 2336: (["O(log n)"], ["O(n)"]),
    2542: (["O(n log n)"], ["O(n)"]), 790: (["O(n)"], ["O(1)", "O(n)"]),
    714: (["O(n)"], ["O(1)"]), 1318: (["O(1)", "O(log n)"], ["O(1)"]),
}


def check(number: int, time_answer: str, space_answer: str) -> dict | None:
    """Grade one self-reported pair. None when we have no reference for this problem."""
    ref = EXPECTED.get(number)
    if ref is None:
        return None
    accepted_time, accepted_space = ref
    return {
        "time_ok": matches(time_answer, accepted_time),
        "space_ok": matches(space_answer, accepted_space),
        "expected_time": accepted_time[0],
        "expected_space": accepted_space[0],
        "accepted_time": accepted_time,
        "accepted_space": accepted_space,
    }
