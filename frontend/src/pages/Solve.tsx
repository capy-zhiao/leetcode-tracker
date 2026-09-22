// Solve page: time it -> write code -> grade -> tag mistakes -> submit -> SRS schedules it
import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import GradeBar from '../components/GradeBar'
import MistakePicker from '../components/MistakePicker'
import Timer, { formatTime, useTimer } from '../components/Timer'
import { api } from '../lib/api'
import type { Attempt, CodeReview, Grade, ProblemDetail } from '../lib/types'

export default function Solve() {
  const { number } = useParams()           // pulls "994" out of /solve/994
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

  // Stopping the timer asks the backend which grade the performance deserves
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

  if (!p) return <p className="text-slate-400">Loading…</p>
  const prev = history[0]

  return (
    <div className="space-y-4">
      {/* problem header */}
      <div className="card">
        <div className="flex items-start gap-3">
          <div className="flex-1">
            <h1 className="text-lg font-semibold">{p.number}. {p.title}</h1>
            <p className="text-sm text-slate-500 mt-0.5">
              {p.difficulty} · {p.chapter}
              {p.state && <> · {p.state.total_attempts} attempts
                {p.state.lapses > 0 && <span className="text-orange-600"> · failed {p.state.lapses}x</span>}</>}
            </p>
          </div>
          {p.url && <a href={p.url} target="_blank" rel="noreferrer" className="btn">Open on NeetCode ↗</a>}
        </div>
        {p.notes && (
          <details className="mt-3">
            <summary className="text-sm text-slate-500 cursor-pointer">
              💡 My earlier notes (open only if you're stuck)
            </summary>
            <pre className="mt-2 text-sm bg-slate-50 rounded-lg p-3 whitespace-pre-wrap">{p.notes}</pre>
          </details>
        )}
      </div>

      {/* timer */}
      <div className="card flex items-center gap-4">
        <Timer running={timer.running} seconds={timer.seconds} onTick={timer.onTick} />
        <div className="flex gap-2">
          {!timer.running
            ? <button className="btn btn-primary" onClick={timer.start}>▶ Start</button>
            : <button className="btn" onClick={stopAndSuggest}>⏸ Stop &amp; grade</button>}
          <button className="btn" onClick={timer.reset}>Reset</button>
        </div>
        {p.state?.best_seconds && (
          <span className="text-xs text-slate-400 ml-auto">best {formatTime(p.state.best_seconds)}</span>
        )}
      </div>

      {/* code */}
      <div className="card">
        <div className="flex items-center mb-2">
          <h2 className="font-medium">Solution</h2>
          <button className="btn ml-auto text-xs" onClick={runAiReview} disabled={busy || !code.trim()}>
            🤖 AI Review
          </button>
        </div>
        <textarea
          value={code}
          onChange={(e) => setCode(e.target.value)}
          placeholder="Write your solution here…"
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
              📜 Last time ({new Date(prev.created_at).toLocaleDateString()}, {prev.grade})
            </summary>
            <pre className="mt-2 text-xs bg-slate-50 rounded-lg p-3 overflow-x-auto">{prev.code}</pre>
          </details>
        )}
      </div>

      {/* grading */}
      <div className="card space-y-3">
        <div className="flex items-center gap-4">
          <h2 className="font-medium">How did it go</h2>
          <label className="text-sm flex items-center gap-1.5">
            <input type="checkbox" checked={lookedAtSolution} onChange={(e) => setLooked(e.target.checked)} />
            looked at the solution
          </label>
          <label className="text-sm flex items-center gap-1.5">
            <input type="checkbox" checked={hadBugs} onChange={(e) => setHadBugs(e.target.checked)} />
            had bugs before it passed
          </label>
        </div>
        <GradeBar value={grade} onChange={setGrade} />
        {suggestion && <p className="text-xs text-slate-500">🕐 Suggested from your time: {suggestion}</p>}

        <div>
          <p className="text-sm font-medium mb-1.5">
            What went wrong?
            <span className="text-xs text-slate-400 ml-1">
              (enough of these become your personal pre-submit checklist)
            </span>
          </p>
          <MistakePicker selected={mistakes} onChange={setMistakes} />
        </div>

        <input
          value={note} onChange={(e) => setNote(e.target.value)}
          placeholder="One line: where you got stuck, or the key insight"
          className="w-full text-sm p-2 rounded-lg border border-slate-200"
        />

        {result ? (
          <div className="rounded-lg bg-emerald-50 border border-emerald-200 p-3 text-sm text-emerald-900">
            ✅ Recorded — this one comes back in <b>{result.days}</b> day{result.days === 1 ? '' : 's'}.
            <Link to="/" className="underline ml-2">Back to today</Link>
          </div>
        ) : (
          <button className="btn btn-primary w-full" onClick={submit} disabled={!grade || busy}>
            {busy ? 'Submitting…' : 'Submit and schedule the next review'}
          </button>
        )}
      </div>

      {history.length > 0 && (
        <div className="card">
          <h2 className="font-medium mb-2">History</h2>
          <div className="space-y-1 text-sm">
            {history.map((a) => (
              <div key={a.id} className="flex items-center gap-3 text-slate-600">
                <span className="text-xs text-slate-400 w-24">
                  {new Date(a.created_at).toLocaleDateString()}
                </span>
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
