// Solve page: time it -> write code -> state the complexity -> grade -> submit ->
// SRS schedules the next review.
//
// Fully keyboard driven: Space toggles the timer, 1-4 pick a grade, Cmd+Enter submits from
// anywhere including inside the editor.
import { useEffect, useState } from 'react'
import { Link, useLocation, useParams } from 'react-router-dom'
import CodeEditor from '../components/CodeEditor'
import ComplexityPicker from '../components/ComplexityPicker'
import GradeBar from '../components/GradeBar'
import PatternChips from '../components/PatternChips'
import Timer, { formatTime, useTimer } from '../components/Timer'
import { api } from '../lib/api'
import { useHotkeys } from '../lib/useHotkeys'
import type {
  Attempt, ComplexityCheck, ComplexityVerdict, Grade, ProblemDetail,
} from '../lib/types'

const GRADE_ORDER: Grade[] = ['again', 'hard', 'good', 'easy']

export default function Solve() {
  const { number } = useParams()           // pulls "994" out of /solve/994
  const num = Number(number)
  // Mock interview hands over what you wrote under the clock, so nothing is retyped.
  const handoff = useLocation().state as
    { code?: string; timeComplexity?: string; spaceComplexity?: string } | null

  const [p, setP] = useState<ProblemDetail | null>(null)
  const [history, setHistory] = useState<Attempt[]>([])
  const timer = useTimer()

  const [code, setCode] = useState('')
  const [grade, setGrade] = useState<Grade | null>(null)
  const [suggestion, setSuggestion] = useState('')
  const [note, setNote] = useState('')
  const [lookedAtSolution, setLooked] = useState(false)
  const [hadBugs, setHadBugs] = useState(false)
  const [timeComplexity, setTimeComplexity] = useState('')
  const [spaceComplexity, setSpaceComplexity] = useState('')
  const [choices, setChoices] = useState<string[]>([])
  const [result, setResult] = useState<{ days: number } | null>(null)
  const [complexity, setComplexity] = useState<ComplexityCheck | null>(null)
  // The lookup-table verdict. With AI on it stays hidden — the AI judges the code actually
  // written, and showing the table first meant a red "expected O(1)" that the AI then
  // contradicted a minute later. It is only a fallback if the AI call fails.
  const [tableCheck, setTableCheck] = useState<ComplexityCheck | null>(null)
  // AI complexity check: runs after submitting, because thinking mode is slow
  const [aiEnabled, setAiEnabled] = useState(false)
  const [aiVerdict, setAiVerdict] = useState<ComplexityVerdict | null>(null)
  const [aiState, setAiState] = useState<'idle' | 'running' | 'failed'>('idle')
  const [aiError, setAiError] = useState('')
  const [attemptId, setAttemptId] = useState<number | null>(null)
  const [busy, setBusy] = useState(false)

  useEffect(() => {
    api.problem(num).then((d) => {
      setP(d)
      setCode(handoff?.code || d.code || '')
    })
    api.attempts(num).then(setHistory).catch(() => {})
    if (handoff?.timeComplexity) setTimeComplexity(handoff.timeComplexity)
    if (handoff?.spaceComplexity) setSpaceComplexity(handoff.spaceComplexity)
    // handoff is read once, on mount for this problem
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [num])

  useEffect(() => {
    api.complexityChoices().then(setChoices).catch(() => {})
    api.health().then((h) => setAiEnabled(h.llm_enabled)).catch(() => {})
  }, [])

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

  const ready = Boolean(grade && timeComplexity.trim() && spaceComplexity.trim())

  const submit = async () => {
    if (!ready || busy || result) return
    setBusy(true)
    try {
      const r = await api.submitAttempt(num, {
        grade: grade!, seconds: timer.seconds, looked_at_solution: lookedAtSolution,
        had_bugs: hadBugs, code, note, mode: 'practice',
        time_complexity: timeComplexity, space_complexity: spaceComplexity,
      })
      setResult({ days: r.next_due_in_days })
      const useAi = aiEnabled && Boolean(code.trim())
      setTableCheck(r.complexity)
      if (!useAi) setComplexity(r.complexity)        // no AI: the reference check is the verdict
      setAttemptId(r.attempt.id)
      if (useAi) runAiComplexity(r.attempt.id, r.complexity)   // not awaited
      setHistory(await api.attempts(num))
    } finally { setBusy(false) }
  }

  // Ask the AI to judge the stated complexity against the code actually written. Its
  // verdict replaces the lookup-table one, which only knows the textbook solution.
  const runAiComplexity = async (id: number, fallback: ComplexityCheck | null = tableCheck) => {
    setAiState('running')
    setAiError('')
    setComplexity(null)          // nothing judged on screen until the AI answers
    try {
      const a = await api.aiComplexity(id)
      const v = a.complexity_ai
      if (!v) throw new Error('No verdict returned')
      setAiVerdict(v)
      setComplexity({
        graded: true, time_ok: v.time_correct, space_ok: v.space_correct,
        expected_time: v.actual_time, expected_space: v.actual_space,
        accepted_time: [], accepted_space: [],
      })
      setAiState('idle')
      setHistory(await api.attempts(num))
    } catch (e) {
      setAiState('failed')
      setAiError((e as Error).message)
      setComplexity(fallback)    // fall back to the reference-answer check
    }
  }

  useHotkeys({
    space: () => (timer.running ? stopAndSuggest() : timer.start()),
    '1': () => setGrade(GRADE_ORDER[0]),
    '2': () => setGrade(GRADE_ORDER[1]),
    '3': () => setGrade(GRADE_ORDER[2]),
    '4': () => setGrade(GRADE_ORDER[3]),
    'mod+enter': () => submit(),
  })

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
            <PatternChips patterns={p.patterns} className="mt-2" linkTo />
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
        <kbd className="text-[10px] text-slate-400 border border-slate-200 rounded px-1">space</kbd>
        {p.state?.best_seconds && (
          <span className="text-xs text-slate-400 ml-auto">best {formatTime(p.state.best_seconds)}</span>
        )}
      </div>

      {/* code */}
      <div className="card">
        <h2 className="font-medium mb-2">Solution</h2>
        <CodeEditor
          value={code}
          onChange={setCode}
          onSubmit={submit}
          height={340}
          placeholder="Write your solution here…"
        />
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

        <ComplexityPicker
          time={timeComplexity} space={spaceComplexity}
          onTime={setTimeComplexity} onSpace={setSpaceComplexity}
          choices={choices} result={complexity} judgedBy={aiVerdict ? 'ai' : 'table'}
        />
        <AiComplexity
          state={aiState} verdict={aiVerdict} error={aiError}
          onRetry={attemptId !== null ? () => runAiComplexity(attemptId) : undefined}
        />

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
          <>
            <button className="btn btn-primary w-full" onClick={submit} disabled={!ready || busy}>
              {busy ? 'Submitting…' : 'Submit and schedule the next review'}
              <kbd className="ml-2 text-[10px] opacity-60">⌘↵</kbd>
            </button>
            {!ready && (
              <p className="text-xs text-slate-400 text-center">
                {!grade ? 'Pick a grade' : 'Fill in both complexities'} to submit
              </p>
            )}
          </>
        )}
      </div>

      {history.length > 0 && (
        <div className="card">
          <h2 className="font-medium mb-2">History</h2>
          <div className="space-y-1 text-sm">
            {history.map((a) => (
              <HistoryRow key={a.id} a={a} pending={aiState === 'running' && a.id === attemptId} />
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

/** One past attempt. Rows judged by the AI expand to show that verdict and its rewrite. */
function HistoryRow({ a, pending = false }: { a: Attempt; pending?: boolean }) {
  const [open, setOpen] = useState(false)
  const expandable = Boolean(a.complexity_ai)
  return (
    <div>
      <button
        type="button"
        onClick={() => expandable && setOpen(!open)}
        aria-expanded={expandable ? open : undefined}
        className={`w-full flex items-center gap-3 text-left text-slate-600 rounded px-1 ${
          expandable ? 'hover:bg-slate-50 cursor-pointer' : 'cursor-default'}`}
      >
        <span className="text-xs text-slate-400 w-24">
          {new Date(a.created_at).toLocaleDateString()}
        </span>
        <span className="w-12">{a.grade}</span>
        <span className="w-16 font-mono text-xs">{formatTime(a.seconds)}</span>
        {pending ? (
          <span className="text-xs text-slate-400" title="the AI is still checking this one">⏳ O</span>
        ) : a.complexity_ok !== null && (
          <span className="text-xs"
                title={a.complexity_ai ? 'complexity, judged by AI against this code'
                                       : 'complexity, checked against the reference'}>
            {a.complexity_ok ? '✅' : '❌'} O{a.complexity_ai && ' 🤖'}
          </span>
        )}
        <span className="flex-1 truncate text-xs">{a.note}</span>
        {expandable && <span className="text-xs text-slate-300">{open ? '▾' : '▸'}</span>}
      </button>
      {open && a.complexity_ai && (
        <div className="mt-1 mb-2 ml-1">
          <AiComplexity state="idle" verdict={a.complexity_ai} error="" />
        </div>
      )}
    </div>
  )
}

function AiComplexity({
  state, verdict, error, onRetry,
}: {
  state: 'idle' | 'running' | 'failed'
  verdict: ComplexityVerdict | null
  error: string
  onRetry?: () => void
}) {
  if (state === 'running') {
    return (
      <p className="text-sm text-indigo-700 bg-indigo-50 border border-indigo-200 rounded-lg p-3">
        🤖 Checking your complexity against the code you wrote… <Elapsed />
        <span className="text-indigo-500"> · usually 20s to 2 min, longer when it has to
        write a faster version of your code</span>
      </p>
    )
  }
  if (state === 'failed') {
    return (
      <div className="text-sm text-slate-600 bg-slate-50 border border-slate-200 rounded-lg p-3
                      flex items-center gap-3">
        <span className="flex-1">
          🤖 AI check failed: {error} — showing the check against the reference answer instead.
        </span>
        {onRetry && <button className="btn text-xs" onClick={onRetry}>Retry</button>}
      </div>
    )
  }
  if (!verdict) return null
  // is_optimal only speaks to time. Space is compared separately, because "can you do it
  // in O(1) space?" is the classic follow-up to an otherwise optimal DP array solution.
  const norm = (x: string) => x.replace(/\s/g, '').toLowerCase()
  const spaceImprovable = norm(verdict.actual_space) !== norm(verdict.optimal_space)
  return (
    <div className="text-sm bg-indigo-50 border border-indigo-200 rounded-lg p-3 space-y-1">
      <p className="text-indigo-950">
        🤖 Your code: <b className="font-mono">{verdict.actual_time}</b> time,{' '}
        <b className="font-mono">{verdict.actual_space}</b> space
        {verdict.is_optimal
          ? <span className="text-emerald-700"> · optimal time</span>
          : <span className="text-amber-700"> · time can be{' '}
              <span className="font-mono">{verdict.optimal_time}</span></span>}
        {spaceImprovable && (
          <span className="text-amber-700"> · space can be{' '}
            <span className="font-mono">{verdict.optimal_space}</span></span>
        )}
      </p>
      <p className="text-indigo-900/80">{verdict.explanation}</p>
      {verdict.optimized_diff && verdict.optimized_diff.length > 0 && verdict.optimized_code && (
        <OptimizedDiff diff={verdict.optimized_diff} code={verdict.optimized_code} />
      )}
      {verdict.model && <p className="text-[11px] text-indigo-900/50">judged by {verdict.model}</p>}
    </div>
  )
}

/** The model's rewrite of the submitted code, as a diff so only the optimisation shows. */
function OptimizedDiff({ diff, code }: { diff: string[]; code: string }) {
  const [copied, setCopied] = useState(false)
  const copy = async () => {
    try {
      await navigator.clipboard.writeText(code)
      setCopied(true)
      setTimeout(() => setCopied(false), 1500)
    } catch { /* clipboard blocked: the full code is still selectable below */ }
  }
  return (
    <div className="pt-1">
      <div className="flex items-center gap-2 mb-1">
        <p className="text-xs font-medium text-indigo-950">Optimized version — changes from your code</p>
        <button type="button" className="btn text-[11px] py-0.5 px-2 ml-auto" onClick={copy}>
          {copied ? 'Copied' : 'Copy full code'}
        </button>
      </div>
      {/* Diff lines keep their own colours; the header lines are dropped as noise */}
      <pre className="text-xs bg-white border border-indigo-100 rounded-lg p-3 overflow-x-auto leading-relaxed">
        {diff.filter((l) => !l.startsWith('---') && !l.startsWith('+++')).map((line, i) => (
          <div key={i} className={
            line.startsWith('+') ? 'bg-emerald-50 text-emerald-800'
            : line.startsWith('-') ? 'bg-rose-50 text-rose-800'
            : line.startsWith('@@') ? 'text-slate-400' : 'text-slate-700'
          }>{line || ' '}</div>
        ))}
      </pre>
      <details className="mt-1">
        <summary className="text-[11px] text-indigo-900/60 cursor-pointer">full optimized code</summary>
        <pre className="mt-1 text-xs bg-white border border-indigo-100 rounded-lg p-3 overflow-x-auto">{code}</pre>
      </details>
    </div>
  )
}

/** Seconds since mount, so a long AI wait visibly isn't frozen. */
function Elapsed() {
  const [start] = useState(() => Date.now())
  const [now, setNow] = useState(start)
  useEffect(() => {
    const id = setInterval(() => setNow(Date.now()), 1000)
    return () => clearInterval(id)
  }, [])
  return <b className="font-mono tabular-nums">{Math.floor((now - start) / 1000)}s</b>
}
