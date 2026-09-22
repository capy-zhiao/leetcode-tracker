// 四个评分按钮。选中的那个高亮。
import type { Grade } from '../lib/types'

const GRADES: { id: Grade; label: string; sub: string; color: string }[] = [
  { id: 'again', label: '😵 不会',  sub: '看了答案',      color: 'bg-red-100 border-red-300 text-red-900' },
  { id: 'hard',  label: '😓 吃力',  sub: '卡壳或有 bug',  color: 'bg-amber-100 border-amber-300 text-amber-900' },
  { id: 'good',  label: '🙂 会了',  sub: '顺利做出',      color: 'bg-emerald-100 border-emerald-300 text-emerald-900' },
  { id: 'easy',  label: '😎 秒杀',  sub: '一遍过',        color: 'bg-sky-100 border-sky-300 text-sky-900' },
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
