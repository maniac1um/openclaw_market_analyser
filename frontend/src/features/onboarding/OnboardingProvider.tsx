import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from 'react'
import { useLocation, useNavigate, useSearchParams } from 'react-router-dom'
import { toast } from 'sonner'
import { useQuery } from '@tanstack/react-query'
import { useAuth } from '../../lib/AuthContext'
import { api } from '../../lib/api'
import { CoachMark } from './CoachMark'
import { WelcomeGuideDrawer } from './WelcomeGuideDrawer'
import {
  clearOnboardingDone,
  clearOnboardingSnooze,
  isMainFlowComplete,
  isOnboardingDone,
  isOnboardingSnoozed,
  loadOnboardingState,
  markOnboardingDone,
  saveOnboardingState,
  snoozeOnboarding,
} from './storage'
import type { OnboardingPersistedState } from './types'
import {
  ONBOARDING_EVENTS,
  STEP_META,
  type OnboardingCoachTarget,
  type OnboardingStepId,
} from './types'

type OnboardingContextValue = {
  openGuide: () => void
  coachTarget: OnboardingCoachTarget | null
  dismissCoach: () => void
  state: OnboardingPersistedState
}

const OnboardingContext = createContext<OnboardingContextValue | null>(null)

function stepDone(state: OnboardingPersistedState, step: OnboardingStepId): boolean {
  if (step === 'step2') return state.step2Done || state.step2Skipped
  return state[step]
}

