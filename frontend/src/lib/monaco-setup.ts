// Point @monaco-editor/react at a bundled, trimmed-down Monaco instead of its default CDN.
//
// Two reasons not to `import * as monaco from 'monaco-editor'`:
//   1. the default loader fetches Monaco from a CDN, so the editor dies offline
//   2. the root entry registers ~80 languages plus the TypeScript/CSS/HTML language
//      servers — a 4.2 MB bundle to write Python in
//
// So we import the API, the Python tokenizer, and only the editor contributions that a
// person actually uses while writing a solution. Anything not listed here is genuinely
// absent (no code folding, no rename, no inline completions), which is fine for this app.
//
// Specifiers go through monaco-editor's "exports" map ("./*.js" -> "./esm/vs/*.js"), so
// they read "monaco-editor/editor/..." rather than the "esm/vs/..." path on disk.
import { loader } from '@monaco-editor/react'
import * as monaco from 'monaco-editor/editor/editor.api.js'
import editorWorker from 'monaco-editor/editor/editor.worker.js?worker'

// Syntax highlighting for the only language this app cares about
import 'monaco-editor/languages/definitions/python/register.js'

// Editing essentials
import 'monaco-editor/editor/browser/coreCommands.js'
import 'monaco-editor/editor/contrib/bracketMatching/browser/bracketMatching.js'
import 'monaco-editor/editor/contrib/clipboard/browser/clipboard.js'
import 'monaco-editor/editor/contrib/comment/browser/comment.js'              // Cmd+/
import 'monaco-editor/editor/contrib/contextmenu/browser/contextmenu.js'
import 'monaco-editor/editor/contrib/cursorUndo/browser/cursorUndo.js'
import 'monaco-editor/editor/contrib/find/browser/findController.js'          // Cmd+F
import 'monaco-editor/editor/contrib/indentation/browser/indentation.js'
import 'monaco-editor/editor/contrib/lineSelection/browser/lineSelection.js'
import 'monaco-editor/editor/contrib/linesOperations/browser/linesOperations.js'
import 'monaco-editor/editor/contrib/multicursor/browser/multicursor.js'
import 'monaco-editor/editor/contrib/smartSelect/browser/smartSelect.js'
import 'monaco-editor/editor/contrib/suggest/browser/suggestController.js'
import 'monaco-editor/editor/contrib/wordOperations/browser/wordOperations.js'
import 'monaco-editor/editor/contrib/wordPartOperations/browser/wordPartOperations.js'

// Monaco does its heavy lifting in a web worker. Python needs only the base editor worker —
// there is no language service to load, unlike TypeScript.
;(self as unknown as { MonacoEnvironment: unknown }).MonacoEnvironment = {
  getWorker: () => new editorWorker(),
}

loader.config({ monaco })

export default monaco
