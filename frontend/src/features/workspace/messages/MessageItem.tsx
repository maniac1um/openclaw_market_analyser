import type { ChatMessage } from '../../chat/types'
import { AssistantMessage } from './AssistantMessage'
import { ReportSummaryMessage } from './ReportSummaryMessage'
import { SystemMessage } from './SystemMessage'
import { UserMessage } from './UserMessage'

type MessageItemProps = {
  message: ChatMessage
  isGenerating?: boolean
}

export function MessageItem({ message, isGenerating }: MessageItemProps) {
  switch (message.role) {
    case 'user':
      return <UserMessage text={message.text} />
    case 'system':
      return <SystemMessage text={message.text} />
    case 'report':
      return (
        <div className="py-2">
          <ReportSummaryMessage
            reportId={message.reportId}
            trend={message.trend}
            risk={message.risk}
            title={message.title}
          />
        </div>
      )
    case 'assistant':
      return <AssistantMessage text={message.text} isGenerating={isGenerating} />
  }
}
