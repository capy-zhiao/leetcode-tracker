// "What went wrong this time" multi-select. Tags come from the backend and are based on
// mistakes actually made while practising, not a generic list.
import { useEffect, useState } from 'react'
import { api } from '../lib/api'
import type { MistakeTag } from '../lib/types'

export default function MistakePicker({
  selected, onChange,
}: { selected: string[]; onChange: (ids: string[]) => void }) {
  const [tags, setTags] = useState<MistakeTag[]>([])

  // An empty dependency array means "run once, when this component first appears"
  useEffect(() => { api.mistakeTags().then(setTags).catch(() => {}) }, [])

  const toggle = (id: string) =>
    onChange(selected.includes(id) ? selected.filter((x) => x !== id) : [...selected, id])

  return (
    <div className="flex flex-wrap gap-1.5">
      {tags.map((t) => {
        const on = selected.includes(t.id)
        return (
          <button
            key={t.id}
            title={t.hint}
            onClick={() => toggle(t.id)}
            className={`chip border transition ${
              on ? 'bg-rose-100 border-rose-300 text-rose-900'
                 : 'bg-white border-slate-200 text-slate-500 hover:border-slate-400'
            }`}
          >
            {on && '✓ '}{t.label}
          </button>
        )
      })}
    </div>
  )
}
