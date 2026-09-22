// Shared shell for every page: top navigation plus the content area.
// Also owns the global shortcuts (? for help, G for today) so every page inherits them.
import { useState, type ReactNode } from 'react'
import { NavLink, useNavigate } from 'react-router-dom'
import ShortcutHelp from './ShortcutHelp'
import { useHotkeys } from '../lib/useHotkeys'

const links = [
  { to: '/', label: 'Today' },
  { to: '/drill', label: 'Drills' },
  { to: '/problems', label: 'Problems' },
  { to: '/patterns', label: 'Patterns' },
  { to: '/mock', label: 'Mock Interview' },
  { to: '/stats', label: 'Stats' },
]

export default function Layout({ children }: { children: ReactNode }) {
  const [helpOpen, setHelpOpen] = useState(false)
  const navigate = useNavigate()

  useHotkeys({
    '?': () => setHelpOpen(true),
    escape: () => setHelpOpen(false),
    g: () => navigate('/'),
  })

  return (
    <div className="min-h-screen">
      <header className="bg-white border-b border-slate-200 sticky top-0 z-10">
        <nav className="max-w-4xl mx-auto px-4 h-14 flex items-center gap-1">
          <span className="font-semibold mr-4">🧠 LeetCode Tracker</span>
          {links.map((l) => (
            <NavLink
              key={l.to}
              to={l.to}
              // `end` stops "/" from matching every route
              end={l.to === '/'}
              // NavLink works out whether its route is the current one and hands you isActive
              className={({ isActive }) =>
                `px-2.5 py-1.5 rounded-lg text-sm transition ${
                  isActive ? 'bg-slate-900 text-white' : 'text-slate-600 hover:bg-slate-100'
                }`
              }
            >
              {l.label}
            </NavLink>
          ))}
          <button
            onClick={() => setHelpOpen(true)}
            title="Keyboard shortcuts"
            className="ml-auto text-slate-400 hover:text-slate-700 text-sm px-2"
          >
            ⌘ <kbd className="border border-slate-200 rounded px-1 text-xs">?</kbd>
          </button>
        </nav>
      </header>
      <main className="max-w-4xl mx-auto px-4 py-6">{children}</main>
      {helpOpen && <ShortcutHelp onClose={() => setHelpOpen(false)} />}
    </div>
  )
}
