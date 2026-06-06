import { ArrowLeft } from 'lucide-react'

export function MobileBackButton({ onClick, label = '返回列表' }: { onClick: () => void; label?: string }) {
  return (
    <button
      type="button"
      onClick={onClick}
      className="mb-4 inline-flex min-h-11 items-center gap-1.5 rounded-md px-1 text-sm text-[var(--color-muted)] hover:text-[var(--color-text)] lg:hidden"
    >
      <ArrowLeft className="h-4 w-4 shrink-0" />
      {label}
    </button>
  )
}
