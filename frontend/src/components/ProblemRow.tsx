import { Link } from 'react-router-dom'
import type { QueueItem } from '../lib/types'

const DIFF_COLOR: Record<string, string> = {
  Easy: 'bg-emerald-100 text-emerald-700',
  Medium: 'bg-amber-100 text-amber-700',
  Hard: 'bg-rose-100 text-rose-700',
}

export default function ProblemRow({ item }: { item: QueueItem }) {
  const p = item.problem
  return (
    <Link
      to={`/solve/${p.number}`}
      className="flex items-center gap-3 px-3 py-2.5 rounded-lg hover:bg-slate-50 transition"
    >
      <span className={`chip ${DIFF_COLOR[p.difficulty]}`}>{p.difficulty}</span>
      <span className="font-mono text-xs text-slate-400 w-12 text-right">{p.number}</span>
      <span className="flex-1 font-medium">{p.title}</span>

      {item.overdue_days > 0 && (
        <span className="chip bg-red-50 text-red-600">逾期 {item.overdue_days} 天</span>
      )}
      {p.state && p.state.lapses > 0 && (
        <span className="chip bg-orange-50 text-orange-600" title="历史翻车次数">
          ✗{p.state.lapses}
        </span>
      )}
      <span className="text-xs text-slate-400 w-28 truncate">{p.chapter}</span>
    </Link>
  )
}
