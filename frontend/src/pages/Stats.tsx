// 统计看板。最有价值的是「错误模式排行」—— 它会长成你的个人自查清单。
import { useEffect, useState } from 'react'
import { api } from '../lib/api'
import type { Stats as StatsT } from '../lib/types'

export default function Stats() {
  const [s, setS] = useState<StatsT | null>(null)
  useEffect(() => { api.stats().then(setS).catch(() => {}) }, [])
  if (!s) return <p className="text-slate-400">加载中…</p>

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <Metric label="已开始" value={`${s.started} / ${s.total_problems}`} />
        <Metric label="已掌握" value={String(s.mastered)} hint="间隔 ≥ 21 天" />
        <Metric label="连续打卡" value={`${s.streak_days} 天`} />
        <Metric label="平均用时" value={s.avg_seconds ? `${Math.round(s.avg_seconds / 60)} 分钟` : '—'} />
      </div>

      {s.top_mistakes.length > 0 && (
        <section className="card">
          <h2 className="font-medium">🔴 你的错误模式排行</h2>
          <p className="text-xs text-slate-400 mt-0.5 mb-3">
            这就是你的个人版「提交前自查清单」—— 比通用清单准得多
          </p>
          <div className="space-y-2">
            {s.top_mistakes.slice(0, 8).map((m, i) => (
              <div key={m.id} className="flex items-center gap-3">
                <span className="text-xs text-slate-400 w-4">{i + 1}</span>
                <span className="w-44 text-sm truncate" title={m.hint}>{m.label}</span>
                <div className="flex-1 h-4 bg-slate-100 rounded overflow-hidden">
                  <div className="h-full bg-rose-400" style={{ width: `${m.pct}%` }} />
                </div>
                <span className="text-xs text-slate-500 w-16 text-right">{m.count} 次 · {m.pct}%</span>
              </div>
            ))}
          </div>
        </section>
      )}

      <section className="card">
        <h2 className="font-medium mb-3">📚 各章进度</h2>
        <div className="space-y-1.5">
          {s.by_chapter.map((c) => (
            <div key={c.chapter_num} className="flex items-center gap-3 text-sm">
              <span className="w-6 text-xs text-slate-400 text-right">{c.chapter_num}</span>
              <span className="w-40 truncate">{c.chapter}</span>
              <div className="flex-1 h-4 bg-slate-100 rounded overflow-hidden flex">
                <div className="h-full bg-emerald-400" style={{ width: `${(c.mastered / c.total) * 100}%` }}
                     title={`已掌握 ${c.mastered}`} />
                <div className="h-full bg-sky-300"
                     style={{ width: `${((c.started - c.mastered) / c.total) * 100}%` }}
                     title={`复习中 ${c.started - c.mastered}`} />
              </div>
              <span className="text-xs text-slate-500 w-14 text-right">{c.started}/{c.total}</span>
            </div>
          ))}
        </div>
        <p className="text-xs text-slate-400 mt-3">
          <span className="inline-block w-3 h-3 bg-emerald-400 rounded-sm align-middle" /> 已掌握
          <span className="inline-block w-3 h-3 bg-sky-300 rounded-sm align-middle ml-3" /> 复习中
        </p>
      </section>

      <p className="text-sm text-slate-400">
        最近 7 天做了 {s.attempts_7d} 次 · 累计 {s.attempts_total} 次 · 今日到期 {s.due_today} 道
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
