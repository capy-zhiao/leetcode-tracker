// 做题页:计时 -> 写代码 -> 评分 -> 标错误 -> 提交 -> SRS 算出下次复习时间
import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import GradeBar from '../components/GradeBar'
import MistakePicker from '../components/MistakePicker'
import Timer, { formatTime, useTimer } from '../components/Timer'
import { api } from '../lib/api'
import type { Attempt, CodeReview, Grade, ProblemDetail } from '../lib/types'

export default function Solve() {
  const { number } = useParams()           // 从网址 /solve/994 里拿到 "994"
  const num = Number(number)

  const [p, setP] = useState<ProblemDetail | null>(null)
  const [history, setHistory] = useState<Attempt[]>([])
  const timer = useTimer()

  const [code, setCode] = useState('')
  const [grade, setGrade] = useState<Grade | null>(null)
  const [suggestion, setSuggestion] = useState('')
  const [mistakes, setMistakes] = useState<string[]>([])
  const [note, setNote] = useState('')
  const [lookedAtSolution, setLooked] = useState(false)
  const [hadBugs, setHadBugs] = useState(false)
  const [result, setResult] = useState<{ days: number } | null>(null)
  const [aiReview, setAiReview] = useState<CodeReview | null>(null)
  const [busy, setBusy] = useState(false)

  useEffect(() => {
    api.problem(num).then((d) => { setP(d); setCode(d.code || '') })
    api.attempts(num).then(setHistory).catch(() => {})
  }, [num])

  // 停止计时后,问后端「这个成绩该打几分」,自动选中推荐项
  const stopAndSuggest = async () => {
    timer.pause()
    if (!p) return
    const s = await api.suggestGrade({
      seconds: timer.seconds, looked_at_solution: lookedAtSolution,
      had_bugs: hadBugs, difficulty: p.difficulty,
    })
    setGrade(s.grade as Grade)
    setSuggestion(s.reason)
  }

  const submit = async () => {
    if (!grade) return
    setBusy(true)
    try {
      const r = await api.submitAttempt(num, {
        grade, seconds: timer.seconds, looked_at_solution: lookedAtSolution,
        had_bugs: hadBugs, mistakes, code, note, mode: 'practice',
      })
      setResult({ days: r.next_due_in_days })
      setHistory(await api.attempts(num))
    } finally { setBusy(false) }
  }

  const runAiReview = async () => {
    setBusy(true)
    try {
      const r = await api.reviewCode(num, code)
      setAiReview(r)
      setMistakes([...new Set([...mistakes, ...r.suggested_mistakes])])
    } catch (e) { alert((e as Error).message) } finally { setBusy(false) }
  }

  if (!p) return <p className="text-slate-400">加载中…</p>
  const prev = history[0]

  return (
    <div className="space-y-4">
      {/* 题目头 */}
      <div className="card">
        <div className="flex items-start gap-3">
          <div className="flex-1">
            <h1 className="text-lg font-semibold">{p.number}. {p.title}</h1>
            <p className="text-sm text-slate-500 mt-0.5">
              {p.difficulty} · {p.chapter}
              {p.state && <> · 复习过 {p.state.total_attempts} 次
                {p.state.lapses > 0 && <span className="text-orange-600"> · 翻车 {p.state.lapses} 次</span>}</>}
            </p>
          </div>
          {p.url && <a href={p.url} target="_blank" rel="noreferrer" className="btn">去 NeetCode ↗</a>}
        </div>
        {p.notes && (
          <details className="mt-3">
            <summary className="text-sm text-slate-500 cursor-pointer">💡 我之前的思路(想不出来再点开)</summary>
            <pre className="mt-2 text-sm bg-slate-50 rounded-lg p-3 whitespace-pre-wrap">{p.notes}</pre>
          </details>
        )}
      </div>

      {/* 计时器 */}
      <div className="card flex items-center gap-4">
        <Timer running={timer.running} seconds={timer.seconds} onTick={timer.onTick} />
        <div className="flex gap-2">
          {!timer.running
            ? <button className="btn btn-primary" onClick={timer.start}>▶ 开始</button>
            : <button className="btn" onClick={stopAndSuggest}>⏸ 停止并评分</button>}
          <button className="btn" onClick={timer.reset}>重置</button>
        </div>
        {p.state?.best_seconds && (
          <span className="text-xs text-slate-400 ml-auto">最快纪录 {formatTime(p.state.best_seconds)}</span>
        )}
      </div>

      {/* 代码 */}
      <div className="card">
        <div className="flex items-center mb-2">
          <h2 className="font-medium">代码</h2>
          <button className="btn ml-auto text-xs" onClick={runAiReview} disabled={busy || !code.trim()}>
            🤖 AI Review
          </button>
        </div>
        <textarea
          value={code}
          onChange={(e) => setCode(e.target.value)}
          placeholder="在这里写你的解法…"
          className="w-full h-64 font-mono text-sm p-3 rounded-lg border border-slate-200
                     focus:outline-none focus:ring-2 focus:ring-slate-300"
          spellCheck={false}
        />
        {aiReview && (
          <div className="mt-3 rounded-lg bg-indigo-50 border border-indigo-200 p-3 text-sm">
            <p className="font-medium text-indigo-900">{aiReview.summary}</p>
            {aiReview.issues.length > 0 && (
              <ul className="mt-2 list-disc list-inside text-indigo-800 space-y-0.5">
                {aiReview.issues.map((i, k) => <li key={k}>{i}</li>)}
              </ul>
            )}
          </div>
        )}
        {prev?.code && prev.code !== code && (
          <details className="mt-3">
            <summary className="text-sm text-slate-500 cursor-pointer">
              📜 上次的写法({new Date(prev.created_at).toLocaleDateString()},{prev.grade})
            </summary>
            <pre className="mt-2 text-xs bg-slate-50 rounded-lg p-3 overflow-x-auto">{prev.code}</pre>
          </details>
        )}
      </div>

      {/* 评分 */}
      <div className="card space-y-3">
        <div className="flex items-center gap-4">
          <h2 className="font-medium">这次表现</h2>
          <label className="text-sm flex items-center gap-1.5">
            <input type="checkbox" checked={lookedAtSolution} onChange={(e) => setLooked(e.target.checked)} />
            看了答案
          </label>
          <label className="text-sm flex items-center gap-1.5">
            <input type="checkbox" checked={hadBugs} onChange={(e) => setHadBugs(e.target.checked)} />
            提交前有 bug
          </label>
        </div>
        <GradeBar value={grade} onChange={setGrade} />
        {suggestion && <p className="text-xs text-slate-500">🕐 根据用时推荐:{suggestion}</p>}

        <div>
          <p className="text-sm font-medium mb-1.5">犯了什么错?<span className="text-xs text-slate-400 ml-1">(攒够数据会生成你的个人自查清单)</span></p>
          <MistakePicker selected={mistakes} onChange={setMistakes} />
        </div>

        <input
          value={note} onChange={(e) => setNote(e.target.value)}
          placeholder="一句话:为什么卡住 / 关键是什么"
          className="w-full text-sm p-2 rounded-lg border border-slate-200"
        />

        {result ? (
          <div className="rounded-lg bg-emerald-50 border border-emerald-200 p-3 text-sm text-emerald-900">
            ✅ 已记录 —— <b>{result.days}</b> 天后再复习这道题。
            <Link to="/" className="underline ml-2">回今日队列</Link>
          </div>
        ) : (
          <button className="btn btn-primary w-full" onClick={submit} disabled={!grade || busy}>
            {busy ? '提交中…' : '提交并安排下次复习'}
          </button>
        )}
      </div>

      {history.length > 0 && (
        <div className="card">
          <h2 className="font-medium mb-2">历史记录</h2>
          <div className="space-y-1 text-sm">
            {history.map((a) => (
              <div key={a.id} className="flex items-center gap-3 text-slate-600">
                <span className="text-xs text-slate-400 w-24">{new Date(a.created_at).toLocaleDateString()}</span>
                <span className="w-12">{a.grade}</span>
                <span className="w-16 font-mono text-xs">{formatTime(a.seconds)}</span>
                <span className="flex-1 truncate text-xs">{a.note}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
