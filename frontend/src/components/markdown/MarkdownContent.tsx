import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { cn } from '../../lib/utils'
import { markdownUrlTransform } from '../../lib/urlSafety'

type MarkdownContentProps = {
  children: string
  className?: string
  compact?: boolean
}

export function MarkdownContent({ children, className, compact }: MarkdownContentProps) {
  return (
    <div className={cn('prose-markdown', compact && 'prose-markdown-compact', className)}>
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        urlTransform={markdownUrlTransform}
        components={{
          a: ({ href, children: linkChildren }) => (
            <a href={href} target="_blank" rel="noreferrer">
              {linkChildren}
            </a>
          ),
        }}
      >
        {children || ''}
      </ReactMarkdown>
    </div>
  )
}
