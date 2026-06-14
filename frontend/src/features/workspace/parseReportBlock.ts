const REPORT_MARKER_RE = /<!--\s*oc-report\s*:?\s*(\{[\s\S]*?\})\s*-->/g
const REPORT_BODY_RE = /<!--\s*oc-report-body\s*-->[\s\S]*?<!--\s*\/oc-report-body\s*-->/g

export type ReportBlockData = {
  id: string
  trend?: string
  risk?: string
  title?: string
}

export type MessageSegment =
  | { kind: 'text'; text: string }
  | { kind: 'report'; report: ReportBlockData }

function parseReportPayload(raw: string): ReportBlockData | null {
  try {
    const parsed = JSON.parse(raw) as Record<string, unknown>
    const id = typeof parsed.id === 'string' ? parsed.id : typeof parsed.reportId === 'string' ? parsed.reportId : ''
    if (!id) return null
    return {
      id,
      trend: typeof parsed.trend === 'string' ? parsed.trend : undefined,
      risk: typeof parsed.risk === 'string' ? parsed.risk : undefined,
      title: typeof parsed.title === 'string' ? parsed.title : undefined,
    }
  } catch {
    return null
  }
}

/** Strip hidden full-report bodies and split assistant text into render segments. */
export function parseAssistantSegments(text: string): MessageSegment[] {
  const cleaned = text.replace(REPORT_BODY_RE, '').trim()
  if (!cleaned) return []

  const segments: MessageSegment[] = []
  let lastIndex = 0

  for (const match of cleaned.matchAll(REPORT_MARKER_RE)) {
    const index = match.index ?? 0
    const before = cleaned.slice(lastIndex, index).trim()
    if (before) segments.push({ kind: 'text', text: before })

    const report = parseReportPayload(match[1])
    if (report) segments.push({ kind: 'report', report })

    lastIndex = index + match[0].length
  }

  const tail = cleaned.slice(lastIndex).trim()
  if (tail) segments.push({ kind: 'text', text: tail })

  return segments.length ? segments : [{ kind: 'text', text: cleaned }]
}
