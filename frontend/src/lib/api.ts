import { getWriteHeaders } from './auth'

export type ReportInsights = {
  sentiment?: 'bullish' | 'bearish' | 'neutral'
  risk_level?: 'low' | 'medium' | 'high'
  market_impact?: string
  confidence?: '低' | '中' | '高'
  forecast?: string
  news_sentiment_counts?: { bullish: number; bearish: number; neutral: number }
}

export type ReportListItem = {
  ingest_id: string
  title?: string
  keyword?: string
  generated_at?: string
}

export type ReportDetail = ReportListItem & {
  time_range?: { start?: string; end?: string }
  analysis?: string
  sources?: string[]
  items_count?: number
  items?: NewsItem[]
  insights?: ReportInsights
  report_markdown?: string
}

export type NewsItem = {
  title?: string
  source?: string
  url?: string
  published_at?: string
  summary?: string
  price?: number
  currency?: string
}

export type TopicCard = ReportListItem & {
  analysis?: string
  items_count?: number
  sources?: string[]
  insights?: ReportInsights
}

export type NewsLibraryItem = {
  id: number
  keyword?: string
  summary?: string
  source_url?: string
  title?: string
  source_name?: string
  published_at?: string
  created_at?: string
}

export type Monitor = {
  monitor_id: string
  keyword?: string
  cadence?: string
  created_at?: string
  url_count?: number
  observation_count?: number
  last_captured_at?: string
}

export type WorkOverview = {
  gateway?: { ok?: boolean; detail?: string; latency_ms?: number }
  reports?: {
    available?: boolean
    published_count?: number
    last_generated_at?: string
    recent?: ReportListItem[]
  }
  price_monitoring?: {
    available?: boolean
    monitor_count?: number
    observation_count?: number
    recent?: Monitor[]
  }
  news_library?: {
    available?: boolean
    item_count?: number
    recent_keywords?: { keyword: string; item_count: number }[]
  }
}

export type WorkflowState = {
  overview?: WorkOverview
  gateway?: { ok?: boolean; detail?: string }
  internal_scheduler?: Record<string, unknown>
  external_scheduler_configs?: Record<string, unknown>[]
  external_scheduler_runs?: Record<string, unknown>[]
}

export type ApiKeyItem = {
  id: string
  key_prefix: string
  label: string
  created_at: string
  last_used_at?: string | null
}

export type ApiKeyCreated = ApiKeyItem & { api_key: string }

export class ApiError extends Error {
  status: number
  constructor(status: number, message: string) {
    super(message)
    this.status = status
  }
}

export type ChatRunPayload = {
  sessionKey: string
  text?: string
  done?: boolean
  status?: string
  error?: string | null
  updatedAt?: number
}

export type UsageSeriesPoint = {
  bucket: string
  tokens: number
}

export type UsageStats = {
  today: number
  total: number
  range: string
  range_total: number
  series: UsageSeriesPoint[]
}

export type UsageEntry = {
  id: string
  tokens_used: number
  endpoint: string
  metadata: {
    type?: string
    action?: string
    keyword?: string
  }
  label: string
  created_at: string
}

export type UsageEntries = {
  range: string
  entries: UsageEntry[]
}

export type Payment = {
  id: string
  user_id: string
  amount: number
  tokens: number
  status: string
  created_at?: string | null
  token_balance?: number | null
}

export type PaymentCreateBody = {
  tokens?: number
  amount?: number
}

export type UserBalance = {
  balance: number
  total_grants: number
  total_usage: number
}

export type Subscription = {
  id: string
  user_id: string
  plan: string
  status: string
  current_period_end?: string | null
  created_at?: string | null
}

export type NotificationItem = {
  id: string
  title: string
  content: string
  notification_type?: string | null
  created_at?: string | null
  read: boolean
}

export type NotificationList = {
  notifications: NotificationItem[]
  unread_count: number
}

export type MarkReadResult = {
  ok: boolean
  unread_count: number
}

let authHeaderProvider: (() => Record<string, string>) | null = null

export function setAuthHeaderProvider(fn: () => Record<string, string>) {
  authHeaderProvider = fn
}

function authHeaders(): Record<string, string> {
  return authHeaderProvider?.() ?? getWriteHeaders()
}

const creds: RequestInit = { credentials: 'include' }

async function fetchJson<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(path, {
    ...creds,
    ...init,
    headers: { ...authHeaders(), ...(init?.headers as Record<string, string> | undefined) },
  })
  if (!res.ok) {
    let detail = `HTTP ${res.status}`
    try {
      const body = await res.json()
      detail = body.detail || body.message || detail
    } catch {
      /* ignore */
    }
    throw new ApiError(res.status, String(detail))
  }
  return res.json() as Promise<T>
}

