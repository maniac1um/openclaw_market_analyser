import { NavLink } from 'react-router-dom'
import { FileText, Loader2 } from 'lucide-react'
import { cn } from '../../lib/utils'

export const sidebarNav = [
  { to: '/app', label: '首页', end: true },
  { to: '/app/reports', label: '专题分析' },
  { to: '/app/news', label: '新闻' },
  { to: '/app/price-trend', label: '价格趋势' },
  { to: '/app/keyword-tracking', label: '关键词' },
  { to: '/app/workflow', label: '工作流' },
  { to: '/app/account', label: '账户' },
] as const

type AppSidebarProps = {
  chatBusy?: boolean
  onNavigate?: () => void
  className?: string
}

function SidebarNavItem({
  item,
  chatBusy,
  onNavigate,
}: {
  item: (typeof sidebarNav)[number]
  chatBusy?: boolean
  onNavigate?: () => void
}) {
  return (
    <NavLink
      to={item.to}
      end={'end' in item ? item.end : false}
      onClick={onNavigate}
      className={({ isActive }) =>
        cn(
          'relative flex items-center gap-2 rounded-lg px-3 py-2.5 text-sm transition-colors',
          isActive
            ? 'font-medium text-[var(--ds-text-primary)]'
            : 'text-[var(--ds-text-secondary)] hover:bg-white/5 hover:text-[var(--ds-text-primary)]',
        )
      }
    >
      {({ isActive }) => (
        <>
          {isActive ? (
            <span
              className="absolute top-1/2 left-0 h-5 w-0.5 -translate-y-1/2 rounded-full bg-[var(--color-accent)]"
              aria-hidden
            />
          ) : null}
          <span className="pl-1">{item.label}</span>
          {item.to === '/app' && chatBusy ? (
            <span className="ml-auto inline-flex items-center gap-1 text-[10px] font-medium text-[var(--color-accent)]">
              <Loader2 className="h-3 w-3 animate-spin" />
            </span>
          ) : null}
        </>
      )}
    </NavLink>
  )
}

export function AppSidebar({ chatBusy, onNavigate, className }: AppSidebarProps) {
  return (
    <aside
      className={cn(
        'flex w-[220px] shrink-0 flex-col border-r border-[var(--ds-border)] bg-[var(--ds-bg-base)]',
        className,
      )}
    >
      <div className="flex h-12 shrink-0 items-center gap-2 border-b border-[var(--ds-border)] px-4">
        <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-md bg-[var(--color-accent)] text-white">
          <FileText className="h-4 w-4" />
        </span>
        <span className="truncate text-sm font-semibold text-[var(--ds-text-primary)]">OpenClaw</span>
      </div>

      <nav className="flex flex-1 flex-col gap-0.5 overflow-y-auto p-3" aria-label="主导航">
        {sidebarNav.map((item) => (
          <SidebarNavItem key={item.to} item={item} chatBusy={chatBusy} onNavigate={onNavigate} />
        ))}
      </nav>
    </aside>
  )
}
