"""Grading a blind-written template against the reference.

Pure functions — no database, no clock — so the scoring rules can be unit tested directly.

Two independent signals:
  checks      did the load-bearing lines appear? (this is the one that matters)
  similarity  how close is the shape overall? (soft signal, naming differences are fine)
"""
from __future__ import annotations

import difflib
import re
from dataclasses import dataclass

from .templates_ref import BY_NUMBER, TemplateRef

# A blind-write passes when every check fires. Similarity alone never passes it, because
# you can write something that reads like the template and still miss the one line that
# makes it correct.
PASS_CHECK_RATIO = 1.0
GOOD_SIMILARITY = 0.55


def strip_comments(line: str) -> str:
    """Drop a trailing # comment, ignoring #s that live inside string literals."""
    out, quote = [], None
    i = 0
    while i < len(line):
        ch = line[i]
        if quote:
            if ch == "\\":
                out.append(line[i:i + 2])
                i += 2
                continue
            if ch == quote:
                quote = None
        elif ch in "'\"":
            quote = ch
        elif ch == "#":
            break
        out.append(ch)
        i += 1
    return "".join(out)


def normalize(code: str) -> list[str]:
    """Comment-free, blank-free, whitespace-collapsed lines — what we actually compare."""
    lines = []
    for raw in code.splitlines():
        line = strip_comments(raw).rstrip()
        if not line.strip():
            continue
        indent = len(line) - len(line.lstrip())
        body = re.sub(r"\s+", " ", line.strip())
        lines.append(" " * (indent // 4 * 4) + body)
    return lines


def similarity(reference: str, written: str) -> float:
    """0..1 shape match. Deliberately whitespace- and comment-insensitive."""
    ref, usr = normalize(reference), normalize(written)
    if not usr:
        return 0.0
    return difflib.SequenceMatcher(None, "\n".join(ref), "\n".join(usr)).ratio()


def run_checks(tpl: TemplateRef, written: str) -> list[dict]:
    """Which load-bearing lines are present. Regexes run against the normalized source."""
    haystack = "\n".join(normalize(written))
    results = []
    for c in tpl.checks:
        hit = any(re.search(p, haystack, re.IGNORECASE) for p in c.patterns)
        results.append({"id": c.id, "label": c.label, "why": c.why, "passed": hit})
    return results


def unified_diff(reference: str, written: str) -> list[str]:
    """Reference vs. what you wrote, normalized so indentation noise doesn't dominate."""
    return list(difflib.unified_diff(
        normalize(reference), normalize(written),
        fromfile="reference", tofile="you wrote", lineterm="", n=2,
    ))


@dataclass(frozen=True)
class BlindWriteResult:
    number: int
    name: str
    passed: bool
    similarity: float
    checks: list[dict]
    missing: list[str]
    diff: list[str]
    reference: str
    verdict: str


def grade(number: int, written: str) -> BlindWriteResult | None:
    """Grade one blind-write. Returns None when `number` is not a known template."""
    tpl = BY_NUMBER.get(number)
    if tpl is None:
        return None

    checks = run_checks(tpl, written)
    missing = [c["label"] for c in checks if not c["passed"]]
    ratio = (len(checks) - len(missing)) / len(checks) if checks else 0.0
    sim = similarity(tpl.reference, written)
    passed = ratio >= PASS_CHECK_RATIO

    if not written.strip():
        verdict = "Nothing written yet."
    elif passed and sim >= GOOD_SIMILARITY:
        verdict = "All checkpoints hit and the shape matches. This one is solid."
    elif passed:
        verdict = "All checkpoints hit. The wording differs from the reference, which is fine."
    elif len(missing) == 1:
        verdict = f"One checkpoint missing: {missing[0]}."
    else:
        verdict = f"{len(missing)} checkpoints missing — read the diff before retrying."

    return BlindWriteResult(
        number=number, name=tpl.name, passed=passed,
        similarity=round(sim, 3), checks=checks, missing=missing,
        diff=unified_diff(tpl.reference, written),
        reference=tpl.reference, verdict=verdict,
    )


def suggested_grade(result: BlindWriteResult) -> str:
    """Map a blind-write result onto the SRS grades, so templates reuse the same engine."""
    if not result.passed:
        return "again" if len(result.missing) > 1 else "hard"
    if result.similarity >= GOOD_SIMILARITY:
        return "easy"
    return "good"
