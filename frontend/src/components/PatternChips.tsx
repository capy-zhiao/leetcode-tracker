// Pattern tags on a problem.
//
// `linkTo` is off by default because these chips are often rendered inside a row that is
// itself a <Link>, and an <a> nested in an <a> is invalid HTML — React warns and the
// browser hoists the inner anchor out of the outer one, breaking the row.
import { Link } from 'react-router-dom'

interface Props {
  patterns: string[]
  className?: string
  /** Only pass this where the chips are NOT already inside a link. */
  linkTo?: boolean
}

export default function PatternChips({ patterns, className = '', linkTo = false }: Props) {
  if (!patterns?.length) return null

  const style = 'chip bg-slate-100 text-slate-600'
  return (
    <div className={`flex flex-wrap gap-1 ${className}`}>
      {patterns.map((p) =>
        linkTo ? (
          <Link key={p} to={`/patterns#${p}`} className={`${style} hover:bg-slate-200 transition`}>
            {p}
          </Link>
        ) : (
          <span key={p} className={style}>{p}</span>
        ),
      )}
    </div>
  )
}
