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
  side?: 'left' | 'right'
  width?: number
}

const ANIMATION_MS = 280

export const DRAWER_DEFAULT_WIDTH = { left: 260, right: 480 } as const

export function Drawer({
  open,
  onClose,
  title,
  children,
  className,
  side = 'right',
  width,
}: DrawerProps) {
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
    return () => document.removeEventListener('keydown', onKey)
  }, [mounted, onClose])

  if (!mounted) return null

  const panelWidth = width ?? DRAWER_DEFAULT_WIDTH[side]
  const hiddenTransform = side === 'left' ? '-translate-x-full' : 'translate-x-full'
  const panelPosition = side === 'left' ? 'left-0 border-r' : 'right-0 border-l'

  return createPortal(
    <aside
      role="dialog"
      aria-modal="false"
      aria-labelledby={title ? 'ds-drawer-title' : undefined}
      className={cn(
        'ds-drawer-panel fixed top-0 z-50 flex h-full max-w-full flex-col border-[var(--border)] bg-background will-change-transform transition-transform duration-[var(--ds-duration-drawer)] ease-[var(--ds-ease-out)]',
        panelPosition,
        visible ? 'translate-x-0' : hiddenTransform,
        !visible && 'pointer-events-none',
        className,
      )}
      style={{ width: panelWidth }}
    >
      {title ? (
        <header className="flex shrink-0 items-center justify-between gap-3 border-b border-[var(--border)] px-6 py-4">
          <h2 id="ds-drawer-title" className="text-base font-semibold text-primary">
            {title}
          </h2>
          <button
            type="button"
            onClick={onClose}
            aria-label="关闭抽屉"
            className="rounded-md p-1 text-[var(--text-secondary)] transition-colors duration-[var(--ds-duration-fast)] hover:bg-[var(--row-hover)] hover:text-primary"
          >
            <X className="h-5 w-5" />
          </button>
        </header>
      ) : null}
      <div className={cn('min-h-0 flex-1 overflow-y-auto', !title && 'p-0', title && 'p-6')}>
        {children}
      </div>
    </aside>,
    document.body,
  )
}
