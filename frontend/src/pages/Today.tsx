// 首页:今天该做什么。这就是取代 REVIEW.md 手工表格的东西。
import { useEffect, useState } from 'react'
import ProblemRow from '../components/ProblemRow'
import { api } from '../lib/api'
import type { DailyQueue } from '../lib/types'

export default function Today() {
  // useState 的三种状态:数据 / 加载中 / 出错 —— 每个要联网的页面都是这个套路
  const [queue, setQueue] = useState<DailyQueue | null>(null)
  const [forecast, setForecast] = useState<{ date: string; count: number }[]>([])
  const [error, setError] = useState('')

  useEffect(() => {
    api.today().then(setQueue).catch((e) => setError(e.message))
    api.forecast(14).then(setForecast).catch(() => {})
  }, [])

  if (error) return <p className="card text-red-600">出错了:{error}<br/>
    <span className="text-slate-500 text-sm">后端跑起来了吗?<code>uvicorn app.main:app --reload</code></span></p>
  if (!queue) return <p className="text-slate-400">加载中…</p>

  const maxCount = Math.max(1, ...forecast.map((f) => f.count))

  return (
    <div className="space-y-5">
      <div className="flex items-baseline justify-between">
        <h1 className="text-xl font-semibold">{queue.date}</h1>
        <p className="text-sm text-slate-500">
          今日到期 <b>{queue.total_due}</b> 道
          {queue.deferred > 0 && <> · 已按优先级排序,<b>{queue.deferred}</b> 道顺延</>}
        </p>
      </div>

      <Section title="🔁 复习" hint="按「逾期天数 + 历史翻车 + 难度 + 章节」排序" items={queue.reviews} />
      <Section title="🆕 新题" hint="按 NeetCode roadmap 顺序推进" items={queue.new_problems} />
      <Section title="🔧 模板盲写" hint="开工前 5 分钟" items={queue.templates} />

      <div className="card">
        <h2 className="font-medium mb-3">📈 未来 14 天复习负载</h2>
        <div className="flex items-end gap-1 h-24">
          {forecast.map((f) => (
            <div key={f.date} className="flex-1 flex flex-col items-center gap-1" title={`${f.date}: ${f.count} 道`}>
              <div
                className="w-full rounded-t bg-slate-300"
                style={{ height: `${(f.count / maxCount) * 100}%` }}
              />
              <span className="text-[9px] text-slate-400">{f.date.slice(8)}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

function Section({ title, hint, items }: { title: string; hint: string; items: any[] }) {
  return (
    <section className="card">
      <div className="flex items-baseline gap-2 mb-2">
        <h2 className="font-medium">{title}</h2>
        <span className="text-xs text-slate-400">{hint}</span>
        <span className="ml-auto text-sm text-slate-400">{items.length}</span>
      </div>
      {items.length === 0
        ? <p className="text-sm text-slate-400 px-3 py-2">今天没有 🎉</p>
        : <div className="-mx-1">{items.map((i) => <ProblemRow key={i.problem.id} item={i} />)}</div>}
    </section>
  )
}
