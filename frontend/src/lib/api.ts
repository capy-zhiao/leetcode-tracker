// 统一的后端调用封装。所有网络请求都走这里,好处是:
//   - 出错处理只写一次
//   - 以后加 API Key / 换 base URL 只改这一个文件
import type {
  Attempt, AttemptIn, AttemptResult, CodeReview, DailyQueue,
  FollowUp, MistakeTag, MockStart, Problem, ProblemDetail, Stats,
} from './types'

// vite.config.ts 里配了代理:/api/xxx -> http://localhost:8000/xxx
const BASE = '/api'
const API_KEY = import.meta.env.VITE_API_KEY ?? ''

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(BASE + path, {
    ...init,
    headers: {
      'Content-Type': 'application/json',
      ...(API_KEY ? { 'X-API-Key': API_KEY } : {}),
      ...init?.headers,
    },
  })
  if (!res.ok) {
    const detail = await res.json().catch(() => ({}))
    throw new Error(detail.detail ?? `请求失败 (${res.status})`)
  }
  return res.json() as Promise<T>
}

const qs = (params: Record<string, unknown>) => {
  const p = new URLSearchParams()
  Object.entries(params).forEach(([k, v]) => {
    if (v !== undefined && v !== null && v !== '') p.set(k, String(v))
  })
  const s = p.toString()
  return s ? `?${s}` : ''
}

export const api = {
  health: () => request<{ status: string; llm_enabled: boolean }>('/health'),

  // --- 每日队列 / 做题 ---
  today: (caps?: { review_cap?: number; new_cap?: number }) =>
    request<DailyQueue>(`/review/today${qs(caps ?? {})}`),
  forecast: (days = 14) =>
    request<{ date: string; count: number; overdue: number }[]>(`/review/forecast${qs({ days })}`),
  suggestGrade: (p: { seconds: number; looked_at_solution: boolean; had_bugs: boolean; difficulty: string }) =>
    request<{ grade: string; reason: string }>(`/review/suggest-grade${qs(p)}`),
  submitAttempt: (number: number, body: AttemptIn) =>
    request<AttemptResult>(`/review/${number}/attempt`, {
      method: 'POST', body: JSON.stringify(body),
    }),
  attempts: (number: number) => request<Attempt[]>(`/review/${number}/attempts`),

  // --- 题库 ---
  problems: (f?: { chapter?: number; difficulty?: string; status?: string; q?: string; kind?: string }) =>
    request<Problem[]>(`/problems${qs(f ?? {})}`),
  problem: (number: number) => request<ProblemDetail>(`/problems/${number}`),
  updateProblem: (number: number, body: { notes?: string; code?: string }) =>
    request<ProblemDetail>(`/problems/${number}`, { method: 'PATCH', body: JSON.stringify(body) }),
  mistakeTags: () => request<MistakeTag[]>('/problems/mistake-tags'),

  // --- 统计 ---
  stats: () => request<Stats>('/stats'),
  heatmap: (days = 90) => request<{ date: string; count: number }[]>(`/stats/heatmap${qs({ days })}`),

  // --- Mock interview ---
  mockStart: (f?: { difficulty?: string; chapter?: number; only_solved?: boolean }) =>
    request<MockStart>(`/mock/start${qs(f ?? {})}`, { method: 'POST' }),
  followups: (number: number, regenerate = false) =>
    request<FollowUp[]>(`/mock/${number}/followups${qs({ regenerate })}`),
  reviewCode: (number: number, code: string) =>
    request<CodeReview>(`/mock/${number}/review-code`, {
      method: 'POST', body: JSON.stringify({ code }),
    }),
}
