import { Link } from 'react-router-dom'
import {
  FileText,
  LineChart,
  MessageSquare,
  Newspaper,
  Settings,
  Tags,
} from 'lucide-react'
import { useEffect, useState } from 'react'
import { Button } from '../components/ui/Button'
import { Badge } from '../components/ui/Badge'
import { Card, CardContent } from '../components/ui/Card'
import { ThemeToggle } from '../components/ui/ThemeToggle'
import { DemoReportPreview } from '../features/landing/DemoReportPreview'
import { DemoPriceChart } from '../features/landing/DemoPriceChart'
import { loadDemoPriceTrend, type DemoPriceTrend } from '../features/landing/demoData'
import { formatCnDateTime } from '../lib/utils'

const features = [
  {
    icon: MessageSquare,
    title: 'OpenClaw AI 对话',
    desc: '向 AI 提问市场分析、关键词追踪或研究任务',
  },
  {
    icon: FileText,
    title: '专题分析',
    desc: '情绪、风险、市场影响、置信度与 AI 结论',
  },
  {
    icon: LineChart,
    title: '价格趋势',
    desc: '关键词价格监测，多时间窗趋势与采集明细',
  },
  {
    icon: Newspaper,
    title: '新闻动态',
    desc: '按关键词沉淀的新闻库与摘要',
  },
  {
    icon: Tags,
    title: '关键词追踪',
    desc: '监测任务、新闻、报告的统一关键词视图',
  },
  {
    icon: Settings,
    title: '工作流',
    desc: '查看监测任务、调度配置与执行记录',
  },
]

const quickSteps = [
  { n: 1, title: '创建关键词', desc: '通过 OpenClaw Agent 或 API 创建监测任务' },
  { n: 2, title: '获取 API Key', desc: '可选 · Agent 自动入库集成', optional: true },
  { n: 3, title: '查看调度运行', desc: '在工作流页查看外部调度与执行记录' },
  { n: 4, title: '查看分析报告', desc: '在专题分析页阅读 AI 研判' },
]

function LandingHeader() {
  return (
    <header className="sticky top-0 z-40 border-b border-[var(--border-solid)] bg-background/90 backdrop-blur">
      <div className="mx-auto flex max-w-6xl items-center justify-between gap-4 px-4 py-3">
        <Link to="/" className="text-sm font-semibold tracking-tight text-primary">
          OpenClaw 分析平台
        </Link>
        <nav className="hidden items-center gap-6 text-sm text-[var(--text-secondary)] md:flex">
          <a href="#features" className="hover:text-primary">
            功能
          </a>
          <a href="#sample-report" className="hover:text-primary">
            示例
          </a>
          <a href="/docs" className="hover:text-primary">
            文档
          </a>
        </nav>
        <div className="flex items-center gap-2">
          <ThemeToggle />
          <Link to="/login?demo=1">
            <Button variant="secondary">试用登录</Button>
          </Link>
          <Link to="/login">
            <Button variant="secondary">登录</Button>
          </Link>
          <Link to="/register">
            <Button variant="primary">免费注册</Button>
          </Link>
        </div>
      </div>
    </header>
  )
}

