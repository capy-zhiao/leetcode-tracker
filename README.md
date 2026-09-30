# LeetCode Tracker

[![CI](https://github.com/capy-zhiao/leetcode-tracker/actions/workflows/ci.yml/badge.svg)](https://github.com/capy-zhiao/leetcode-tracker/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/python-3.12%20%7C%203.13-blue)
![React](https://img.shields.io/badge/react-18-61dafb)

A study tracker for the NeetCode 250. It picks what to practice each day, schedules
reviews with spaced repetition, and checks your time and space complexity answers.

I built it because my markdown study plan stopped working past a hundred or so problems.
Keeping track of review dates by hand wasn't realistic.

## Features

- Daily queue: due reviews, new problems in NeetCode order, and one template drill
- Spaced repetition: the next review date depends on how the attempt went
- Complexity check: enter time and space before submitting. With an LLM set up, it judges
  your answer against the code you actually wrote and shows a faster version if there is one
- Template drills: write one of 15 algorithm templates from memory, checked against the
  lines people usually get wrong
- Mock interview: a random problem on a timer, then follow-up questions about your code,
  graded by an LLM
- Pattern view: progress by technique (sliding window, union-find, ...) instead of by chapter
- Dark mode and keyboard shortcuts

## Stack

Frontend: React, TypeScript, Vite, Tailwind, Monaco.
Backend: FastAPI, SQLAlchemy, SQLite or Postgres.
AI features are optional and work with DeepSeek (or any OpenAI-compatible API) or Claude.

## Running it

```bash
./start.sh
```

This installs dependencies, sets up the database, starts both servers and opens the browser.

Or run them separately:

```bash
# backend
cd backend
python3 -m venv .venv && ./.venv/bin/pip install -r requirements.txt
cp .env.example .env
./.venv/bin/python seed_db.py
./.venv/bin/uvicorn app.main:app --reload

# frontend
cd frontend
npm install
npm run dev
```

Tests: `cd backend && ./.venv/bin/pytest -q`

## AI setup

In `backend/.env`:

```bash
LLM_PROVIDER=deepseek
DEEPSEEK_API_KEY=sk-...
DEEPSEEK_BASE_URL=https://api.deepseek.com     # any OpenAI-compatible endpoint
DEEPSEEK_MODEL=deepseek-v4-pro                  # mock interviews
DEEPSEEK_COMPLEXITY_MODEL=deepseek-v4-flash     # complexity checks (cheaper)
```

For Claude, set `LLM_PROVIDER=anthropic` and `ANTHROPIC_API_KEY`.

With `LLM_PROVIDER=none` everything else still works, and complexity answers are checked
against a built-in answer table instead. When a provider is set, the Stats page shows how
much API credit is left.

## How scheduling works

After each attempt you pick a grade: again, hard, good or easy. The app suggests one from
how long you took, whether you had bugs, and whether you looked at the solution. The grade
sets the next review interval, similar to Anki's SM-2, with shorter intervals for hard
problems.

When more is due than you can do in a day, reviews are ranked by how overdue they are and
how often you've failed them before. A day gets at most two reviews from the same chapter,
so you don't end up with four graph problems in a row.

New problems cover the NeetCode 150 first, in NeetCode's order, then the rest of the 250.
Hard problems come last.

Most of this can be adjusted in `backend/.env` (see `.env.example`).

## Shortcuts

Space starts and stops the timer, 1 to 4 pick a grade, Cmd+Enter submits, J and K move
through the queue. Press `?` in the app for the full list.

## Data

The problem list comes from my NeetCode notes. `python3 scripts/extract_seed.py` turns
the markdown into `data/seed.json`.

## Deploying

Frontend on Vercel (`frontend/`), backend on Railway or Render (`backend/`, Procfile
included), Postgres through `DATABASE_URL`. If it's public, set `API_KEY` on the backend
and `VITE_API_KEY` on the frontend.
