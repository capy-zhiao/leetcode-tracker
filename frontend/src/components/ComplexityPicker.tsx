// Time and space complexity, required before an attempt can be submitted.
//
// Interviewers ask for this on essentially every problem, but nothing in the practice loop
// used to force an answer, so it was the one habit that never got rehearsed. A <datalist>
// gives the common classes as suggestions while still accepting free text — restricting to
// a dropdown would make the odd problem unanswerable.
import type { ComplexityCheck } from '../lib/types'

interface Props {
  time: string
  space: string
  onTime: (v: string) => void
  onSpace: (v: string) => void
  choices: string[]
  result?: ComplexityCheck | null    // set after submitting
  /** 'ai' when the verdict came from analysing the submitted code itself */
  judgedBy?: 'table' | 'ai'
}

export default function ComplexityPicker({
  time, space, onTime, onSpace, choices, result, judgedBy = 'table',
}: Props) {
  return (
    <div>
      <p className="text-sm font-medium mb-1.5">
        Complexity
        <span className="text-xs text-slate-400 ml-1">
          (required — state it out loud like you would in the interview)
        </span>
      </p>

      <datalist id="complexity-choices">
        {choices.map((c) => <option key={c} value={c} />)}
      </datalist>

      <div className="grid grid-cols-2 gap-2">
        <Field label="Time"  value={time}  onChange={onTime}
               ok={result?.graded ? result.time_ok : undefined}
               expected={result?.expected_time} judgedBy={judgedBy} />
        <Field label="Space" value={space} onChange={onSpace}
               ok={result?.graded ? result.space_ok : undefined}
               expected={result?.expected_space} judgedBy={judgedBy} />
      </div>

      {result && !result.graded && (
        <p className="text-xs text-slate-400 mt-1.5">
          Recorded. No reference answer for this one yet, so it isn't scored.
        </p>
      )}
    </div>
  )
}

function Field({
  label, value, onChange, ok, expected, judgedBy,
}: {
  label: string; value: string; onChange: (v: string) => void
  ok?: boolean; expected?: string; judgedBy: 'table' | 'ai'
}) {
  // undefined = not graded yet, so the neutral border stays
  const border = ok === undefined ? 'border-slate-200'
    : ok ? 'border-emerald-400 bg-emerald-50' : 'border-red-400 bg-red-50'

  return (
    <label className="block">
      <span className="text-xs text-slate-500">{label}</span>
      <input
        list="complexity-choices"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={label === 'Time' ? 'O(n log n)' : 'O(1)'}
        className={`w-full mt-0.5 text-sm font-mono p-2 rounded-lg border ${border}`}
        spellCheck={false}
      />
      {/* With an AI verdict the card below states right/wrong and why; the field only
          carries the colour, so the same thing is not said twice. */}
      {judgedBy === 'table' && ok === false && expected && (
        <span className="text-xs text-red-600">expected {expected}</span>
      )}
      {judgedBy === 'table' && ok === true && <span className="text-xs text-emerald-600">correct</span>}
    </label>
  )
}
