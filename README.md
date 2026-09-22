# 🧠 LeetCode Tracker

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
| **Mock interview** | Random problem, countdown, notes hidden, then **interviewer follow-up questions** |
| **AI code review** | An LLM reviews your solution and infers which mistake tags it exhibits |

## 🏗 Architecture

```
React + TypeScript + Vite + Tailwind      SPA frontend
          | REST
FastAPI + SQLAlchemy 2.0 + Pydantic v2    backend (auto-generated OpenAPI docs)
          |
SQLite (dev) / PostgreSQL (prod)
          |
Claude or DeepSeek                        follow-up generation + code review (optional)
```

**Design decisions worth calling out:**

- **The scheduling algorithm is a set of pure functions** (`app/srs.py`) — no database access,
  no clock reads (`today` is a parameter). That is what makes it fully unit-testable: 17 cases
  cover first intervals, growth curves, lapse resets, ease clamping and priority ordering.
- **The LLM layer is provider-agnostic** (`app/llm.py`). Claude uses native structured outputs;
  DeepSeek goes through its OpenAI-compatible endpoint with JSON mode plus Pydantic validation.
  Adding a third provider means implementing one `complete()` method.
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

**3. New problems advance in roadmap order** and are interleaved with reviews.

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

Follow-up generation and code review need a provider. Set `LLM_PROVIDER` in `backend/.env`:

```bash
# Option A — Claude: best-quality follow-ups
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-...
ANTHROPIC_MODEL=claude-opus-5

# Option B — DeepSeek: roughly 30x cheaper, OpenAI-compatible API
LLM_PROVIDER=deepseek
DEEPSEEK_API_KEY=sk-...
DEEPSEEK_MODEL=deepseek-flash        # or deepseek-v4-pro
DEEPSEEK_BASE_URL=https://api.deepseek.com
```

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

## 🗺 Roadmap

- [ ] JWT accounts (currently single-user with optional API-key protection)
- [ ] Alembic migrations (currently `create_all` on startup)
- [ ] Daily email reminder (Vercel Cron + Resend)
- [ ] Monaco editor in place of the plain textarea
- [ ] Proficiency view grouped by pattern (sliding window, monotonic stack, union-find)
  rather than by chapter
