import type { Components } from 'react-markdown'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { cn } from '../../lib/utils'
import { markdownUrlTransform } from '../../lib/urlSafety'

type MarkdownContentProps = {
  children: string
  className?: string
  compact?: boolean
}

const markdownComponents: Components = {
  a: ({ href, children }) => (
    <a href={href} target="_blank" rel="noreferrer">
      {children}
    </a>
  ),
  table: ({ children }) => (
    <div className="prose-markdown-table-wrap">
      <table>{children}</table>
    </div>
  ),
  pre: ({ children }) => <pre className="prose-markdown-pre">{children}</pre>,
}

export function MarkdownContent({ children, className, compact }: MarkdownContentProps) {
  return (
    <div className={cn('prose-markdown', compact && 'prose-markdown-compact', className)}>
      <ReactMarkdown remarkPlugins={[remarkGfm]} urlTransform={markdownUrlTransform} components={markdownComponents}>
        {children || ''}
      </ReactMarkdown>
    </div>
  )
}
