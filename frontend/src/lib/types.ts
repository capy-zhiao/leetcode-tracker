// 和后端 schemas.py 一一对应。TypeScript 的类型只在编译期存在,
// 作用是让编辑器帮你catch「拼错字段名」这类错误。

export type Grade = 'again' | 'hard' | 'good' | 'easy'
export type Difficulty = 'Easy' | 'Medium' | 'Hard'

export interface ReviewStateT {
  interval_days: number
  ease: number
  reps: number
  lapses: number
  due: string | null
  total_attempts: number
  best_seconds: number | null
}

export interface Problem {
  id: number
  number: number
  title: string
  difficulty: Difficulty
  chapter_num: number
  chapter: string
  url: string
  in_neetcode150: boolean
  kind: 'problem' | 'template'
  state: ReviewStateT | null
}

export interface ProblemDetail extends Problem {
  notes: string
  code: string
}

export interface QueueItem {
  problem: Problem
  reason: 'due' | 'new' | 'template'
  priority_score: number
  overdue_days: number
}

export interface DailyQueue {
  date: string
  reviews: QueueItem[]
  new_problems: QueueItem[]
  templates: QueueItem[]
  total_due: number
  deferred: number
}

export interface MistakeTag { id: string; label: string; hint: string }
export interface MistakeStat extends MistakeTag { count: number; pct: number }

export interface AttemptIn {
  grade: Grade
  seconds: number
  looked_at_solution: boolean
  had_bugs: boolean
  mistakes: string[]
  code: string
  note: string
  mode: 'practice' | 'mock'
}

export interface Attempt {
  id: number
  problem_id: number
  created_at: string
  grade: Grade
  seconds: number
  mistakes: string[]
  note: string
  mode: string
  code: string
}

export interface AttemptResult {
  attempt: Attempt
  state: ReviewStateT
  next_due_in_days: number
}

export interface ChapterStat {
  chapter_num: number; chapter: string
  total: number; started: number; mastered: number
}

export interface Stats {
  total_problems: number; started: number; mastered: number
  due_today: number; attempts_total: number; attempts_7d: number
  streak_days: number; avg_seconds: number
  by_chapter: ChapterStat[]
  top_mistakes: MistakeStat[]
}

export interface FollowUp { id: number; question: string; hint: string }
export interface MockStart { problem: ProblemDetail; minutes: number; followups_ready: boolean }
export interface CodeReview { summary: string; issues: string[]; suggested_mistakes: string[] }
