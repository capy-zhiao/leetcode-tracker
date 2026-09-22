// Lazy wrapper around the Monaco editor.
//
// Monaco is by far the heaviest dependency in the app. React.lazy + a dynamic import puts
// it in its own chunk that the browser only fetches when a page that actually contains an
// editor is opened, so the home screen stays light.
import { Suspense, lazy, type ComponentProps } from 'react'
import type CodeEditorImpl from './CodeEditorImpl'

const Impl = lazy(() => import('./CodeEditorImpl'))

type Props = ComponentProps<typeof CodeEditorImpl>

export default function CodeEditor(props: Props) {
  return (
    <Suspense
      fallback={
        <div
          className="rounded-lg border border-slate-200 bg-slate-50 flex items-center
                     justify-center text-sm text-slate-400"
          style={{ height: props.height ?? 320 }}
        >
          Loading editor…
        </div>
      }
    >
      <Impl {...props} />
    </Suspense>
  )
}
