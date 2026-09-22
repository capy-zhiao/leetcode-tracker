// Shared shell for every page: top navigation plus the content area.
// `children` is React's special prop — whatever this component wraps.
import type { ReactNode } from 'react'
import { NavLink } from 'react-router-dom'

const links = [
  { to: '/', label: 'Today' },
  { to: '/problems', label: 'Problems' },
  { to: '/mock', label: 'Mock Interview' },
  { to: '/stats', label: 'Stats' },
]

export default function Layout({ children }: { children: ReactNode }) {
  return (
    <div className="min-h-screen">
      <header className="bg-white border-b border-slate-200 sticky top-0 z-10">
        <nav className="max-w-4xl mx-auto px-4 h-14 flex items-center gap-1">
          <span className="font-semibold mr-4">🧠 LeetCode Tracker</span>
          {links.map((l) => (
            <NavLink
              key={l.to}
              to={l.to}
              // NavLink works out whether its route is the current one and hands you isActive
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