export const api = {
  listReports: () => fetchJson<ReportListItem[]>('/api/v1/public/reports'),
  getReport: (id: string) => fetchJson<ReportDetail>(`/api/v1/public/reports/${id}`),
  deleteReports: (ingest_ids: string[]) =>
    fetchJson('/api/v1/public/reports/bulk-delete', {
      method: 'POST',
      body: JSON.stringify({ ingest_ids }),
    }),
  topicCards: () => fetchJson<TopicCard[]>('/api/v1/public/topic/cards'),
  listNews: (keyword?: string) =>
    fetchJson<NewsLibraryItem[]>(`/api/v1/public/news/library?limit=200${keyword ? `&keyword=${encodeURIComponent(keyword)}` : ''}`),
  getNews: (id: number) => fetchJson<NewsLibraryItem>(`/api/v1/public/news/library/${id}`),
  deleteNews: (ids: number[]) =>
    fetchJson('/api/v1/public/news/library/bulk-delete', {
      method: 'POST',
      body: JSON.stringify({ ids }),
    }),
  listMonitors: () => fetchJson<Monitor[]>('/api/v1/public/monitoring/monitors'),
  timeseries: (monitorId: string, windowDays = 30) =>
    fetchJson<{ points: { date: string; avg_price?: number; min_price?: number; max_price?: number }[] }>(
      `/api/v1/public/monitoring/${monitorId}/timeseries?window_days=${windowDays}`,
    ),
  observations: (monitorId: string, limit = 200) =>
    fetchJson<{ rows: { index: number; item_name: string; captured_at?: string; price?: number; delta_from_prev?: number }[] }>(
      `/api/v1/public/monitoring/${monitorId}/observations?limit=${limit}`,
    ),
  workOverview: () => fetchJson<WorkOverview>('/api/v1/public/portal/openclaw-work-overview'),
  workflowState: () => fetchJson<WorkflowState>('/api/v1/public/workflow/state'),
  workflowDiagnostics: () => fetchJson('/api/v1/public/workflow/diagnostics'),
  workflowBootstrap: (body: { keyword: string; candidate_count?: number }) =>
    fetchJson('/api/v1/public/workflow/monitor/bootstrap', {
      method: 'POST',
      body: JSON.stringify(body),
    }),
  workflowAnalysis: (body: Record<string, unknown>) =>
    fetchJson('/api/v1/public/workflow/analysis/run', {
      method: 'POST',
      body: JSON.stringify(body),
    }),
  listApiKeys: () => fetchJson<ApiKeyItem[]>('/api/v1/public/auth/api-keys'),
  createApiKey: (label: string) =>
    fetchJson<ApiKeyCreated>('/api/v1/public/auth/api-keys', {
      method: 'POST',
      body: JSON.stringify({ label }),
    }),
  revokeApiKey: (id: string) =>
    fetchJson(`/api/v1/public/auth/api-keys/${id}`, { method: 'DELETE' }),
  chatActiveRuns: () => fetchJson<{ runs: ChatRunPayload[] }>('/api/v1/chat/runs/active'),
  chatRun: (sessionKey: string) => fetchJson<ChatRunPayload>(`/api/v1/chat/runs/${sessionKey}`),
  getUserBalance: () => fetchJson<UserBalance>('/api/v1/public/users/balance'),
  getSubscription: () => fetchJson<Subscription>('/api/v1/public/subscriptions'),
  upgradeSubscription: () =>
    fetchJson<Subscription>('/api/v1/public/subscriptions/upgrade', { method: 'POST' }),
  usageStats: (range: string) =>
    fetchJson<UsageStats>(`/api/v1/public/usage/stats?range=${encodeURIComponent(range)}`),
  usageEntries: (range: string) =>
    fetchJson<UsageEntries>(`/api/v1/public/usage/entries?range=${encodeURIComponent(range)}`),
  createPayment: (body?: PaymentCreateBody) =>
    fetchJson<Payment>('/api/v1/public/payments', {
      method: 'POST',
      body: JSON.stringify(body ?? {}),
    }),
  getPayment: (id: string) => fetchJson<Payment>(`/api/v1/public/payments/${id}`),
  confirmPayment: (id: string) =>
    fetchJson<Payment>(`/api/v1/public/payments/${id}/confirm`, { method: 'POST' }),
  listNotifications: () => fetchJson<NotificationList>('/api/v1/public/notifications'),
  markNotificationRead: (id: string) =>
    fetchJson<MarkReadResult>(`/api/v1/public/notifications/${id}/read`, { method: 'POST' }),
  markAllNotificationsRead: () =>
    fetchJson<MarkReadResult>('/api/v1/public/notifications/read-all', { method: 'POST' }),
}