export function LandingPage() {
  const [priceDemo, setPriceDemo] = useState<DemoPriceTrend | null>(null)

  useEffect(() => {
    void loadDemoPriceTrend().then(setPriceDemo)
  }, [])

  return (
    <div className="min-h-screen bg-background text-primary">
      <LandingHeader />

      <main>
        {/* Hero */}
        <section className="mx-auto max-w-6xl px-4 py-16 sm:py-24">
          <div className="max-w-2xl">
            <Badge variant="muted" className="mb-4">
              市场趋势分析平台
            </Badge>
            <h1 className="text-3xl font-semibold tracking-tight sm:text-4xl">
              OpenClaw 市场趋势分析平台
            </h1>
            <p className="mt-4 text-lg text-[var(--color-muted)]">
              追踪关键词、汇聚新闻、生成 AI 专题报告，并用图表呈现价格走势。无需 Agent 也可在门户创建工作流；Agent 可自动入库。
            </p>
            <div className="mt-8 flex flex-wrap gap-3">
              <Link to="/register">
                <Button variant="primary" className="px-5 py-2.5">
                  免费开始使用
                </Button>
              </Link>
              <a href="#sample-report">
                <Button variant="secondary" className="px-5 py-2.5">
                  查看示例报告
                </Button>
              </a>
              <Link to="/login?demo=1">
                <Button variant="secondary" className="px-5 py-2.5">
                  试用登录
                </Button>
              </Link>
            </div>
            <ul className="mt-8 space-y-2 text-sm text-[var(--color-muted)]">
              <li>· 多用户数据隔离</li>
              <li>· 情绪 / 风险 / 置信度结构化研判</li>
              <li>· 支持 OpenClaw Agent 自动入库</li>
            </ul>
          </div>
        </section>

        {/* Features */}
        <section id="features" className="border-t border-[var(--color-border)] bg-[var(--color-surface)] py-16">
          <div className="mx-auto max-w-6xl px-4">
            <h2 className="text-xl font-semibold">核心功能</h2>
            <p className="mt-2 text-sm text-[var(--color-muted)]">注册后即可在门户中使用以下模块</p>
            <div className="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {features.map(({ icon: Icon, title, desc }) => (
                <Card key={title}>
                  <CardContent className="p-5">
                    <div className="mb-3 flex h-10 w-10 items-center justify-center rounded-lg bg-[var(--color-accent-soft)] text-[var(--color-accent)]">
                      <Icon className="h-5 w-5" />
                    </div>
                    <h3 className="font-medium">{title}</h3>
                    <p className="mt-1 text-sm text-[var(--color-muted)]">{desc}</p>
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>
        </section>

        {/* Sample report */}
        <section id="sample-report" className="py-16">
          <div className="mx-auto max-w-6xl px-4">
            <div className="mb-8 flex flex-wrap items-end justify-between gap-4">
              <div>
                <h2 className="text-xl font-semibold">示例报告</h2>
                <p className="mt-2 text-sm text-[var(--color-muted)]">
                  完全虚构的演示内容 · 注册后可生成真实报告
                </p>
              </div>
              <Link to="/register?intent=report">
                <Button variant="primary">注册并创建第一份报告</Button>
              </Link>
            </div>
            <DemoReportPreview />
          </div>
        </section>

        {/* Price trend */}
        <section id="price-demo" className="border-t border-[var(--color-border)] bg-[var(--color-surface)] py-16">
          <div className="mx-auto max-w-6xl px-4">
            <div className="mb-8 flex flex-wrap items-end justify-between gap-4">
              <div>
                <h2 className="text-xl font-semibold">价格趋势示例</h2>
                <p className="mt-2 text-sm text-[var(--color-muted)]">
                  以上为完全虚构的演示数据，不代表任何真实商品或行情
                </p>
              </div>
              <Link to="/register">
                <Button variant="primary">免费注册体验</Button>
              </Link>
            </div>
            {priceDemo ? (
              <>
                <div className="mb-6 grid gap-4 sm:grid-cols-3">
                  <Card>
                    <CardContent className="p-4">
                      <p className="text-xs text-[var(--color-muted)]">观测数</p>
                      <p className="text-2xl font-semibold">{priceDemo.observation_count}</p>
                    </CardContent>
                  </Card>
                  <Card>
                    <CardContent className="p-4">
                      <p className="text-xs text-[var(--color-muted)]">URL 数</p>
                      <p className="text-2xl font-semibold">{priceDemo.url_count}</p>
                    </CardContent>
                  </Card>
                  <Card>
                    <CardContent className="p-4">
                      <p className="text-xs text-[var(--color-muted)]">最近采集</p>
                      <p className="text-sm font-medium">{formatCnDateTime(priceDemo.last_captured_at)}</p>
                    </CardContent>
                  </Card>
                </div>
                <Card>
                  <CardContent className="p-4">
                    <p className="mb-4 text-sm font-medium">
                      价格趋势 · <Badge>{priceDemo.keyword}</Badge>
                    </p>
                    <DemoPriceChart data={priceDemo} />
                  </CardContent>
                </Card>
                <div className="mt-6 overflow-x-auto rounded-lg border border-[var(--color-border)]">
                  <table className="w-full min-w-[480px] text-sm">
                    <thead>
                      <tr className="border-b border-[var(--color-border)] bg-[var(--color-bg)] text-left text-[var(--color-muted)]">
                        <th className="px-4 py-2 font-medium">商品</th>
                        <th className="px-4 py-2 font-medium">时间</th>
                        <th className="px-4 py-2 font-medium">价格</th>
                        <th className="px-4 py-2 font-medium">涨跌</th>
                      </tr>
                    </thead>
                    <tbody>
                      {priceDemo.rows.map((row, i) => (
                        <tr key={i} className="border-b border-[var(--color-border)] last:border-0">
                          <td className="px-4 py-2">{row.item_name}</td>
                          <td className="px-4 py-2 text-[var(--color-muted)]">{formatCnDateTime(row.captured_at)}</td>
                          <td className="px-4 py-2">¥{row.price.toFixed(1)}</td>
                          <td
                            className={
                              row.delta_from_prev == null
                                ? 'px-4 py-2 text-[var(--color-muted)]'
                                : row.delta_from_prev >= 0
                                  ? 'px-4 py-2 text-[var(--color-success)]'
                                  : 'px-4 py-2 text-[var(--color-danger)]'
                            }
                          >
                            {row.delta_from_prev == null
                              ? '—'
                              : `${row.delta_from_prev >= 0 ? '+' : ''}${row.delta_from_prev.toFixed(1)}`}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </>
            ) : null}
          </div>
        </section>

        {/* Quick start */}
        <section id="quick-start" className="py-16">
          <div className="mx-auto max-w-6xl px-4">
            <h2 className="text-xl font-semibold">快速上手</h2>
            <p className="mt-2 text-sm text-[var(--color-muted)]">约 10 分钟完成首个分析闭环（主流程 3 步，API Key 可选）</p>
            <div className="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
              {quickSteps.map((step) => (
                <Card key={step.n} className={step.optional ? 'opacity-80' : undefined}>
                  <CardContent className="p-5">
                    <p className="text-xs font-medium text-[var(--color-accent)]">
                      Step {step.n}
                      {step.optional ? ' · 可选' : ''}
                    </p>
                    <h3 className="mt-1 font-medium">{step.title}</h3>
                    <p className="mt-1 text-sm text-[var(--color-muted)]">{step.desc}</p>
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>
        </section>

        {/* Footer CTA */}
        <section className="border-t border-[var(--color-border)] bg-[var(--color-accent-soft)] py-16">
          <div className="mx-auto max-w-6xl px-4 text-center">
            <h2 className="text-xl font-semibold">准备好开始了吗？</h2>
            <p className="mt-2 text-sm text-[var(--color-muted)]">免费注册，或先试用演示账号体验完整界面</p>
            <div className="mt-6 flex flex-wrap justify-center gap-3">
              <Link to="/register">
                <Button variant="primary" className="px-6 py-2.5">
                  立即注册 — 免费
                </Button>
              </Link>
              <Link to="/login?demo=1">
                <Button variant="secondary" className="px-6 py-2.5">
                  试用登录
                </Button>
              </Link>
            </div>
            <p className="mt-4 text-sm text-[var(--color-muted)]">
              已有账号？{' '}
              <Link to="/login" className="text-[var(--color-accent)] hover:underline">
                登录
              </Link>
            </p>
          </div>
        </section>
      </main>

      <footer className="border-t border-[var(--color-border)] py-8 text-center text-xs text-[var(--color-muted)]">
        OpenClaw 市场趋势分析平台 · 示例数据均为虚构
      </footer>
    </div>
  )
}
