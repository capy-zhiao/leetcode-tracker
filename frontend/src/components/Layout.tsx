// 所有页面共用的外壳:顶部导航 + 内容区。
// children 是 React 的特殊 prop —— 被这个组件包起来的东西。
import type { ReactNode } from 'react'
import { NavLink } from 'react-router-dom'

const links = [
  { to: '/', label: '今日' },
  { to: '/problems', label: '题库' },
  { to: '/mock', label: '模拟面试' },
  { to: '/stats', label: '统计' },
]

export default function Layout({ children }: { children: ReactNode }) {
  return (
    <div className="min-h-screen">
      <header className="bg-white border-b border-slate-200 sticky top-0 z-10">
        <nav className="max-w-4xl mx-auto px-4 h-14 flex items-center gap-1">
          <span className="font-semibold mr-4">🧠 刷题追踪器</span>
          {links.map((l) => (
            <NavLink
              key={l.to}
              to={l.to}
              // NavLink 会自动判断当前网址是不是它,isActive 就是结果
              className={({ isActive }) =>
                `px-3 py-1.5 rounded-lg text-sm transition ${
                  isActive ? 'bg-slate-900 text-white' : 'text-slate-600 hover:bg-slate-100'
                }`
              }
            >
              {l.label}
            </NavLink>
          ))}
        </nav>
      </header>
      <main className="max-w-4xl mx-auto px-4 py-6">{children}</main>
    </div>
  )
}
