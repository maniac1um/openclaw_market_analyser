import { useQuery } from '@tanstack/react-query'
import { useState } from 'react'
import { api } from '../lib/api'
import { formatCnDateTime } from '../lib/utils'
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/Card'
import { Skeleton, ErrorBanner } from '../components/ui/States'

type Tab = 'monitors' | 'news' | 'reports'

export function KeywordTrackingPage() {
  const [tab, setTab] = useState<Tab>('monitors')

  const overviewQuery = useQuery({ queryKey: ['overview'], queryFn: api.workOverview })
  const reportsQuery = useQuery({ queryKey: ['reports'], queryFn: api.listReports })
  const newsQuery = useQuery({ queryKey: ['news-all'], queryFn: () => api.listNews() })

  if (overviewQuery.isLoading) return <Skeleton className="h-[500px]" />
  if (overviewQuery.isError) return <ErrorBanner message={(overviewQuery.error as Error).message} />

  const price = overviewQuery.data?.price_monitoring
  const newsKw = overviewQuery.data?.news_library?.recent_keywords || []

  const reportByKeyword = (reportsQuery.data || []).reduce<Record<string, { count: number; latest?: string }>>((acc, r) => {
    const kw = r.keyword || '未分类'
    if (!acc[kw]) acc[kw] = { count: 0 }
    acc[kw].count++
    if (!acc[kw].latest || (r.generated_at && r.generated_at > acc[kw].latest!)) {
      acc[kw].latest = r.generated_at
    }
    return acc
  }, {})

  const tabs: { id: Tab; label: string }[] = [
    { id: 'monitors', label: '价格监测' },
    { id: 'news', label: '新闻库' },
    { id: 'reports', label: '报告' },
  ]

  return (
    <div className="space-y-6">
      <div className="grid gap-4 sm:grid-cols-3">
        <Card>
          <CardContent className="p-4">
            <p className="text-xs text-[var(--color-muted)]">监测任务</p>
            <p className="text-2xl font-semibold">{price?.monitor_count ?? 0}</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <p className="text-xs text-[var(--color-muted)]">新闻关键词</p>
            <p className="text-2xl font-semibold">{newsKw.length}</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <p className="text-xs text-[var(--color-muted)]">报告总数</p>
            <p className="text-2xl font-semibold">{reportsQuery.data?.length ?? 0}</p>
          </CardContent>
        </Card>
      </div>

      <div className="flex gap-1 rounded-lg border border-[var(--color-border)] p-1">
        {tabs.map((t) => (
          <button
            key={t.id}
            onClick={() => setTab(t.id)}
            className={`flex-1 rounded-md px-3 py-2 text-sm font-medium transition-colors ${
              tab === t.id ? 'bg-[var(--color-accent)] text-white' : 'text-[var(--color-muted)] hover:text-[var(--color-text)]'
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      <Card>
        <CardHeader>
          <CardTitle>{tabs.find((t) => t.id === tab)?.label}</CardTitle>
        </CardHeader>
        <CardContent className="overflow-x-auto p-0">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-[var(--color-border)] text-left text-xs text-[var(--color-muted)]">
                <th className="px-4 py-2">关键词</th>
                <th className="px-4 py-2">数量</th>
                <th className="px-4 py-2">最近更新</th>
                <th className="px-4 py-2">状态</th>
              </tr>
            </thead>
            <tbody>
              {tab === 'monitors' &&
                (price?.recent || []).map((m) => (
                  <tr key={m.monitor_id} className="border-b border-[var(--color-border)]">
                    <td className="px-4 py-2 font-medium">{m.keyword}</td>
                    <td className="px-4 py-2">{m.observation_count} 观测</td>
                    <td className="px-4 py-2 text-[var(--color-muted)]">{formatCnDateTime(m.last_captured_at)}</td>
                    <td className="px-4 py-2">{(m.observation_count || 0) > 0 ? '正常' : '待采集'}</td>
                  </tr>
                ))}
              {tab === 'news' &&
                newsKw.map((k) => (
                  <tr key={k.keyword} className="border-b border-[var(--color-border)]">
                    <td className="px-4 py-2 font-medium">{k.keyword}</td>
                    <td className="px-4 py-2">{k.item_count}</td>
                    <td className="px-4 py-2 text-[var(--color-muted)]">—</td>
                    <td className="px-4 py-2">{(k.item_count || 0) > 0 ? '正常' : '待入库'}</td>
                  </tr>
                ))}
              {tab === 'reports' &&
                Object.entries(reportByKeyword).map(([kw, v]) => (
                  <tr key={kw} className="border-b border-[var(--color-border)]">
                    <td className="px-4 py-2 font-medium">{kw}</td>
                    <td className="px-4 py-2">{v.count}</td>
                    <td className="px-4 py-2 text-[var(--color-muted)]">{formatCnDateTime(v.latest)}</td>
                    <td className="px-4 py-2">{v.count > 0 ? '正常' : '待生成'}</td>
                  </tr>
                ))}
            </tbody>
          </table>
          {tab === 'news' && !newsKw.length && !newsQuery.isLoading && (
            <p className="p-4 text-sm text-[var(--color-muted)]">暂无新闻关键词数据</p>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
