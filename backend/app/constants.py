"""错误模式标签 —— 直接照着真实踩坑史定义的,不是通用清单。

这是这个 app 最有价值的功能:积累几十次之后,能算出「你 40% 的错是 XX」,
并自动生成个人版的提交前自查清单(见 /stats/mistakes)。
"""

MISTAKE_TAGS: list[dict[str, str]] = [
    {"id": "missing_visited_brake", "label": "DFS 缺「已访问」刹车", "hint": "三个刹车:越界 / 不合法 / 已访问,最后那个最容易漏"},
    {"id": "type_confusion",        "label": "类型混淆",            "hint": "格子是 int 还是 str?'0'(零)≠ 'O'(欧)—— 先看函数签名"},
    {"id": "forgot_return",         "label": "忘了 return",          "hint": "只 print 不 return,判题器只看返回值"},
    {"id": "scope_confusion",       "label": "循环内外变量混淆",      "hint": "循环内 = 本轮的,循环外 = 全局的;交卷要交全局那个"},
    {"id": "direction_reversed",    "label": "方向/条件写反",         "hint": "adj 方向、爬山 vs 水流、大于小于 —— 拿最小例子验一遍"},
    {"id": "off_by_one",            "label": "边界 / ±1",            "hint": "二分的 mid±1、区间开闭、k vs k+1"},
    {"id": "shared_state",          "label": "该分开的状态共用了",     "hint": "两个问题要两本账(417 两个海各一个 visited)"},
    {"id": "pass_by_value",         "label": "值传递传不回来",        "hint": "int 当参数传进递归改不回来,用返回值或 nonlocal"},
    {"id": "no_snapshot",           "label": "该拍快照没拍",          "hint": "限步数的 DP/BF 要读旧写新(tmp),否则一轮连跳多步"},
    {"id": "while_vs_if",           "label": "while 写成 if",        "hint": "并查集 find、滑窗收缩 —— 要一直循环,不是判一次"},
    {"id": "wrong_ds",              "label": "选错数据结构",          "hint": "最短路要 BFS 不能 DFS;查询频繁要 set 不用 list"},
    {"id": "timeout",               "label": "超时",                 "hint": "缺记忆化 / 缺剪枝 / 复杂度想错了"},
    {"id": "misread_problem",       "label": "题意理解错",            "hint": "先用最小例子手算一遍再动手"},
    {"id": "left_debug_print",      "label": "忘删 print",           "hint": "轻则 TLE,重则 Output Limit Exceeded"},
    {"id": "wrong_output_format",   "label": "返回格式/顺序错",       "hint": "下标小的放前面、要不要排序、返回类型对不对"},
]

MISTAKE_IDS = {t["id"] for t in MISTAKE_TAGS}

GRADE_LABELS = {
    "again": "不会 / 看了答案",
    "hard": "卡壳或有 bug",
    "good": "顺利做出",
    "easy": "秒杀",
}
