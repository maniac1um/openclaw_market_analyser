import { useQuery } from '@tanstack/react-query'
import { useState } from 'react'
import { api } from '../lib/api'
import { formatCnDateTime } from '../lib/utils'
import { ErrorBanner } from '../components/ui/States'
import {
  Panel,
  StatStrip,
  StatStripItem,
  PageSkeleton,
  Table,
  TableHead,
  TableBody,
  TableRow,
  TableHeaderRow,
  TableCell,
  TableHeaderCell,
} from '../components/ui/ds'

type Tab = 'monitors' | 'news' | 'reports'

export function KeywordTrackingPage() {
  const [tab, setTab] = useState<Tab>('monitors')

  const overviewQuery = useQuery({ queryKey: ['overview'], queryFn: api.workOverview })
  const reportsQuery = useQuery({ queryKey: ['reports'], queryFn: api.listReports })
  const newsQuery = useQuery({ queryKey: ['news-all'], queryFn: () => api.listNews() })

  if (overviewQuery.isLoading) return <PageSkeleton tables={1} statItems={3} />
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
    <div className="flex flex-col gap-8">
      <header>
        <h1 className="text-lg font-semibold text-[var(--ds-text-primary)]">关键词</h1>
        <p className="mt-1 text-sm text-[var(--ds-text-secondary)]">跨模块关键词追踪概览</p>
      </header>

      <StatStrip>
        <StatStripItem label="监测任务" value={price?.monitor_count ?? 0} />
        <StatStripItem label="新闻关键词" value={newsKw.length} />
        <StatStripItem label="报告总数" value={reportsQuery.data?.length ?? 0} />
      </StatStrip>

      <div className="flex gap-1 rounded-lg border border-[var(--ds-border)] p-1 transition-[border-color] duration-[var(--ds-duration-fast)] hover:border-[var(--ds-border-hover)]">
        {tabs.map((t) => (
          <button
            key={t.id}
            onClick={() => setTab(t.id)}
            className={`flex-1 rounded-md px-3 py-2 text-sm font-medium transition-colors duration-[var(--ds-duration-fast)] ${
              tab === t.id
                ? 'bg-[var(--color-accent)] text-[var(--accent-fg)]'
                : 'text-[var(--text-secondary)] hover:bg-[var(--row-hover)] hover:text-primary'
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      <Panel className="overflow-x-auto p-0">
        <Table>
          <TableHead>
            <TableHeaderRow>
              <TableHeaderCell>关键词</TableHeaderCell>
              <TableHeaderCell>数量</TableHeaderCell>
              <TableHeaderCell>最近更新</TableHeaderCell>
              <TableHeaderCell>状态</TableHeaderCell>
            </TableHeaderRow>
          </TableHead>
          <TableBody>
            {tab === 'monitors' &&
              (price?.recent || []).map((m) => (
                <TableRow key={m.monitor_id}>
                  <TableCell className="font-medium">{m.keyword}</TableCell>
                  <TableCell>{m.observation_count} 观测</TableCell>
                  <TableCell className="text-[var(--ds-text-secondary)]">{formatCnDateTime(m.last_captured_at)}</TableCell>
                  <TableCell>{(m.observation_count || 0) > 0 ? '正常' : '待采集'}</TableCell>
                </TableRow>
              ))}
            {tab === 'news' &&
              newsKw.map((k) => (
                <TableRow key={k.keyword}>
                  <TableCell className="font-medium">{k.keyword}</TableCell>
                  <TableCell>{k.item_count}</TableCell>
                  <TableCell className="text-[var(--ds-text-secondary)]">—</TableCell>
                  <TableCell>{(k.item_count || 0) > 0 ? '正常' : '待入库'}</TableCell>
                </TableRow>
              ))}
            {tab === 'reports' &&
              Object.entries(reportByKeyword).map(([kw, v]) => (
                <TableRow key={kw}>
                  <TableCell className="font-medium">{kw}</TableCell>
                  <TableCell>{v.count}</TableCell>
                  <TableCell className="text-[var(--ds-text-secondary)]">{formatCnDateTime(v.latest)}</TableCell>
                  <TableCell>{v.count > 0 ? '正常' : '待生成'}</TableCell>
                </TableRow>
              ))}
          </TableBody>
        </Table>
        {tab === 'news' && !newsKw.length && !newsQuery.isLoading ? (
          <p className="p-4 text-sm text-[var(--ds-text-secondary)]">暂无新闻关键词数据</p>
        ) : null}
      </Panel>
    </div>
  )
}
