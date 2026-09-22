// Problem library: filter by chapter, difficulty and status; search by title or number.
import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../lib/api'
import type { Problem } from '../lib/types'

const DIFF_COLOR: Record<string, string> = {
  Easy: 'bg-emerald-100 text-emerald-700',
  Medium: 'bg-amber-100 text-amber-700',
  Hard: 'bg-rose-100 text-rose-700',
}

export default function Problems() {
  const [items, setItems] = useState<Problem[]>([])
  const [q, setQ] = useState('')
  const [difficulty, setDifficulty] = useState('')
  const [status, setStatus] = useState('')
  const [kind, setKind] = useState('problem')

  // Anything in the dependency array re-triggers the fetch, so filters refresh automatically
  useEffect(() => {
    api.problems({ q, difficulty, status, kind }).then(setItems).catch(() => {})
  }, [q, difficulty, status, kind])

  const groups = items.reduce<Record<string, Problem[]>>((acc, p) => {
    const key = `${p.chapter_num}. ${p.chapter}`
    ;(acc[key] ??= []).push(p)
    return acc
  }, {})

  return (
    <div className="space-y-4">
      <div className="card flex flex-wrap gap-2 items-center">
        <input
          value={q} onChange={(e) => setQ(e.target.value)}
          placeholder="Search by number or title…"
          className="flex-1 min-w-48 text-sm p-2 rounded-lg border border-slate-200"
        />
        <select value={difficulty} onChange={(e) => setDifficulty(e.target.value)} className="btn">
          <option value="">All difficulties</option>
          <option>Easy</option><option>Medium</option><option>Hard</option>
        </select>
        <select value={status} onChange={(e) => setStatus(e.target.value)} className="btn">
          <option value="">All statuses</option>
          <option value="new">Not started</option>
          <option value="learning">In review</option>
          <option value="mastered">Mastered</option>
        </select>
        <select value={kind} onChange={(e) => setKind(e.target.value)} className="btn">
          <option value="problem">Problems</option>
          <option value="template">Templates</option>
        </select>
      </div>

      <p className="text-sm text-slate-500">{items.length} total</p>

      {Object.entries(groups).map(([chapter, list]) => (
        <section key={chapter} className="card">
          <h2 className="font-medium mb-2">
            {chapter} <span className="text-sm text-slate-400">({list.length})</span>
          </h2>
          <div className="-mx-1">
            {list.map((p) => (
              <Link key={p.id} to={`/solve/${p.number}`}
                    className="flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-slate-50 text-sm">
                <span className={`chip ${DIFF_COLOR[p.difficulty]}`}>{p.difficulty[0]}</span>
                <span className="font-mono text-xs text-slate-400 w-12 text-right">{p.number}</span>
                <span className="flex-1">{p.title}</span>
                {!p.in_neetcode150 && <span className="chip bg-purple-50 text-purple-600">250</span>}
                {p.state?.due
                  ? <span className="text-xs text-slate-400">
                      {p.state.interval_days}d interval{p.state.lapses > 0 && ` · ✗${p.state.lapses}`}
                    </span>
                  : <span className="text-xs text-slate-300">not started</span>}
              </Link>
            ))}
          </div>
        </section>
      ))}
    </div>
  )
}
