import { useMutation, useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { toast } from 'sonner'
import { Button } from '../components/ui/Button'
import { useAuth } from '../lib/AuthContext'
import { api, type Payment } from '../lib/api'

function formatTokens(value: number | undefined): string {
  if (value == null) return '—'
  return value.toLocaleString()
}

function planLabel(plan: string | undefined): string {
  if (plan === 'pro') return 'Pro'
  return 'Free'
}

const POLL_INTERVAL_MS = 500
const POLL_TIMEOUT_MS = 15_000

async function pollPaymentUntilDone(paymentId: string): Promise<Payment> {
  const deadline = Date.now() + POLL_TIMEOUT_MS
  while (Date.now() < deadline) {
    const payment = await api.getPayment(paymentId)
    if (payment.status === 'success' || payment.status === 'failed') {
      return payment
    }
    await new Promise((resolve) => setTimeout(resolve, POLL_INTERVAL_MS))
  }
  throw new Error('支付状态查询超时，请稍后刷新余额')
}

export function BillingPage() {
  const { user, refreshUser } = useAuth()
  const isDemo = user?.is_demo

  const subscriptionQuery = useQuery({
    queryKey: ['subscription'],
    queryFn: () => api.getSubscription(),
  })

  const balanceQuery = useQuery({
    queryKey: ['user-balance'],
    queryFn: () => api.getUserBalance(),
  })

  const usageQuery = useQuery({
    queryKey: ['usage-stats', '30d'],
    queryFn: () => api.usageStats('30d'),
  })

  const upgradeMutation = useMutation({
    mutationFn: () => api.upgradeSubscription(),
    onSuccess: async () => {
      await subscriptionQuery.refetch()
      await balanceQuery.refetch()
      await refreshUser()
      toast.success('已升级为 Pro')
    },
    onError: (err: Error) => toast.error(err.message),
  })

  const rechargeMutation = useMutation({
    mutationFn: async () => {
      const order = await api.createPayment()
      await api.confirmPayment(order.id)
      return pollPaymentUntilDone(order.id)
    },
    onSuccess: async (payment) => {
      if (payment.status === 'failed') {
        toast.error('支付失败，请重试')
        return
      }
      await balanceQuery.refetch()
      await refreshUser()
      toast.success(`已充值 +${payment.tokens.toLocaleString()} tokens`)
    },
    onError: (err: Error) => toast.error(err.message),
  })

  const plan = subscriptionQuery.data?.plan ?? 'free'
  const isPro = plan === 'pro' && subscriptionQuery.data?.status === 'active'
  const balance = balanceQuery.data?.balance
  const monthlyUsage = usageQuery.data?.range_total

  return (
    <div className="mx-auto flex w-full max-w-lg flex-col gap-6">
      <header className="border-b border-[var(--ds-border)] pb-4">
        <h1 className="text-lg font-semibold text-[var(--ds-text-primary)]">订阅与充值</h1>
      </header>

      <div className="flex flex-col gap-1">
        <span className="text-xs text-[var(--ds-text-secondary)]">当前计划</span>
        <p className="text-2xl font-semibold text-[var(--ds-text-primary)]">
          {subscriptionQuery.isLoading ? '…' : planLabel(plan)}
        </p>
        {subscriptionQuery.data?.status === 'cancelled' && (
          <p className="text-xs text-[var(--ds-text-secondary)]">已取消续订</p>
        )}
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        <div>
          <p className="text-xs text-[var(--ds-text-secondary)]">当前 Token</p>
          <p className="mt-1 text-2xl font-semibold tabular-nums text-[var(--ds-text-primary)]">
            {balanceQuery.isLoading ? '…' : formatTokens(balance)}
          </p>
        </div>
        <div>
          <p className="text-xs text-[var(--ds-text-secondary)]">本月使用量</p>
          <p className="mt-1 text-2xl font-semibold tabular-nums text-[var(--ds-text-primary)]">
            {usageQuery.isLoading ? '…' : formatTokens(monthlyUsage)}
          </p>
        </div>
      </div>

      <div className="flex flex-col gap-3 border-t border-[var(--ds-border)] pt-4">
        {!isPro && (
          <Button
            variant="primary"
            className="h-10 w-full text-sm"
            disabled={isDemo || upgradeMutation.isPending}
            onClick={() => upgradeMutation.mutate()}
          >
            {upgradeMutation.isPending ? '处理中…' : '升级 Pro'}
          </Button>
        )}

        <Button
          variant="secondary"
          className="h-10 w-full text-sm"
          disabled={isDemo || rechargeMutation.isPending}
          onClick={() => rechargeMutation.mutate()}
        >
          {rechargeMutation.isPending ? '处理中…' : '充值 +1,000 tokens'}
        </Button>

        {isDemo && (
          <p className="text-xs text-amber-500">演示账号为只读，请注册正式账号后充值或升级。</p>
        )}
        {!isDemo && (
          <p className="text-xs text-[var(--ds-text-secondary)]">
            模拟充值：创建订单后自动确认到账（非真实支付）。
          </p>
        )}
      </div>

      <p className="text-xs text-[var(--ds-text-secondary)]">
        <Link to="/app/usage" className="text-[var(--color-accent)] hover:underline">
          查看使用明细
        </Link>
      </p>
    </div>
  )
}
