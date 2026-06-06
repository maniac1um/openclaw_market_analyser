import type { ReportDetail, ReportInsights } from './api'

const POSITIVE = ['上涨', '走强', '利好', '增持', '突破', '反弹', '上调', '紧张', '减产']
const NEGATIVE = ['下跌', '走弱', '利空', '抛售', '回落', '暴跌', '下调', '宽松', '增产']

function sentimentFromText(text: string): 'bullish' | 'bearish' | 'neutral' {
  const lower = text.toLowerCase()
  const p = POSITIVE.filter((t) => lower.includes(t)).length
  const n = NEGATIVE.filter((t) => lower.includes(t)).length
  if (p > n) return 'bullish'
  if (n > p) return 'bearish'
  return 'neutral'
}

export function deriveInsights(report: ReportDetail): ReportInsights {
  if (report.insights && Object.keys(report.insights).length > 0) {
    return report.insights
  }

  const analysis = report.analysis || ''
  const items = report.items || []
  let bullish = 0
  let bearish = 0
  let neutral = 0
  for (const item of items.slice(0, 12)) {
    const s = sentimentFromText(`${item.title || ''} ${item.summary || ''}`)
    if (s === 'bullish') bullish++
    else if (s === 'bearish') bearish++
    else neutral++
  }

  let sentiment: ReportInsights['sentiment'] = 'neutral'
  if (bullish > bearish) sentiment = 'bullish'
  else if (bearish > bullish) sentiment = 'bearish'
  else sentiment = sentimentFromText(analysis)

  let risk_level: ReportInsights['risk_level'] = 'medium'
  if (['暴跌', '危机', '制裁', '违约', '中断'].some((t) => analysis.includes(t))) risk_level = 'high'
  else if (['平稳', '稳定', '缓和', '复苏'].some((t) => analysis.includes(t))) risk_level = 'low'

  let confidence: ReportInsights['confidence'] = '中'
  if (analysis.includes('置信度')) {
    if (analysis.includes('高')) confidence = '高'
    else if (analysis.includes('低')) confidence = '低'
  }

  let forecast = '震荡'
  if (analysis.includes('上行') || analysis.includes('偏强')) forecast = '上行'
  else if (analysis.includes('下行') || analysis.includes('偏弱')) forecast = '下行'

  return {
    sentiment,
    risk_level,
    market_impact: analysis.slice(0, 200) + (analysis.length > 200 ? '…' : ''),
    confidence,
    forecast,
    news_sentiment_counts: { bullish, bearish, neutral },
  }
}

export const sentimentLabel: Record<string, string> = {
  bullish: '偏多',
  bearish: '偏空',
  neutral: '中性',
}

export const riskLabel: Record<string, string> = {
  low: '低',
  medium: '中',
  high: '高',
}
