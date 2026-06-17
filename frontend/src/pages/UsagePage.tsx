import { useQuery } from '@tanstack/react-query'
import { useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../lib/api'
import { ChartTimeRangePicker } from '../components/charts/ChartTimeRangePicker'
import { TokenUsageChart } from '../components/charts/TokenUsageChart'
import type { TimeRange } from '../components/charts/types'
import { TIME_RANGE_LABELS } from '../components/charts/types'
import { ChartSkeleton, Skeleton } from '../components/ui/ds'
import { ErrorBanner } from '../components/ui/States'

const CHART_HEIGHT = 320

function formatTokens(value: number | undefined): string {
  if (value == null) return '—'
  return value.toLocaleString()
}

function formatUsageTime(iso: string): string {
  try {
    return new Date(iso).toLocaleString('zh-CN', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    })
  } catch {
    return iso
  }
}

export function UsagePage() {
  const [timeRange, setTimeRange] = useState<TimeRange>('7d')

  const statsQuery = useQuery({
    queryKey: ['usage-stats', timeRange],
    queryFn: () => api.usageStats(timeRange),
  })

  const entriesQuery = useQuery({
    queryKey: ['usage-entries', timeRange],
    queryFn: () => api.usageEntries(timeRange),
  })

  const stats = statsQuery.data
  const entries = entriesQuery.data?.entries ?? []

  return (
    <div className="mx-auto flex w-full max-w-4xl flex-col gap-8">
      <header className="flex flex-wrap items-end justify-between gap-4 border-b border-[var(--ds-border)] pb-6">
        <div>
          <h1 className="text-lg font-semibold text-[var(--ds-text-primary)]">Token 使用</h1>
          <p className="mt-1 text-sm text-[var(--ds-text-secondary)]">
            查看 AI 请求的 token 消耗趋势与明细
          </p>
        </div>
        <ChartTimeRangePicker value={timeRange} onChange={setTimeRange} />
      </header>

      <div className="grid gap-8 sm:grid-cols-2">
        <div>
          <p className="text-xs font-medium uppercase tracking-wide text-[var(--ds-text-secondary)]">
            今日使用量
          </p>
          <p className="mt-1 text-3xl font-semibold tabular-nums text-[var(--ds-text-primary)]">
            {statsQuery.isLoading ? '…' : formatTokens(stats?.today)}
          </p>
        </div>
        <div>
          <p className="text-xs font-medium uppercase tracking-wide text-[var(--ds-text-secondary)]">
            总使用量
          </p>
          <p className="mt-1 text-3xl font-semibold tabular-nums text-[var(--ds-text-primary)]">
            {statsQuery.isLoading ? '…' : formatTokens(stats?.total)}
          </p>
        </div>
      </div>

      <section className="flex flex-col gap-3">
        <div className="flex flex-wrap items-baseline justify-between gap-2">
          <h2 className="text-sm font-medium text-[var(--ds-text-primary)]">使用趋势</h2>
          {stats ? (
            <p className="text-xs text-[var(--ds-text-secondary)]">
              {TIME_RANGE_LABELS[timeRange]} 合计 {formatTokens(stats.range_total)} tokens
            </p>
          ) : null}
        </div>

        {statsQuery.isLoading ? (
          <ChartSkeleton height={CHART_HEIGHT} />
        ) : statsQuery.isError ? (
          <ErrorBanner
            message={(statsQuery.error as Error).message}
            onRetry={() => statsQuery.refetch()}
          />
        ) : (
          <TokenUsageChart series={stats?.series ?? []} height={CHART_HEIGHT} />
        )}
      </section>

      <section className="flex flex-col gap-3">
        <h2 className="text-sm font-medium text-[var(--ds-text-primary)]">使用明细</h2>

        {entriesQuery.isLoading ? (
          <div className="flex flex-col gap-2">
            {Array.from({ length: 5 }).map((_, i) => (
              <Skeleton key={i} className="h-12 w-full rounded-lg" />
            ))}
          </div>
        ) : entriesQuery.isError ? (
          <ErrorBanner
            message={(entriesQuery.error as Error).message}
            onRetry={() => entriesQuery.refetch()}
          />
        ) : entries.length === 0 ? (
          <p className="rounded-lg border border-dashed border-[var(--ds-border)] px-4 py-8 text-center text-sm text-[var(--ds-text-secondary)]">
            {TIME_RANGE_LABELS[timeRange]}暂无扣费记录
          </p>
        ) : (
          <ul className="divide-y divide-[var(--ds-border)] rounded-lg border border-[var(--ds-border)]">
            {entries.map((entry) => (
              <li
                key={entry.id}
                className="flex flex-wrap items-center justify-between gap-3 px-4 py-3"
              >
                <div className="min-w-0 flex-1">
                  <p className="truncate text-sm text-[var(--ds-text-primary)]">{entry.label}</p>
                  <p className="mt-0.5 text-xs text-[var(--ds-text-secondary)]">
                    {formatUsageTime(entry.created_at)}
                  </p>
                </div>
                <p className="shrink-0 text-sm font-medium tabular-nums text-[var(--ds-text-primary)]">
                  -{formatTokens(entry.tokens_used)} tokens
                </p>
              </li>
            ))}
          </ul>
        )}
      </section>

      <p className="text-xs text-[var(--ds-text-secondary)]">
        数据来自 token_usage 表，按 Asia/Shanghai 时区聚合。
        <Link to="/app/account" className="ml-1 text-[var(--color-accent)] hover:underline">
          账户设置
        </Link>
      </p>
    </div>
  )
}
