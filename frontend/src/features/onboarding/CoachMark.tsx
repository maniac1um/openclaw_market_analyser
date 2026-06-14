import { useEffect, useState } from 'react'
import { createPortal } from 'react-dom'
import { COACH_MESSAGES, type OnboardingCoachTarget } from './types'

type Rect = { top: number; left: number; width: number; height: number }

function measureTarget(target: OnboardingCoachTarget): Rect | null {
  const el = document.querySelector(`[data-onboarding="${target}"]`)
  if (!el) return null
  const r = el.getBoundingClientRect()
  return { top: r.top, left: r.left, width: r.width, height: r.height }
}

export function CoachMark({
  target,
  onDismiss,
}: {
  target: OnboardingCoachTarget | null
  onDismiss?: () => void
}) {
  const [rect, setRect] = useState<Rect | null>(null)

  useEffect(() => {
    if (!target) {
      setRect(null)
      return
    }

    const update = () => setRect(measureTarget(target))
    update()

    const t = window.setTimeout(update, 120)
    window.addEventListener('resize', update)
    window.addEventListener('scroll', update, true)

    return () => {
      window.clearTimeout(t)
      window.removeEventListener('resize', update)
      window.removeEventListener('scroll', update, true)
    }
  }, [target])

  if (!target || !rect) return null

  const pad = 8
  const hole = {
    top: rect.top - pad,
    left: rect.left - pad,
    width: rect.width + pad * 2,
    height: rect.height + pad * 2,
  }

  const tooltipTop = hole.top + hole.height + 12
  const tooltipLeft = Math.min(Math.max(hole.left, 12), window.innerWidth - 280)

  return createPortal(
    <div className="fixed inset-0 z-[70]" role="presentation">
      <button
        type="button"
        aria-label="关闭引导提示"
        className="absolute inset-0 bg-[var(--overlay)]"
        onClick={onDismiss}
      />
      <div
        className="pointer-events-none absolute rounded-lg ring-2 ring-[var(--color-accent)] ring-offset-2 ring-offset-transparent"
        style={{
          top: hole.top,
          left: hole.left,
          width: hole.width,
          height: hole.height,
          boxShadow: '0 0 0 9999px rgba(0,0,0,0.45)',
        }}
      />
      <div
        className="absolute z-[71] max-w-[min(18rem,calc(100vw-1.5rem))] rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] p-3 text-sm shadow-lg"
        style={{ top: Math.min(tooltipTop, window.innerHeight - 100), left: tooltipLeft }}
      >
        <p className="leading-relaxed text-[var(--color-text)]">{COACH_MESSAGES[target]}</p>
        {onDismiss ? (
          <button
            type="button"
            className="mt-2 text-xs text-[var(--color-accent)] hover:underline"
            onClick={onDismiss}
          >
            知道了
          </button>
        ) : null}
      </div>
    </div>,
    document.body,
  )
}
