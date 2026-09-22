// Timer. Demonstrates React's two core hooks:
//   useState  — the component's memory; changing it re-renders the UI
//   useEffect — side effects (timers, network calls) that aren't part of rendering
import { useEffect, useRef, useState } from 'react'

export function formatTime(sec: number) {
  const m = Math.floor(sec / 60)
  const s = sec % 60
  return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`
}

interface Props {
  running: boolean
  seconds: number
  onTick: (s: number) => void
  limitMinutes?: number          // when set, counts down instead of up (mock interview)
}

export default function Timer({ running, seconds, onTick, limitMinutes }: Props) {
  // useRef holds a value that does NOT trigger a re-render when it changes
  const saved = useRef(onTick)
  saved.current = onTick

  useEffect(() => {
    if (!running) return
    const id = setInterval(() => saved.current(seconds + 1), 1000)
    // The returned function runs when the component unmounts or `running` changes —
    // clearing the interval here is what prevents a leak.
    return () => clearInterval(id)
  }, [running, seconds])

  const limit = limitMinutes ? limitMinutes * 60 : null
  const over = limit !== null && seconds > limit
  const display = limit !== null ? Math.abs(limit - seconds) : seconds

  return (
    <div className="flex items-baseline gap-2">
      <span className={`font-mono text-3xl tabular-nums ${over ? 'text-red-600' : ''}`}>
        {over && '-'}{formatTime(display)}
      </span>
      {limit !== null && (
        <span className="text-xs text-slate-400">{over ? 'over time' : `/ ${limitMinutes} min`}</span>
      )}
    </div>
  )
}

/** Bundles the timer state into a custom hook so pages need a single line to use it. */
export function useTimer() {
  const [seconds, setSeconds] = useState(0)
  const [running, setRunning] = useState(false)
  return {
    seconds, running, setSeconds,
    start: () => setRunning(true),
    pause: () => setRunning(false),
    reset: () => { setRunning(false); setSeconds(0) },
    onTick: setSeconds,
  }
}
