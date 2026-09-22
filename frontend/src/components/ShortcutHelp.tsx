// The "?" overlay. Lives in Layout so every page has it.
import { SHORTCUTS } from '../lib/useHotkeys'

export default function ShortcutHelp({ onClose }: { onClose: () => void }) {
  return (
    <div
      className="fixed inset-0 z-50 bg-slate-900/40 flex items-center justify-center p-4"
      onClick={onClose}
    >
      <div
        className="bg-white rounded-xl shadow-xl max-w-md w-full p-5"
        // Stop a click inside the panel from reaching the backdrop and closing it
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-baseline mb-3">
          <h2 className="font-semibold">Keyboard shortcuts</h2>
          <span className="ml-auto text-xs text-slate-400">Esc to close</span>
        </div>
        <table className="w-full text-sm">
          <tbody>
            {SHORTCUTS.map((s) => (
              <tr key={s.keys} className="border-t border-slate-100">
                <td className="py-1.5 w-20">
                  <kbd className="px-1.5 py-0.5 rounded border border-slate-300
                                  bg-slate-50 font-mono text-xs">{s.keys}</kbd>
                </td>
                <td className="py-1.5 text-slate-700">{s.label}</td>
                <td className="py-1.5 text-right text-xs text-slate-400">{s.where}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
