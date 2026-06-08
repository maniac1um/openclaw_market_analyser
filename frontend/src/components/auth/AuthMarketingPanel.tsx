import { Link } from 'react-router-dom'
import { FileText, LineChart, MessageSquare } from 'lucide-react'
import { Badge } from '../../components/ui/Badge'

export function AuthMarketingPanel() {
  return (
    <div className="hidden flex-1 flex-col justify-center border-r border-[var(--color-border)] bg-[var(--color-surface)] p-10 lg:flex">
      <Badge variant="muted" className="mb-4 w-fit">
        OpenClaw 分析平台
      </Badge>
      <h2 className="text-2xl font-semibold tracking-tight">市场趋势分析，从关键词到报告</h2>
      <p className="mt-3 max-w-md text-sm leading-relaxed text-[var(--color-muted)]">
        追踪关键词、汇聚新闻、生成 AI 专题报告，并用图表呈现价格走势。注册后约 10 分钟可完成首个分析闭环。
      </p>
      <ul className="mt-8 space-y-4 text-sm">
        <li className="flex gap-3">
          <MessageSquare className="mt-0.5 h-5 w-5 shrink-0 text-[var(--color-accent)]" />
          <span>AI 对话提问市场分析与研究任务</span>
        </li>
        <li className="flex gap-3">
          <FileText className="mt-0.5 h-5 w-5 shrink-0 text-[var(--color-accent)]" />
          <span>情绪 / 风险 / 置信度结构化专题报告</span>
        </li>
        <li className="flex gap-3">
          <LineChart className="mt-0.5 h-5 w-5 shrink-0 text-[var(--color-accent)]" />
          <span>关键词价格监测与 30 日趋势图</span>
        </li>
      </ul>
      <p className="mt-8 text-sm text-[var(--color-muted)]">
        <Link to="/" className="text-[var(--color-accent)] hover:underline">
          了解 OpenClaw 产品能力 →
        </Link>
      </p>
    </div>
  )
}