export function OnboardingProvider({ children }: { children: ReactNode }) {
  const { user } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const [searchParams, setSearchParams] = useSearchParams()

  const [open, setOpen] = useState(false)
  const [step2Expanded, setStep2Expanded] = useState(false)
  const [state, setState] = useState<OnboardingPersistedState>(() => loadOnboardingState())
  const [coachTarget, setCoachTarget] = useState<OnboardingCoachTarget | null>(null)
  const autoOpenedRef = useRef(false)

  const overviewQuery = useQuery({
    queryKey: ['onboarding-overview'],
    queryFn: api.workOverview,
    enabled: !!user && !user.is_demo,
    refetchInterval: open ? 15_000 : 60_000,
  })

  const workflowQuery = useQuery({
    queryKey: ['onboarding-workflow'],
    queryFn: api.workflowState,
    enabled: !!user && !user.is_demo && open,
    refetchInterval: 15_000,
  })

  const keysQuery = useQuery({
    queryKey: ['api-keys'],
    queryFn: api.listApiKeys,
    enabled: !!user && !user.is_demo && open,
  })

  const finishIfComplete = useCallback((next: OnboardingPersistedState) => {
    if (isMainFlowComplete(next)) {
      markOnboardingDone()
      setOpen(false)
      setCoachTarget(null)
      toast.success('恭喜完成新手引导！')
    }
  }, [])

  const patchState = useCallback((patch: Partial<OnboardingPersistedState>) => {
    setState((prev) => {
      const next = { ...prev, ...patch }
      saveOnboardingState(next)
      finishIfComplete(next)
      return next
    })
  }, [finishIfComplete])

  const syncFromServer = useCallback(() => {
    const overview = overviewQuery.data
    const workflow = workflowQuery.data
    const keys = keysQuery.data

    setState((prev) => {
      const next = { ...prev }
      if ((overview?.price_monitoring?.monitor_count ?? 0) >= 1) next.step1 = true
      if ((overview?.reports?.published_count ?? 0) >= 1) next.step4 = true
      const runs = workflow?.external_scheduler_runs?.length ?? 0
      if (runs > 0) next.step3 = true
      if (keys && keys.length > 0) next.step2Done = true
      saveOnboardingState(next)
      finishIfComplete(next)
      return next
    })
  }, [overviewQuery.data, workflowQuery.data, keysQuery.data, finishIfComplete])

  useEffect(() => {
    if (!user || user.is_demo) return
    syncFromServer()
  }, [user, syncFromServer])

  useEffect(() => {
    if (!user || user.is_demo) return

    const welcome = searchParams.get('welcome') === '1'
    const intent = searchParams.get('intent')
    if (intent === 'api') setStep2Expanded(true)

    if (welcome && !isOnboardingDone() && !isOnboardingSnoozed()) {
      setOpen(true)
      autoOpenedRef.current = true
      const next = new URLSearchParams(searchParams)
      next.delete('welcome')
      next.delete('intent')
      setSearchParams(next, { replace: true })
    }
  }, [user, searchParams, setSearchParams])

  useEffect(() => {
    if (autoOpenedRef.current || !user || user.is_demo) return
    if (isOnboardingDone() || isOnboardingSnoozed()) return
    if (!isMainFlowComplete(loadOnboardingState())) {
      setOpen(true)
      autoOpenedRef.current = true
    }
  }, [user])

  useEffect(() => {
    const onboarding = searchParams.get('onboarding') as OnboardingStepId | null
    if (!onboarding || !STEP_META[onboarding]) return
    const coach = STEP_META[onboarding].coach
    if (coach) {
      const t = window.setTimeout(() => setCoachTarget(coach), 200)
      return () => window.clearTimeout(t)
    }
  }, [location.pathname, searchParams])

  useEffect(() => {
    if (!user || user.is_demo) return

    const onReport = () => patchState({ step4: true })
    const onApiKey = () => patchState({ step2Done: true })

    window.addEventListener(ONBOARDING_EVENTS.reportViewed, onReport)
    window.addEventListener(ONBOARDING_EVENTS.apiKeyCreated, onApiKey)

    return () => {
      window.removeEventListener(ONBOARDING_EVENTS.reportViewed, onReport)
      window.removeEventListener(ONBOARDING_EVENTS.apiKeyCreated, onApiKey)
    }
  }, [user, patchState, finishIfComplete])

  const openGuide = useCallback(() => {
    clearOnboardingDone()
    clearOnboardingSnooze()
    setState(loadOnboardingState())
    setOpen(true)
  }, [])

  const goToStep = useCallback(
    (step: OnboardingStepId) => {
      const meta = STEP_META[step]
      navigate(`${meta.path}?onboarding=${step}`)
      setOpen(false)
      if (meta.coach) {
        window.setTimeout(() => setCoachTarget(meta.coach!), 300)
      }
    },
    [navigate],
  )

  const markStep = useCallback(
    (step: OnboardingStepId) => {
      if (step === 'step1' || step === 'step3' || step === 'step4') {
        patchState({ [step]: true })
      }
    },
    [patchState],
  )

  const skipAll = useCallback(() => {
    markOnboardingDone()
    setOpen(false)
    setCoachTarget(null)
  }, [])

  const snooze = useCallback(() => {
    snoozeOnboarding(24)
    setOpen(false)
    setCoachTarget(null)
  }, [])

  const skipStep2 = useCallback(() => {
    patchState({ step2Skipped: true })
  }, [patchState])

  const value = useMemo(
    () => ({
      openGuide,
      coachTarget,
      dismissCoach: () => setCoachTarget(null),
      state,
    }),
    [openGuide, coachTarget, state],
  )

  if (!user || user.is_demo) {
    return <OnboardingContext.Provider value={null}>{children}</OnboardingContext.Provider>
  }

  return (
    <OnboardingContext.Provider value={value}>
      {children}
      <WelcomeGuideDrawer
        open={open}
        username={user.username}
        state={state}
        step2Expanded={step2Expanded}
        onToggleStep2={() => setStep2Expanded((v) => !v)}
        onClose={() => setOpen(false)}
        onSkip={skipAll}
        onSnooze={snooze}
        onGoToStep={goToStep}
        onMarkStep={markStep}
        onSkipStep2={skipStep2}
      />
      <CoachMark target={coachTarget} onDismiss={() => setCoachTarget(null)} />
    </OnboardingContext.Provider>
  )
}

export function useOnboarding(): OnboardingContextValue {
  const ctx = useContext(OnboardingContext)
  if (!ctx) {
    return {
      openGuide: () => {},
      coachTarget: null,
      dismissCoach: () => {},
      state: loadOnboardingState(),
    }
  }
  return ctx
}

export function useOnboardingActive(): boolean {
  const ctx = useContext(OnboardingContext)
  if (!ctx) return false
  return !isOnboardingDone() && !isMainFlowComplete(ctx.state)
}

export { stepDone }
