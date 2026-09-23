// Home screen: what to work on today. This replaces the hand-maintained markdown plan.
// J / K walk the queue, Enter opens the highlighted item — no mouse needed.
import { useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import LoadChart, { type ForecastRow } from '../components/LoadChart'
import ProblemRow, { rowHref } from '../components/ProblemRow'
import { api } from '../lib/api'
import { useHotkeys } from '../lib/useHotkeys'
import type { DailyQueue, QueueItem } from '../lib/types'

export default function Today() {
  // data / loading / error — the standard trio for any page that fetches
  const [queue, setQueue] = useState<DailyQueue | null>(null)
  const [forecast, setForecast] = useState<ForecastRow[]>([])
  const [error, setError] = useState('')
  const [cursor, setCursor] = useState(-1)      // -1 = nothing highlighted yet
  const navigate = useNavigate()

  useEffect(() => {
    api.today().then(setQueue).catch((e) => setError(e.message))
    api.forecast(14).then(setForecast).catch(() => {})
  }, [])

  // One flat list across all three sections, so J/K walk the whole day in order.
  // useMemo keeps the array identity stable between renders.
  const flat = useMemo<QueueItem[]>(
    () => (queue ? [...queue.reviews, ...queue.new_problems, ...queue.templates] : []),
    [queue],
  )

  const move = (delta: number) => {
    if (!flat.length) return
    setCursor((c) => {
      const next = Math.min(flat.length - 1, Math.max(0, c + delta))
      document.getElementById(`row-${flat[next].problem.number}`)
        ?.scrollIntoView({ block: 'nearest' })
      return next
    })
  }

  useHotkeys({
    j: () => move(1),
    k: () => move(-1),
    arrowdown: () => move(1),
    arrowup: () => move(-1),
    enter: () => {
      const item = flat[cursor]
      if (item) navigate(rowHref(item.problem.number, item.problem.kind))
    },
  })

  if (error) return (
    <p className="card text-red-600">
      {error}<br />
      <span className="text-slate-500 text-sm">
        Is the backend running? <code>uvicorn app.main:app --reload</code>
      </span>
    </p>
  )
  if (!queue) return <p className="text-slate-400">Loading…</p>

  const selected = flat[cursor]?.problem.number

  return (
    <div className="space-y-5">
      <div className="flex items-baseline justify-between">
        <h1 className="text-xl font-semibold">{queue.date}</h1>
        <p className="text-sm text-slate-500">
          <b>{queue.total_due}</b> due today
          {queue.deferred > 0 && <> · ranked by priority, <b>{queue.deferred}</b> deferred</>}
          <span className="ml-2 text-xs text-slate-400">
            <kbd className="border border-slate-200 rounded px-1">J</kbd>
            <kbd className="border border-slate-200 rounded px-1 ml-0.5">K</kbd> to navigate
          </span>
        </p>
      </div>

      <Section title="🔁 Review" hint="ranked by priority · at most 2 per chapter or pattern, so the day stays mixed"
               items={queue.reviews} selected={selected} />
      <Section title="🆕 New" hint="roadmap order · one per chapter · Hards held back"
               items={queue.new_problems} selected={selected} />
      <Section title="🔧 Template drill" hint="five minutes of blind writing before you start"
               items={queue.templates} selected={selected} />

      <LoadChart rows={forecast} reviewCap={queue.review_cap} />
    </div>
  )
}

function Section({
  title, hint, items, selected,
}: { title: string; hint: string; items: QueueItem[]; selected?: number }) {
  return (
    <section className="card">
      <div className="flex items-baseline gap-2 mb-2">
        <h2 className="font-medium">{title}</h2>
        <span className="text-xs text-slate-400">{hint}</span>
        <span className="ml-auto text-sm text-slate-400">{items.length}</span>
      </div>
      {items.length === 0
        ? <p className="text-sm text-slate-400 px-3 py-2">Nothing here today 🎉</p>
        : (
          <div className="-mx-1">
            {items.map((i) => (
              <div key={i.problem.id} id={`row-${i.problem.number}`}>
                <ProblemRow item={i} selected={i.problem.number === selected} />
              </div>
            ))}
          </div>
        )}
    </section>
  )
}
