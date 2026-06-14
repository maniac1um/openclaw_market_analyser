import { ChevronDown, ChevronRight, X } from 'lucide-react'
import { cn } from '../../lib/utils'
import { Button } from '../../components/ui/Button'
import { useIsMdUp } from '../../lib/useMediaQuery'
import { MAIN_STEPS, STEP_META, type OnboardingStepId } from './types'
import { mainProgressCount } from './storage'
import type { OnboardingPersistedState } from './types'

type Props = {
  open: boolean
  username: string
  state: OnboardingPersistedState
  step2Expanded: boolean
  onToggleStep2: () => void
  onClose: () => void
  onSkip: () => void
  onSnooze: () => void
  onGoToStep: (step: OnboardingStepId) => void
  onMarkStep: (step: OnboardingStepId) => void
  onSkipStep2: () => void
}

function mainStepDone(state: OnboardingPersistedState, stepId: 'step1' | 'step3' | 'step4'): boolean {
  if (stepId === 'step1') return state.step1
  if (stepId === 'step3') return state.step3
  return state.step4
}

function StepRow({
  stepId,
  done,
  optional,
  onGo,
  onMark,
}: {
  stepId: OnboardingStepId
  done: boolean
  optional?: boolean
  onGo: () => void
  onMark?: () => void
}) {
  const meta = STEP_META[stepId]
  return (
    <div className="rounded-lg border border-[var(--color-border)] p-3">
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0">
          <p className="text-xs font-medium text-[var(--color-accent)]">
            {stepId.replace('step', 'Step ')}
            {optional ? ' · 可选' : ''}
          </p>
          <p className="mt-0.5 font-medium">{meta.title}</p>
          <p className="mt-1 text-xs leading-relaxed text-[var(--color-muted)]">{meta.description}</p>
        </div>
        <span
          className={cn(
            'shrink-0 rounded-full px-2 py-0.5 text-[10px] font-medium',
            done ? 'bg-green-100 text-green-700 dark:bg-green-950 dark:text-green-400' : 'bg-[var(--color-border)] text-[var(--color-muted)]',
          )}
        >
          {done ? '已完成' : '未完成'}
        </span>
      </div>
      {!done && (
        <div className="mt-3 flex flex-wrap gap-2">
          <Button variant="primary" className="h-8 text-xs" onClick={onGo}>
            去完成 →
          </Button>
          {onMark ? (
            <Button variant="ghost" className="h-8 text-xs" onClick={onMark}>
              标记完成
            </Button>
          ) : null}
        </div>
      )}
    </div>
  )
}

function PanelContent(props: Props) {
  const progress = mainProgressCount(props.state)

  return (
    <>
      <div className="flex items-start justify-between gap-3 border-b border-[var(--color-border)] px-4 py-4">
        <div>
          <h2 className="text-base font-semibold">欢迎使用 OpenClaw，{props.username}！</h2>
          <p className="mt-1 text-sm text-[var(--color-muted)]">按以下 3 步快速上手，约需 10 分钟</p>
        </div>
        <button
          type="button"
          onClick={props.onClose}
          className="rounded-md p-1 text-[var(--color-muted)] hover:bg-[var(--color-bg)]"
          aria-label="关闭引导"
        >
          <X className="h-4 w-4" />
        </button>
      </div>

      <div className="flex-1 space-y-3 overflow-y-auto px-4 py-4">
        {MAIN_STEPS.map((stepId) => (
          <StepRow
            key={stepId}
            stepId={stepId}
            done={mainStepDone(props.state, stepId as 'step1' | 'step3' | 'step4')}
            onGo={() => props.onGoToStep(stepId)}
            onMark={stepId === 'step1' || stepId === 'step3' ? () => props.onMarkStep(stepId) : undefined}
          />
        ))}

        <div className="rounded-lg border border-dashed border-[var(--color-border)]">
          <button
            type="button"
            className="flex w-full items-center gap-2 px-3 py-2.5 text-left text-sm font-medium text-[var(--color-muted)] hover:text-[var(--color-text)]"
            onClick={props.onToggleStep2}
          >
            {props.step2Expanded ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
            高级 · 可选 — Step 2 获取 API Key
          </button>
          {props.step2Expanded ? (
            <div className="border-t border-[var(--color-border)] p-3 pt-0">
              <StepRow
                stepId="step2"
                done={props.state.step2Done || props.state.step2Skipped}
                optional
                onGo={() => props.onGoToStep('step2')}
              />
              {!props.state.step2Done && !props.state.step2Skipped && (
                <Button variant="ghost" className="mt-2 h-8 w-full text-xs" onClick={props.onSkipStep2}>
                  暂不需要，跳过此步
                </Button>
              )}
            </div>
          ) : null}
        </div>
      </div>

      <div className="border-t border-[var(--color-border)] px-4 py-4">
        <div className="mb-3 flex items-center justify-between text-xs text-[var(--color-muted)]">
          <span>进度</span>
          <span>
            {progress}/3
          </span>
        </div>
        <div className="mb-4 h-1.5 overflow-hidden rounded-full bg-[var(--color-border)]">
          <div
            className="h-full rounded-full bg-[var(--color-accent)] transition-all"
            style={{ width: `${(progress / 3) * 100}%` }}
          />
        </div>
        <div className="flex flex-wrap gap-2">
          <Button variant="ghost" className="h-8 text-xs" onClick={props.onSnooze}>
            稍后提醒
          </Button>
          <Button variant="ghost" className="h-8 text-xs" onClick={props.onSkip}>
            跳过引导
          </Button>
        </div>
      </div>
    </>
  )
}

export function WelcomeGuideDrawer(props: Props) {
  const isMdUp = useIsMdUp()
  if (!props.open) return null

  if (isMdUp) {
    return (
      <aside className="fixed bottom-0 right-0 top-14 z-[60] flex w-[min(22rem,100vw)] flex-col border-l border-[var(--color-border)] bg-[var(--color-surface)] shadow-xl">
        <PanelContent {...props} />
      </aside>
    )
  }

  return (
    <>
      <button
        type="button"
        aria-label="关闭引导"
        className="fixed inset-0 z-[59] bg-[var(--overlay)]"
        onClick={props.onClose}
      />
      <div className="fixed inset-x-0 bottom-0 z-[60] flex max-h-[min(85dvh,640px)] flex-col rounded-t-2xl border border-[var(--color-border)] bg-[var(--color-surface)] shadow-2xl pb-[env(safe-area-inset-bottom)]">
        <div className="flex justify-center py-2">
          <div className="h-1 w-10 rounded-full bg-[var(--color-border)]" />
        </div>
        <PanelContent {...props} />
      </div>
    </>
  )
}
