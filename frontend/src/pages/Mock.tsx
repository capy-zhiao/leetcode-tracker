// Mock interview: random problem, countdown, and interviewer follow-ups from the LLM.
import { useState } from 'react'
import Timer, { useTimer } from '../components/Timer'
import { api } from '../lib/api'
import type { FollowUp, MockStart } from '../lib/types'

export default function Mock() {
  const [session, setSession] = useState<MockStart | null>(null)
  const [followups, setFollowups] = useState<FollowUp[]>([])
  const [phase, setPhase] = useState<'idle' | 'solving' | 'followup'>('idle')
  const [difficulty, setDifficulty] = useState('')
  const [onlySolved, setOnlySolved] = useState(false)
  const [answered, setAnswered] = useState<number[]>([])
  const [loading, setLoading] = useState(false)
  const timer = useTimer()

  const start = async () => {
    setLoading(true)
    try {
      const s = await api.mockStart({ difficulty: difficulty || undefined, only_solved: onlySolved })
      setSession(s); setFollowups([]); setAnswered([]); setPhase('solving')
      timer.reset(); timer.start()
    } catch (e) { alert((e as Error).message) } finally { setLoading(false) }
  }

  const toFollowup = async () => {
    timer.pause(); setPhase('followup'); setLoading(true)
    try { setFollowups(await api.followups(session!.problem.number)) }
    finally { setLoading(false) }
  }

  // A real interview doesn't show you your own notes, so this page deliberately hides them.
  if (phase === 'idle') {
    return (
      <div className="card space-y-4 max-w-lg">
        <div>
          <h1 className="text-lg font-semibold">🎤 Mock interview</h1>
          <p className="text-sm text-slate-500 mt-1">
            Random problem, a clock, and no notes. Follow-ups come after — that is where
            real interviews are won or lost.
          </p>
        </div>
        <div className="flex gap-2 items-center">
          <select value={difficulty} onChange={(e) => setDifficulty(e.target.value)} className="btn">
            <option value="">Any difficulty</option>
            <option>Easy</option><option>Medium</option><option>Hard</option>
          </select>
          <label className="text-sm flex items-center gap-1.5">
            <input type="checkbox" checked={onlySolved} onChange={(e) => setOnlySolved(e.target.checked)} />
            only problems I've solved (practise explaining)
          </label>
        </div>
        <button className="btn btn-primary w-full" onClick={start} disabled={loading}>
          {loading ? 'Drawing a problem…' : 'Start interview'}
        </button>
      </div>
    )
  }

  const p = session!.problem
  return (
    <div className="space-y-4">
      <div className="card flex items-center gap-4">
        <div className="flex-1">
          <h1 className="text-lg font-semibold">{p.number}. {p.title}</h1>
          <p className="text-sm text-slate-500">{p.difficulty} · {p.chapter}</p>
        </div>
        <Timer running={timer.running} seconds={timer.seconds}
               onTick={timer.onTick} limitMinutes={session!.minutes} />
      </div>

      {phase === 'solving' && (
        <div className="card space-y-3">
          <p className="text-sm text-slate-500">
            🔇 Interview mode: notes and past solutions are hidden. Talk through the approach
            first, then code, then state the complexity.
          </p>
          {p.url && <a href={p.url} target="_blank" rel="noreferrer" className="btn inline-block">
            Open the problem ↗
          </a>}
          <button className="btn btn-primary w-full" onClick={toFollowup}>
            Done coding — go to follow-ups →
          </button>
        </div>
      )}

      {phase === 'followup' && (
        <div className="card space-y-3">
          <h2 className="font-medium">
            Interviewer follow-ups {loading && <span className="text-sm text-slate-400">generating…</span>}
          </h2>
          {followups.map((f, i) => {
            const open = answered.includes(f.id)
            return (
              <div key={f.id} className="rounded-lg border border-slate-200 p-3">
                <p className="font-medium text-sm">Q{i + 1}. {f.question}</p>
                {open
                  ? <p className="mt-2 text-sm text-slate-600 bg-slate-50 rounded p-2">💡 {f.hint}</p>
                  : <button className="btn text-xs mt-2"
                            onClick={() => setAnswered([...answered, f.id])}>
                      I've answered — show the key points
                    </button>}
              </div>
            )
          })}
          <div className="flex gap-2">
            <a href={`/solve/${p.number}`} className="btn flex-1 text-center">Record this attempt</a>
            <button className="btn flex-1" onClick={() => { setPhase('idle'); setSession(null) }}>
              Another one
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
