import { TrendingDown, TrendingUp, Shield, Target } from 'lucide-react'
import { Card, CardContent } from '../../components/ui/Card'
import type { ReportInsights } from '../../lib/api'
import { riskLabel, sentimentLabel } from '../../lib/insights'

function InsightCard({
  icon,
  label,
  value,
  sub,
}: {
  icon: React.ReactNode
  label: string
  value: string
  sub?: string
}) {
  return (
    <Card>
      <CardContent className="flex items-start gap-3 p-4">
        <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-[var(--color-accent-soft)] text-[var(--color-accent)]">
          {icon}
        </div>
        <div className="min-w-0">
          <p className="text-xs text-[var(--color-muted)]">{label}</p>
          <p className="mt-0.5 text-lg font-semibold tracking-tight">{value}</p>
          {sub && <p className="mt-1 text-xs text-[var(--color-muted)] line-clamp-2">{sub}</p>}
        </div>
      </CardContent>
    </Card>
  )
}

export function InsightGrid({ insights }: { insights: ReportInsights }) {
  const sentiment = insights.sentiment ? sentimentLabel[insights.sentiment] || insights.sentiment : '—'
  const risk = insights.risk_level ? riskLabel[insights.risk_level] || insights.risk_level : '—'
  const confidence = insights.confidence || '—'
  const forecast = insights.forecast || '—'

  return (
    <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
      <InsightCard
        icon={insights.sentiment === 'bearish' ? <TrendingDown className="h-4 w-4" /> : <TrendingUp className="h-4 w-4" />}
        label="情绪分析"
        value={sentiment}
        sub={
          insights.news_sentiment_counts
            ? `利多 ${insights.news_sentiment_counts.bullish} / 利空 ${insights.news_sentiment_counts.bearish}`
            : undefined
        }
      />
      <InsightCard icon={<Shield className="h-4 w-4" />} label="风险等级" value={risk} />
      <InsightCard
        icon={<Target className="h-4 w-4" />}
        label="市场影响"
        value={forecast}
        sub={insights.market_impact}
      />
      <InsightCard icon={<TrendingUp className="h-4 w-4" />} label="置信度" value={confidence} />
    </div>
  )
}
