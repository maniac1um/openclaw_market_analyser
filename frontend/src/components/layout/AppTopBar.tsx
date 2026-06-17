import { useState, type FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { History, Menu, Search, User } from 'lucide-react'
import { useAuth } from '../../lib/AuthContext'
import { CommandBar, CommandBarInput } from '../ui/ds'

type AppTopBarProps = {
  onOpenNav?: () => void
  onOpenInfo?: () => void
  onOpenUser?: () => void
  showInfoButton?: boolean
}

export function AppTopBar({ onOpenNav, onOpenInfo, onOpenUser, showInfoButton }: AppTopBarProps) {
  const navigate = useNavigate()
  const { user } = useAuth()
  const [query, setQuery] = useState('')

  const handleSearch = (e: FormEvent) => {
    e.preventDefault()
    const term = query.trim()
    if (!term) return
    navigate(`/app/news?q=${encodeURIComponent(term)}`)
  }

  const initials = user?.username?.slice(0, 1).toUpperCase() || '?'

  return (
    <header className="flex h-12 shrink-0 items-center gap-3 border-b border-[var(--border)] bg-background px-4 md:px-8">
      <button
        type="button"
        onClick={onOpenNav}
        className="inline-flex h-8 w-8 shrink-0 items-center justify-center rounded-lg text-[var(--text-secondary)] transition-colors hover:bg-[var(--row-hover)] hover:text-primary"
        aria-label="打开导航菜单"
      >
        <Menu className="h-5 w-5" />
      </button>

      <form onSubmit={handleSearch} className="min-w-0 flex-1">
        <CommandBar className="border-0 bg-transparent p-0 backdrop-blur-none">
          <Search className="h-4 w-4 shrink-0 text-[var(--text-secondary)]" aria-hidden />
          <CommandBarInput
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="搜索新闻、专题…"
            aria-label="全局搜索"
            className="min-w-0 border-0 px-0 focus:border-0"
          />
        </CommandBar>
      </form>

      {showInfoButton ? (
        <button
          type="button"
          onClick={onOpenInfo}
          className="inline-flex h-8 w-8 shrink-0 items-center justify-center rounded-lg text-[var(--text-secondary)] transition-colors hover:bg-[var(--row-hover)] hover:text-primary"
          aria-label="打开对话列表"
        >
          <History className="h-5 w-5" />
        </button>
      ) : null}

      {user ? (
        <button
          type="button"
          onClick={onOpenUser}
          className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full border border-[var(--border)] bg-[var(--bg-panel)] text-xs font-medium text-primary transition-colors hover:bg-[var(--row-hover)]"
          aria-label="打开账户"
        >
          {initials}
        </button>
      ) : (
        <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full border border-[var(--border)] text-[var(--text-secondary)]">
          <User className="h-4 w-4" />
        </span>
      )}
    </header>
  )
}
