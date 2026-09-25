// Monaco (the editor behind VS Code) in place of a bare <textarea>.
//
// Loaded lazily through CodeEditor.tsx — Monaco is ~3 MB, and Today / Patterns / Stats
// never need it, so it must not sit in the entry chunk.
//
// The textarea was the single biggest daily friction point: Enter returned the caret to
// column 0, so every line of Python needed its indentation typed by hand, and Tab moved
// focus out of the field entirely. Monaco gives auto-indent, bracket matching and syntax
// highlighting, and lets us bind Cmd/Ctrl+Enter to submit from inside the editor — a
// document-level key handler never sees keys Monaco has swallowed.
import Editor, { type OnMount } from '@monaco-editor/react'
import { useRef } from 'react'
import '../lib/monaco-setup'
import { useTheme } from '../lib/theme'

interface Props {
  value: string
  onChange: (v: string) => void
  onSubmit?: () => void          // bound to Cmd/Ctrl+Enter inside the editor
  height?: number
  language?: string
  readOnly?: boolean
  /** Shown over an empty editor, since Monaco has no placeholder of its own. */
  placeholder?: string
}

export default function CodeEditor({
  value, onChange, onSubmit, height = 320,
  language = 'python', readOnly = false, placeholder,
}: Props) {
  // A ref, not state: changing it must not re-render (that would remount the editor).
  const submitRef = useRef(onSubmit)
  submitRef.current = onSubmit
  const theme = useTheme()

  const handleMount: OnMount = (editor, monaco) => {
    editor.addCommand(
      monaco.KeyMod.CtrlCmd | monaco.KeyCode.Enter,
      () => submitRef.current?.(),
    )
    if (!readOnly) editor.focus()
  }

  return (
    <div className="relative rounded-lg border border-slate-200 overflow-hidden">
      <Editor
        height={height}
        language={language}
        theme={theme === 'dark' ? 'vs-dark' : 'light'}
        value={value}
        onChange={(v) => onChange(v ?? '')}
        onMount={handleMount}
        loading={<div className="p-4 text-sm text-slate-400">Loading editor…</div>}
        options={{
          readOnly,
          fontSize: 13,
          fontFamily: 'ui-monospace, SFMono-Regular, Menlo, monospace',
          minimap: { enabled: false },
          scrollBeyondLastLine: false,
          lineNumbers: 'on',
          tabSize: 4,
          insertSpaces: true,
          automaticLayout: true,       // re-measure when the pane resizes
          renderWhitespace: 'selection',
          padding: { top: 10, bottom: 10 },
          scrollbar: { alwaysConsumeMouseWheel: false },
          overviewRulerLanes: 0,
          folding: false,
        }}
      />
      {placeholder && !value && (
        <div className="pointer-events-none absolute top-[10px] left-[60px] text-sm
                        text-slate-400 font-mono">
          {placeholder}
        </div>
      )}
    </div>
  )
}
