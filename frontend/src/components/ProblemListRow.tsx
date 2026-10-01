// One problem in a library list: difficulty, number, title, and where it stands in review.
import { Link } from 'react-router-dom'
import type { Problem } from '../lib/types'

const DIFF_COLOR: Record<string, string> = {
  Easy: 'bg-emerald-100 text-emerald-700',
  Medium: 'bg-amber-100 text-amber-700',
  Hard: 'bg-rose-100 text-rose-700',
}

export default function ProblemListRow({ p, showChapter = false }: { p: Problem; showChapter?: boolean }) {
  const mastered = (p.state?.interval_days ?? 0) >= 21
  return (
    <Link to={`/solve/${p.number}`}
          className="flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-slate-50 text-sm">
      <span className={`chip ${DIFF_COLOR[p.difficulty]}`}>{p.difficulty[0]}</span>
      <span className="font-mono text-xs text-slate-400 w-12 text-right">{p.number}</span>
      <span className="flex-1 truncate">{p.title}</span>
      {showChapter && <span className="text-xs text-slate-400 truncate max-w-32">{p.chapter}</span>}
      {/* Only marks problems from LeetCode's Top Interview 150 that NeetCode 150 doesn't have */}
      {!p.in_neetcode150 && p.in_top150 && (
        <span className="chip bg-purple-50 text-purple-600" title="LeetCode Top Interview 150">Top 150</span>
      )}
      {p.state?.due
        ? <span className={`text-xs ${mastered ? 'text-emerald-600' : 'text-slate-400'}`}>
            {mastered ? 'mastered' : `${p.state.interval_days}d interval`}
            {p.state.lapses > 0 && ` · ✗${p.state.lapses}`}
          </span>
        : <span className="text-xs text-slate-300">not started</span>}
    </Link>
  )
}
