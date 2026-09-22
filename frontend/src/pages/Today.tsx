// Home screen: what to work on today. This replaces the hand-maintained markdown plan.
import { useEffect, useState } from 'react'
import ProblemRow from '../components/ProblemRow'
import { api } from '../lib/api'
import type { DailyQueue, QueueItem } from '../lib/types'

export default function Today() {
  // data / loading / error — the standard trio for any page that fetches
  const [queue, setQueue] = useState<DailyQueue | null>(null)
  const [forecast, setForecast] = useState<{ date: string; count: number }[]>([])
  const [error, setError] = useState('')

  useEffect(() => {
    api.today().then(setQueue).catch((e) => setError(e.message))
    api.forecast(14).then(setForecast).catch(() => {})
  }, [])

  if (error) return (
    <p className="card text-red-600">
      {error}<br />
      <span className="text-slate-500 text-sm">
        Is the backend running? <code>uvicorn app.main:app --reload</code>
      </span>
    </p>
  )
  if (!queue) return <p className="text-slate-400">Loading…</p>

  const maxCount = Math.max(1, ...forecast.map((f) => f.count))

  return (
    <div className="space-y-5">
      <div className="flex items-baseline justify-between">
        <h1 className="text-xl font-semibold">{queue.date}</h1>
        <p className="text-sm text-slate-500">
          <b>{queue.total_due}</b> due today
          {queue.deferred > 0 && <> · ranked by priority, <b>{queue.deferred}</b> deferred</>}
        </p>
      </div>

      <Section title="🔁 Review" hint="ranked by overdue days, past failures, difficulty and chapter"
               items={queue.reviews} />
      <Section title="🆕 New" hint="next up in NeetCode roadmap order" items={queue.new_problems} />
      <Section title="🔧 Template drill" hint="five minutes before you start" items={queue.templates} />

      <div className="card">
        <h2 className="font-medium mb-3">📈 Review load, next 14 days</h2>
        <div className="flex items-end gap-1 h-24">
          {forecast.map((f) => (
            <div key={f.date} className="flex-1 flex flex-col items-center gap-1"
                 title={`${f.date}: ${f.count} due`}>
              <div className="w-full rounded-t bg-slate-300"
                   style={{ height: `${(f.count / maxCount) * 100}%` }} />
              <span className="text-[9px] text-slate-400">{f.date.slice(8)}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

function Section({ title, hint, items }: { title: string; hint: string; items: QueueItem[] }) {
  return (
    <section className="card">
      <div className="flex items-baseline gap-2 mb-2">
        <h2 className="font-medium">{title}</h2>
        <span className="text-xs text-slate-400">{hint}</span>
        <span className="ml-auto text-sm text-slate-400">{items.length}</span>
      </div>
      {items.length === 0
        ? <p className="text-sm text-slate-400 px-3 py-2">Nothing here today 🎉</p>
        : <div className="-mx-1">{items.map((i) => <ProblemRow key={i.problem.id} item={i} />)}</div>}
    </section>
  )
}
