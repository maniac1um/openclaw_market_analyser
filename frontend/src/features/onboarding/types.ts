export type OnboardingStepId = 'step1' | 'step2' | 'step3' | 'step4'

export type OnboardingCoachTarget =
  | 'monitor-row'
  | 'scheduler-run'
  | 'api-key-create'
  | 'report-detail'

export type OnboardingPersistedState = {
  step1: boolean
  step2Done: boolean
  step2Skipped: boolean
  step3: boolean
  step4: boolean
}

export const ONBOARDING_DONE_KEY = 'onboarding_done'
export const ONBOARDING_DONE_LEGACY_KEY = 'oc_onboarding_done'
export const ONBOARDING_SNOOZE_KEY = 'oc_onboarding_snooze'
export const ONBOARDING_STATE_KEY = 'oc_onboarding_state'

export const MAIN_STEPS: OnboardingStepId[] = ['step1', 'step3', 'step4']

export const STEP_META: Record<
  OnboardingStepId,
  { title: string; description: string; path: string; coach?: OnboardingCoachTarget }
> = {
  step1: {
    title: '创建关键词',
    description: '通过 OpenClaw Agent 或 API 创建价格监测任务。创建成功后将在工作流页显示。',
    path: '/app/workflow',
    coach: 'monitor-row',
  },
  step2: {
    title: '获取 API Key',
    description: '若您通过 OpenClaw Agent / Cursor Skill 自动提交报告，请在此生成 Key 并配置 X-Api-Key。',
    path: '/app/account',
    coach: 'api-key-create',
  },
  step3: {
    title: '查看调度运行',
    description: '在工作流页查看外部调度配置与执行记录，或通过 Agent 配置定时任务。',
    path: '/app/workflow',
    coach: 'scheduler-run',
  },
  step4: {
    title: '查看分析报告',
    description: '在专题分析页打开报告，查看情绪、风险、AI 结论与时间线。',
    path: '/app/reports',
    coach: 'report-detail',
  },
}

export const COACH_MESSAGES: Record<OnboardingCoachTarget, string> = {
  'monitor-row': '点击监测任务行查看详情与执行状态',
  'scheduler-run': '点击执行记录查看最近运行详情',
  'api-key-create': '可选：生成 API Key 供 OpenClaw Agent 使用',
  'report-detail': '点击左侧报告查看详细分析',
}

export const ONBOARDING_EVENTS = {
  reportViewed: 'onboarding:report_viewed',
  apiKeyCreated: 'onboarding:api_key_created',
} as const
