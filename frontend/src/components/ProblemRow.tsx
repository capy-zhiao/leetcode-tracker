import { Link } from 'react-router-dom'
import PatternChips from './PatternChips'
import type { QueueItem } from '../lib/types'

const DIFF_COLOR: Record<string, string> = {
  Easy: 'bg-emerald-100 text-emerald-700',
  Medium: 'bg-amber-100 text-amber-700',
  Hard: 'bg-rose-100 text-rose-700',
}

/** Templates open the blind-write drill; problems open the solve page. */
export function rowHref(number: number, kind: string) {
  return kind === 'template' ? `/drill/${number}` : `/solve/${number}`
}

export default function ProblemRow({
  item, selected = false,
}: { item: QueueItem; selected?: boolean }) {
  const p = item.problem
  return (
    <Link
      to={rowHref(p.number, p.kind)}
      className={`flex items-center gap-3 px-3 py-2.5 rounded-lg transition ${
        selected ? 'bg-slate-100 ring-1 ring-slate-300' : 'hover:bg-slate-50'
      }`}
    >
      <span className={`chip ${DIFF_COLOR[p.difficulty]}`}>{p.difficulty}</span>
      <span className="font-mono text-xs text-slate-400 w-12 text-right">
        {p.kind === 'template' ? '🔧' : p.number}
      </span>
      <span className="flex-1 font-medium truncate">{p.title}</span>

      <PatternChips patterns={p.patterns?.slice(0, 2) ?? []} />

      {item.overdue_days > 0 && (
        <span className="chip bg-red-50 text-red-600">{item.overdue_days}d overdue</span>
      )}
      {p.state && p.state.lapses > 0 && (
        <span className="chip bg-orange-50 text-orange-600" title="times failed before">
          ✗{p.state.lapses}
        </span>
      )}
      <span className="text-xs text-slate-400 w-24 truncate">{p.chapter}</span>
    </Link>
  )
}
