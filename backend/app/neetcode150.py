"""The official NeetCode 150, by roadmap chapter.

The in_neetcode150 flag used to be inferred from which section of the markdown notes a
problem sat in, and that drifted: Math & Geometry and Bit Manipulation were dropped from
the notes and only recreated during the 250 expansion, and Generate Parentheses was
missing from the original list — 16 problems of the 150 ended up flagged as 250 extras.
This list is now the single source of truth; seed_db.py applies it on every run.
"""

NEETCODE_150_BY_CHAPTER: dict[int, tuple[int, ...]] = {
    1: (217, 242, 1, 49, 347, 271, 238, 36, 128),
    2: (125, 167, 15, 11, 42),
    3: (121, 3, 424, 567, 76, 239),
    4: (20, 155, 150, 22, 739, 853, 84),
    5: (704, 74, 875, 153, 33, 981, 4),
    6: (206, 21, 143, 19, 138, 2, 141, 287, 146, 23, 25),
    7: (226, 104, 543, 110, 100, 572, 235, 102, 199, 1448, 98, 230, 105, 124, 297),
    8: (208, 211, 212),
    9: (703, 1046, 973, 215, 621, 355, 295),
    10: (78, 39, 46, 90, 40, 79, 131, 17, 51),
    11: (200, 695, 133, 286, 994, 417, 130, 207, 210, 684, 323, 261, 127),
    12: (332, 1584, 743, 778, 269, 787),
    13: (70, 746, 198, 213, 5, 647, 91, 322, 152, 139, 300, 416),
    14: (62, 1143, 309, 518, 494, 97, 72, 329, 115, 312, 10),
    15: (53, 55, 45, 134, 846, 1899, 763, 678),
    16: (57, 56, 435, 252, 253, 1851),
    17: (136, 191, 338, 190, 268, 371, 7),
    18: (48, 54, 73, 202, 66, 50, 43, 2013),
}

NEETCODE_150: frozenset[int] = frozenset(
    n for numbers in NEETCODE_150_BY_CHAPTER.values() for n in numbers
)

# (chapter, position within the chapter) — NeetCode's own teaching order, which is not
# problem-number order: 1-D DP runs 70, 746, 198, 213, 5, ... rather than 5, 70, 91, ...
NEETCODE_150_POSITION: dict[int, tuple[int, int]] = {
    n: (chapter, i)
    for chapter, numbers in NEETCODE_150_BY_CHAPTER.items()
    for i, n in enumerate(numbers)
}
