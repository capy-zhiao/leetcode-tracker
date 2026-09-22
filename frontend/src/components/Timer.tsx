// 计时器。演示 React 两个核心 Hook:
//   useState  —— 组件的「记忆」,值一变界面自动重画
//   useEffect —— 处理「副作用」(定时器、网络请求这类不属于渲染的事)
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
  limitMinutes?: number          // 传了就是倒计时(模拟面试用)
}

export default function Timer({ running, seconds, onTick, limitMinutes }: Props) {
  // useRef 存一个「不触发重画」的值 —— 这里用来记住定时器 id
  const saved = useRef(onTick)
  saved.current = onTick

  useEffect(() => {
    if (!running) return
    const id = setInterval(() => saved.current(seconds + 1), 1000)
    // 返回的函数会在「组件消失」或「running 变化」时执行 —— 清理定时器,防内存泄漏
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
        <span className="text-xs text-slate-400">{over ? '已超时' : `/ ${limitMinutes} 分钟`}</span>
      )}
    </div>
  )
}

/** 把计时状态收进一个自定义 Hook，页面里用起来只要一行 */
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
