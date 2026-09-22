// Stats dashboard. The mistake ranking is the part that grows into a personal checklist.
import { useEffect, useState } from 'react'
import { api } from '../lib/api'
import type { Stats as StatsT } from '../lib/types'

export default function Stats() {
  const [s, setS] = useState<StatsT | null>(null)
  useEffect(() => { api.stats().then(setS).catch(() => {}) }, [])
  if (!s) return <p className="text-slate-400">Loading…</p>

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <Metric label="Started" value={`${s.started} / ${s.total_problems}`} />
        <Metric label="Mastered" value={String(s.mastered)} hint="interval ≥ 21 days" />
        <Metric label="Streak" value={`${s.streak_days} day${s.streak_days === 1 ? '' : 's'}`} />
        <Metric label="Average time"
                value={s.avg_seconds ? `${Math.round(s.avg_seconds / 60)} min` : '—'} />
      </div>

      {s.top_mistakes.length > 0 && (
        <section className="card">
          <h2 className="font-medium">🔴 Your mistake ranking</h2>
          <p className="text-xs text-slate-400 mt-0.5 mb-3">
            This is your personal pre-submit checklist — far more accurate than a generic one
          </p>
          <div className="space-y-2">
            {s.top_mistakes.slice(0, 8).map((m, i) => (
              <div key={m.id} className="flex items-center gap-3">
                <span className="text-xs text-slate-400 w-4">{i + 1}</span>
                <span className="w-56 text-sm truncate" title={m.hint}>{m.label}</span>
                <div className="flex-1 h-4 bg-slate-100 rounded overflow-hidden">
                  <div className="h-full bg-rose-400" style={{ width: `${m.pct}%` }} />
                </div>
                <span className="text-xs text-slate-500 w-20 text-right">{m.count}x · {m.pct}%</span>
              </div>
            ))}
          </div>
        </section>
      )}

      <section className="card">
        <h2 className="font-medium mb-3">📚 Progress by chapter</h2>
        <div className="space-y-1.5">
          {s.by_chapter.map((c) => (
            <div key={c.chapter_num} className="flex items-center gap-3 text-sm">
              <span className="w-6 text-xs text-slate-400 text-right">{c.chapter_num}</span>
              <span className="w-40 truncate">{c.chapter}</span>
              <div className="flex-1 h-4 bg-slate-100 rounded overflow-hidden flex">
                <div className="h-full bg-emerald-400" style={{ width: `${(c.mastered / c.total) * 100}%` }}
                     title={`${c.mastered} mastered`} />
                <div className="h-full bg-sky-300"
                     style={{ width: `${((c.started - c.mastered) / c.total) * 100}%` }}
                     title={`${c.started - c.mastered} in review`} />
              </div>
              <span className="text-xs text-slate-500 w-14 text-right">{c.started}/{c.total}</span>
            </div>
          ))}
        </div>
        <p className="text-xs text-slate-400 mt-3">
          <span className="inline-block w-3 h-3 bg-emerald-400 rounded-sm align-middle" /> mastered
          <span className="inline-block w-3 h-3 bg-sky-300 rounded-sm align-middle ml-3" /> in review
        </p>
      </section>

      <p className="text-sm text-slate-400">
        {s.attempts_7d} attempts in the last 7 days · {s.attempts_total} all time ·
        {' '}{s.due_today} due today
      </p>
    </div>
  )
}

function Metric({ label, value, hint }: { label: string; value: string; hint?: string }) {
  return (
    <div className="card">
      <p className="text-xs text-slate-500">{label}</p>
      <p className="text-2xl font-semibold mt-1">{value}</p>
      {hint && <p className="text-[10px] text-slate-400">{hint}</p>}
    </div>
  )
}
