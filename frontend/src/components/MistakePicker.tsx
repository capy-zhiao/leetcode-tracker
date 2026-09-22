// 「这次犯了什么错」多选器。标签来自后端,是照着真实 bug 史定的。
import { useEffect, useState } from 'react'
import { api } from '../lib/api'
import type { MistakeTag } from '../lib/types'

export default function MistakePicker({
  selected, onChange,
}: { selected: string[]; onChange: (ids: string[]) => void }) {
  const [tags, setTags] = useState<MistakeTag[]>([])

  // 空依赖数组 [] = 只在组件第一次出现时跑一次
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
