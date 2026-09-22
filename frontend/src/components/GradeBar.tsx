// The four grade buttons. The selected one is highlighted.
import type { Grade } from '../lib/types'

const GRADES: { id: Grade; label: string; sub: string; color: string }[] = [
  { id: 'again', label: '😵 Again', sub: 'saw the solution',  color: 'bg-red-100 border-red-300 text-red-900' },
  { id: 'hard',  label: '😓 Hard',  sub: 'struggled / bugs',  color: 'bg-amber-100 border-amber-300 text-amber-900' },
  { id: 'good',  label: '🙂 Good',  sub: 'solved smoothly',   color: 'bg-emerald-100 border-emerald-300 text-emerald-900' },
  { id: 'easy',  label: '😎 Easy',  sub: 'first try, fast',   color: 'bg-sky-100 border-sky-300 text-sky-900' },
]

export default function GradeBar({
  value, onChange,
}: { value: Grade | null; onChange: (g: Grade) => void }) {
  return (
    <div className="grid grid-cols-4 gap-2">
      {GRADES.map((g) => (
        <button
          key={g.id}
          onClick={() => onChange(g.id)}
          className={`rounded-lg border-2 px-2 py-2 text-left transition ${
            value === g.id ? g.color + ' ring-2 ring-offset-1 ring-slate-400'
                           : 'bg-white border-slate-200 hover:border-slate-400'
          }`}
        >
          <div className="text-sm font-medium">{g.label}</div>
          <div className="text-[11px] text-slate-500">{g.sub}</div>
        </button>
      ))}
    </div>
  )
}
