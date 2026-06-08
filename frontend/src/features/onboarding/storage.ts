import {
  ONBOARDING_DONE_KEY,
  ONBOARDING_SNOOZE_KEY,
  ONBOARDING_STATE_KEY,
  type OnboardingPersistedState,
} from './types'

const DEFAULT_STATE: OnboardingPersistedState = {
  step1: false,
  step2Done: false,
  step2Skipped: false,
  step3: false,
  step4: false,
}

export function loadOnboardingState(): OnboardingPersistedState {
  try {
    const raw = localStorage.getItem(ONBOARDING_STATE_KEY)
    if (!raw) return { ...DEFAULT_STATE }
    return { ...DEFAULT_STATE, ...JSON.parse(raw) }
  } catch {
    return { ...DEFAULT_STATE }
  }
}

export function saveOnboardingState(state: OnboardingPersistedState) {
  localStorage.setItem(ONBOARDING_STATE_KEY, JSON.stringify(state))
}

export function isOnboardingDone(): boolean {
  return localStorage.getItem(ONBOARDING_DONE_KEY) === '1'
}

export function markOnboardingDone() {
  localStorage.setItem(ONBOARDING_DONE_KEY, '1')
}

export function clearOnboardingDone() {
  localStorage.removeItem(ONBOARDING_DONE_KEY)
}

export function isOnboardingSnoozed(): boolean {
  const raw = localStorage.getItem(ONBOARDING_SNOOZE_KEY)
  if (!raw) return false
  const until = Number(raw)
  return Number.isFinite(until) && until > Date.now()
}

export function snoozeOnboarding(hours = 24) {
  localStorage.setItem(ONBOARDING_SNOOZE_KEY, String(Date.now() + hours * 3600_000))
}

export function clearOnboardingSnooze() {
  localStorage.removeItem(ONBOARDING_SNOOZE_KEY)
}

export function mainProgressCount(state: OnboardingPersistedState): number {
  return [state.step1, state.step3, state.step4].filter(Boolean).length
}

export function isMainFlowComplete(state: OnboardingPersistedState): boolean {
  return state.step1 && state.step3 && state.step4
}
