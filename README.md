# 🧠 LeetCode Tracker

[![CI](https://github.com/capy-zhiao/leetcode-tracker/actions/workflows/ci.yml/badge.svg)](https://github.com/capy-zhiao/leetcode-tracker/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/python-3.12%20%7C%203.13-blue)
![React](https://img.shields.io/badge/react-18-61dafb)
![Tests](https://img.shields.io/badge/tests-177-brightgreen)

A spaced-repetition tracker for the **NeetCode 250**: it decides what to practise each day,
schedules reviews on a forgetting curve, tracks your personal bug patterns, and runs timed
mock interviews with LLM-generated follow-up questions.

> Built because a hand-maintained markdown study plan stops scaling at 250 problems —
> you cannot keep 250 review dates in your head, and when twenty come due at once there is
> no way to decide which four actually matter.

## ✨ Features

| Feature | What it does |
| --- | --- |
| **Adaptive scheduling** | Each problem's next review is computed from how the attempt actually went. When more is due than you can finish, the queue ranks by priority and defers the rest |
| **Daily queue** | Reviews + new problems + one template drill, replacing the manual plan |
| **Timer with auto-grading** | Stops the clock and suggests a grade from your time and the problem's difficulty — no guessing how well you "felt" you did |
| **Mistake pattern tracking** | 15 tags; once you have some history it ranks them into a **personal pre-submit checklist** |
| **Solution history & diff** | Every submission is archived, so a second pass can be compared against the first |
| **Mock interview** | Random problem, countdown, notes hidden, then **follow-up questions about the code you just wrote** — answer each in writing and an LLM grades it (strong / good / partial / weak, what you missed, a model answer) |
| **Template blind-writing** | Write one of 15 algorithm skeletons from memory; it is graded against **checkpoints** (does `find` loop with `while`?) rather than text similarity, then shown as a diff |
| **Complexity self-check** | Time and space are **required** before an attempt can be submitted, and graded against a reference for 217 of the 250 problems |
| **Proficiency by pattern** | 40 techniques cutting across the roadmap, ranked weakest first, each linked to the drill that fixes it |
| **Fully keyboard driven** | Space, 1-4, ⌘↵, J/K — one solve without touching the mouse |

## 🏗 Architecture

```
React + TypeScript + Vite + Tailwind      SPA frontend
          | REST
FastAPI + SQLAlchemy 2.0 + Pydantic v2    backend (auto-generated OpenAPI docs)
          |
SQLite (dev) / PostgreSQL (prod)
          |
Claude or DeepSeek                        interview follow-ups, grading, complexity check (optional)
```

**Design decisions worth calling out:**

- **The scheduling algorithm is a set of pure functions** (`app/srs.py`) — no database access,
  no clock reads (`today` is a parameter). That is what makes it fully unit-testable: 17 cases
  cover first intervals, growth curves, lapse resets, ease clamping and priority ordering.
- **The LLM layer is provider-agnostic** (`app/llm.py`). Claude uses native structured outputs;
  DeepSeek goes through its OpenAI-compatible endpoint with JSON mode plus Pydantic validation.
  Adding a third provider means implementing one `complete()` method.
- **Blind-write grading is by checkpoint, not by diff** (`app/blindwrite.py`). Text similarity
  is the wrong signal: a Union-Find with every identifier renamed scores 0.39 and is correct,
  while a binary search missing its `mid + 1` scores 0.92 and loops forever. Each template
  carries regex checkpoints for the lines that actually cause bugs, and a test asserts every
  reference implementation passes its own checkpoints.
- **Complexity answers are normalized before comparison** (`app/complexity.py`), so
  `O(m*n)`, `O(N M)` and `O(n * m)` are one answer, while each problem accepts a *list* of
  correct answers — 3Sum's space is O(1) or O(n) depending on whether the sort counts.
- **"Today" is the user's day, not UTC** (`app/deps.py`). Timestamps are stored in UTC, but
  a UTC day boundary falls at 20:00 the previous evening in EDT — so an evening session
  would land on the next date, showing tomorrow's queue at 8pm and breaking the streak.
  `TIMEZONE` pins the zone when deploying to a UTC server.
- **Storage is swappable** — `DATABASE_URL` alone moves you between SQLite and Postgres.
- **Everything degrades gracefully** — with no LLM configured, AI features return sensible
  fallbacks and the rest of the app is unaffected.

## 🧮 The scheduling algorithm

Coding problems are not flashcards. An Anki card takes five seconds and you can clear two
hundred a day; a LeetCode problem takes 20-45 minutes and you can manage six. Three changes
follow from that:

**1. The grade comes from measured behaviour, not self-assessment**

| Grade | Trigger | Effect |
| --- | --- | --- |
| `again` | looked at the solution | interval resets to 1 day, `ease -= 0.2`, lapse recorded |
| `hard` | struggled >15 min, or had bugs | `interval x 1.2` |
| `good` | solved smoothly (5-15 min) | `interval x ease` |
| `easy` | first try, under 5 min | `interval x ease x 1.3`, `ease += 0.1` |

First intervals are 1/2/4/7 days; `ease` is clamped to `[1.3, 3.0]` starting at 2.3;
**Hard problems get intervals multiplied by 0.8** because they decay faster. Time thresholds
scale with difficulty — twenty minutes is fine on a Hard problem and slow on an Easy one.

**2. A daily cap with priority ordering** (Anki has no equivalent, but you hit this on day one)

```
priority = days_overdue      x 1.0
         + lifetime_lapses   x 3.0     <- problems you've failed before surface first
         + difficulty_weight            (Hard 2 / Medium 1 / Easy 0)
         + (20 - chapter)    x 0.1     <- foundations before advanced topics
```

**3. The day is interleaved, not just ranked.** Ranking alone clusters: failures pile up in
whichever chapter was hardest, and on the first day of real use the top four reviews were
all graph problems. Four of a kind in a row means you know the technique before reading
the problem — skipping the recognition step an interview actually tests. So each chapter
and each primary pattern gets at most two slots a day, and anything skipped backfills
empty slots in priority order, so the limits change *which* problems you get, never how
many. Both limits are needed: capping patterns alone still gave four graph problems,
because Course Schedule is topological sort rather than grid DFS.

**4. New problems finish the NeetCode 150 first, in NeetCode's order.** New problems are
drawn from four tiers, each exhausted before the next: the 150's Easy/Medium in NeetCode's
own teaching order, then the 250 additions' Easy/Medium in a fixed shuffled order, then
the Hards of each. Chapters listed in `NEW_LATER_CHAPTERS` (default Bit Manipulation and
Math & Geometry) wait with the additions while staying flagged as NeetCode 150. Unlike
reviews, new problems are not spread across chapters by default — the order *is* the
plan. The shuffle is a hash of the problem number rather than a reshuffle per request, so
finishing one problem never swaps out the others.

## 🚀 Running it

**One command:**

```bash
./start.sh
```

It checks dependencies, seeds the database if needed, starts both servers, prints today's
queue, and opens the browser. `Ctrl+C` stops everything.

<details>
<summary>Or start the two halves manually</summary>

```bash
# backend
cd backend
python3 -m venv .venv && ./.venv/bin/pip install -r requirements.txt
cp .env.example .env
./.venv/bin/python seed_db.py
./.venv/bin/uvicorn app.main:app --reload     # docs at http://localhost:8000/docs

# frontend (second terminal)
cd frontend
npm install
npm run dev                                   # http://localhost:5173
```

</details>

Tests: `cd backend && ./.venv/bin/python -m pytest -q`

## 🤖 Enabling the AI features

Interview follow-ups, answer grading and the AI complexity check need a provider. Set
`LLM_PROVIDER` in `backend/.env`:

```bash
# Option A — Claude: best-quality follow-ups
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-...
ANTHROPIC_MODEL=claude-opus-5

# Option B — DeepSeek: roughly 30x cheaper, OpenAI-compatible API
LLM_PROVIDER=deepseek
DEEPSEEK_API_KEY=sk-...
DEEPSEEK_MODEL=deepseek-flash        # or deepseek-v4-pro
DEEPSEEK_BASE_URL=https://api.deepseek.com   # or an OpenAI-compatible relay
DEEPSEEK_THINKING=true               # thinking mode; reasoning tokens bill as output
DEEPSEEK_REASONING_EFFORT=high       # low | high | max
DEEPSEEK_COMPLEXITY_MODEL=deepseek-v4-flash   # optional: cheaper model for the complexity check
```

Each task can run on its own model: the complexity check is a small, mechanical judgement
and runs well on flash, while interview questions and answer grading stay on the default
model. On four real checks (including two deliberately wrong answers) flash matched pro's
verdicts at about a twentieth of the cost. Each stored verdict records which model made it.

**AI complexity check.** The built-in check compares your stated big-O with the textbook
solution, so an honest O(n²) analysis of a brute-force answer is marked wrong. With a
provider configured, every submission is also sent to the model, which judges your answer
against *the code you actually wrote* and says separately whether that code is optimal;
its verdict replaces the table's. When your code is not optimal in time or space, the
same call returns **your code minimally rewritten to reach the optimum**, shown as a diff so
only the optimisation stands out (e.g. a House Robber dp array becoming a two-slot rolling
array: three changed lines). The rewrite must parse as Python or it is not shown; past
verdicts, rewrite included, open from the History list. It runs after the attempt is saved, since a
thinking-mode reply can take up to a minute. At DeepSeek v4-pro peak rates that is
roughly $0.01 a problem with thinking on and $0.0015 with it off.

**AI mock interview.** After a timed mock, the model reads the code you wrote and asks three
follow-ups about it — the extra array your DP allocates, an edge case your code handles
oddly, a requirement change. You answer in writing; each answer is graded separately, so
you can move on while the previous one is being judged. The key points a question expects
are generated alongside it and stay hidden until you answer. They can be wrong, so the
grader is told to re-check the problem rather than deduct for disagreeing with them.

Replies are parsed defensively: one relay was observed echoing the requested schema back
before the real answer, so the prompt lists the expected keys instead of pasting a JSON
Schema, and the parser keeps the first object in the reply that actually validates.

Follow-ups are generated once per problem and cached in the database, so building the full
library for all 250 problems costs roughly **$0.20 on DeepSeek** or **$8 on Claude**, once.
Leave `LLM_PROVIDER=none` and everything still works with generic fallback questions.

## 📥 Where the problem data comes from

The library is extracted from a personal NeetCode markdown notes repository:

```bash
python3 scripts/extract_seed.py       # markdown -> data/seed.json
```

The extractor preserves existing approach notes and solutions, marks already-solved problems
as due immediately, and restores per-problem failure counts from the previous study plan —
so the very first daily queue already has meaningful priorities. Re-run it any time the notes
change.

## 🌐 Deployment

| Component | Platform | Config |
| --- | --- | --- |
| Frontend | Vercel | root `frontend/`, `vercel.json` handles SPA rewrites |
| Backend | Railway / Render | root `backend/`, `Procfile` included |
| Database | Railway Postgres / Supabase | set `DATABASE_URL`, `pip install "psycopg[binary]"` |

For a public deployment set `API_KEY` on the backend and `VITE_API_KEY` on the frontend;
the middleware then requires a matching `X-API-Key` header.

## ⌨️ Keyboard shortcuts

Press <kbd>?</kbd> anywhere for this list.

| Key | Action | Where |
| --- | --- | --- |
| <kbd>Space</kbd> | Start / stop the timer | Solve |
| <kbd>1</kbd>–<kbd>4</kbd> | Pick a grade, again → easy | Solve |
| <kbd>⌘</kbd><kbd>↵</kbd> | Submit — works from inside the editor | Solve, Drill |
| <kbd>C</kbd> | Check the blind-write | Drill |
| <kbd>J</kbd> / <kbd>K</kbd> | Move through the queue | Today |
| <kbd>G</kbd> | Jump to Today | Anywhere |

Shortcuts are suppressed while the caret is in an editor, so <kbd>Space</kbd> types a space
while you are writing code. <kbd>⌘</kbd><kbd>↵</kbd> is the exception, registered as a
Monaco command so it fires from inside the editor too.

## 🗺 Roadmap

- [ ] JWT accounts (currently single-user with optional API-key protection)
- [ ] Alembic migrations (currently an additive `migrate.py` plus `create_all` on startup)
- [ ] Daily email reminder (Vercel Cron + Resend)
- [ ] Reference complexities for the remaining 33 problems
- [ ] Spoken mock interviews — record the explanation, not just the code
