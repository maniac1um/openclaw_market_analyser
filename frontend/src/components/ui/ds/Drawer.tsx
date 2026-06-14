import { useEffect, useState, type ReactNode } from 'react'
import { createPortal } from 'react-dom'
import { X } from 'lucide-react'
import { cn } from '../../../lib/utils'

type DrawerProps = {
  open: boolean
  onClose: () => void
  title?: string
  children: ReactNode
  className?: string
}

const ANIMATION_MS = 300

export function Drawer({ open, onClose, title, children, className }: DrawerProps) {
  const [mounted, setMounted] = useState(open)
  const [visible, setVisible] = useState(open)

  useEffect(() => {
    if (open) {
      setMounted(true)
      const frame = requestAnimationFrame(() => setVisible(true))
      return () => cancelAnimationFrame(frame)
    }
    setVisible(false)
    const timer = window.setTimeout(() => setMounted(false), ANIMATION_MS)
    return () => window.clearTimeout(timer)
  }, [open])

  useEffect(() => {
    if (!mounted) return
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose()
    }
    document.addEventListener('keydown', onKey)
    document.body.style.overflow = 'hidden'
    return () => {
      document.removeEventListener('keydown', onKey)
      document.body.style.overflow = ''
    }
  }, [mounted, onClose])

  if (!mounted) return null

  return createPortal(
    <div
      className={cn('fixed inset-0 z-50', visible ? 'pointer-events-auto' : 'pointer-events-none')}
      role="presentation"
    >
      <button
        type="button"
        aria-label="关闭"
        className={cn(
          'absolute inset-0 bg-black/50 backdrop-blur-sm transition-opacity duration-300',
          visible ? 'opacity-100' : 'opacity-0',
        )}
        onClick={onClose}
      />
      <aside
        role="dialog"
        aria-modal="true"
        aria-labelledby={title ? 'ds-drawer-title' : undefined}
        className={cn(
          'absolute top-0 right-0 flex h-full w-[480px] max-w-full flex-col border-l border-[var(--ds-border)] bg-[var(--ds-bg-base)] will-change-transform transition-transform duration-300 ease-[cubic-bezier(0.16,1,0.3,1)]',
          visible ? 'translate-x-0' : 'translate-x-full',
          className,
        )}
      >
        {title ? (
          <header className="flex shrink-0 items-center justify-between gap-3 border-b border-[var(--ds-border)] px-6 py-4">
            <h2 id="ds-drawer-title" className="text-base font-semibold text-[var(--ds-text-primary)]">
              {title}
            </h2>
            <button
              type="button"
              onClick={onClose}
              aria-label="关闭抽屉"
              className="rounded-md p-1 text-[var(--ds-text-secondary)] transition-colors hover:bg-white/5 hover:text-[var(--ds-text-primary)]"
            >
              <X className="h-5 w-5" />
            </button>
          </header>
        ) : null}
        <div className="min-h-0 flex-1 overflow-y-auto p-6 transition-opacity duration-200 ease-out" style={{ opacity: visible ? 1 : 0 }}>
          {children}
        </div>
      </aside>
    </div>,
    document.body,
  )
}
