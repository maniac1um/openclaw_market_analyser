import { Loader2 } from 'lucide-react'
import { MarkdownContent } from '../../../components/markdown/MarkdownContent'
import { parseAssistantSegments } from '../parseReportBlock'
import { ReportSummaryMessage } from './ReportSummaryMessage'

type AssistantMessageProps = {
  text: string
  isGenerating?: boolean
}

export function AssistantMessage({ text, isGenerating }: AssistantMessageProps) {
  const segments = text ? parseAssistantSegments(text) : []

  return (
    <div className="flex gap-2 py-3 sm:gap-3">
      <div className="mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-full border border-[var(--color-border)] bg-[var(--color-surface)] text-xs font-semibold text-[var(--color-accent)]">
        OC
      </div>
      <div className="min-w-0 flex-1 space-y-3">
        {!text ? (
          <span className="inline-flex items-center gap-1 text-[var(--color-muted)]">
            <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-[var(--color-muted)]" />
            <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-[var(--color-muted)] [animation-delay:150ms]" />
            <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-[var(--color-muted)] [animation-delay:300ms]" />
          </span>
        ) : (
          segments.map((segment, index) =>
            segment.kind === 'report' ? (
              <ReportSummaryMessage
                key={`report-${segment.report.id}-${index}`}
                reportId={segment.report.id}
                trend={segment.report.trend}
                risk={segment.report.risk}
                title={segment.report.title}
              />
            ) : (
              <div key={`text-${index}`} className="text-sm text-[var(--ds-text-primary)]">
                <MarkdownContent compact>{segment.text}</MarkdownContent>
              </div>
            ),
          )
        )}
        {isGenerating ? (
          <p className="inline-flex items-center gap-1.5 text-xs text-[var(--color-muted)]">
            <Loader2 className="h-3.5 w-3.5 animate-spin" />
            生成中…
          </p>
        ) : null}
      </div>
    </div>
  )
}
