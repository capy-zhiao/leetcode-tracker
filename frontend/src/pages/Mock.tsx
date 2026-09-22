// 模拟面试:随机抽题 + 倒计时 + 面试官追问(Claude 生成)
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

  // 面试里不该看到自己的笔记和代码 —— 这页刻意不显示它们
  if (phase === 'idle') {
    return (
      <div className="card space-y-4 max-w-lg">
        <div>
          <h1 className="text-lg font-semibold">🎤 模拟面试</h1>
          <p className="text-sm text-slate-500 mt-1">
            随机抽题、限时、不显示笔记。做完进追问环节 —— 真实面试的分水岭就在追问。
          </p>
        </div>
        <div className="flex gap-2 items-center">
          <select value={difficulty} onChange={(e) => setDifficulty(e.target.value)} className="btn">
            <option value="">随机难度</option>
            <option>Easy</option><option>Medium</option><option>Hard</option>
          </select>
          <label className="text-sm flex items-center gap-1.5">
            <input type="checkbox" checked={onlySolved} onChange={(e) => setOnlySolved(e.target.checked)} />
            只抽做过的题(练讲解)
          </label>
        </div>
        <button className="btn btn-primary w-full" onClick={start} disabled={loading}>
          {loading ? '抽题中…' : '开始面试'}
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
            🔇 面试模式:笔记和历史代码已隐藏。先讲思路,再写代码,最后说复杂度。
          </p>
          {p.url && <a href={p.url} target="_blank" rel="noreferrer" className="btn inline-block">打开题目 ↗</a>}
          <button className="btn btn-primary w-full" onClick={toFollowup}>
            写完了,进入追问环节 →
          </button>
        </div>
      )}

      {phase === 'followup' && (
        <div className="card space-y-3">
          <h2 className="font-medium">面试官追问 {loading && <span className="text-sm text-slate-400">生成中…</span>}</h2>
          {followups.map((f, i) => {
            const open = answered.includes(f.id)
            return (
              <div key={f.id} className="rounded-lg border border-slate-200 p-3">
                <p className="font-medium text-sm">Q{i + 1}. {f.question}</p>
                {open
                  ? <p className="mt-2 text-sm text-slate-600 bg-slate-50 rounded p-2">💡 {f.hint}</p>
                  : <button className="btn text-xs mt-2"
                            onClick={() => setAnswered([...answered, f.id])}>
                      我答完了,看要点
                    </button>}
              </div>
            )
          })}
          <div className="flex gap-2">
            <a href={`/solve/${p.number}`} className="btn flex-1 text-center">去记录这次表现</a>
            <button className="btn flex-1" onClick={() => { setPhase('idle'); setSession(null) }}>
              再来一道
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
