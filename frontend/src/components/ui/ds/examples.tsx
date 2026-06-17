/**
 * Design system usage examples — import individually for reference or Storybook.
 * Not wired to any route.
 */
import { useState } from 'react'
import { Search, Trash2 } from 'lucide-react'
import { Panel } from './Panel'
import { StatStrip, StatStripItem } from './StatStrip'
import { DataRow } from './DataRow'
import { Drawer } from './Drawer'
import { Section } from './Section'
import { CommandBar, CommandBarButton, CommandBarInput } from './CommandBar'

export function PanelExample() {
  return (
    <Panel>
      <p className="text-sm text-[var(--ds-text-primary)]">Panel 内容区域，带 border + backdrop-blur，无阴影。</p>
    </Panel>
  )
}

export function StatStripExample() {
  return (
    <StatStrip>
      <StatStripItem label="观测数" value={1247} trend={{ value: '12%', direction: 'up' }} />
      <StatStripItem label="URL 数" value={3} />
      <StatStripItem label="最近采集" value="2 小时前" trend={{ value: '3.2%', direction: 'down' }} />
    </StatStrip>
  )
}

export function DataRowExample() {
  return (
    <Section title="报告列表">
      <DataRow
        title="铜价短期震荡，关注库存变化"
        subtitle="铜 · 2026-06-14 10:30"
        meta="偏多"
        onClick={() => {}}
      />
      <DataRow
        title="原油价格回落，需求预期下调"
        subtitle="原油 · 2026-06-13 18:00"
        meta="偏空"
        onClick={() => {}}
      />
    </Section>
  )
}

export function DrawerExample() {
  const [open, setOpen] = useState(false)

  return (
    <>
      <button
        type="button"
        onClick={() => setOpen(true)}
        className="text-sm text-[var(--color-accent)]"
      >
        打开 Drawer
      </button>
      <Drawer open={open} onClose={() => setOpen(false)} title="报告详情">
        <p className="text-sm text-[var(--ds-text-secondary)]">Drawer 从右侧滑入，宽度 480px，不阻塞页面交互。</p>
      </Drawer>
    </>
  )
}

export function SectionExample() {
  return (
    <Section title="相关新闻" description="最近 6 条关联报道" action={<span className="text-xs text-[var(--ds-text-secondary)]">查看全部</span>}>
      <DataRow title="LME 铜库存连续三周下降" subtitle="Reuters" meta="2h ago" onClick={() => {}} />
      <DataRow title="智利矿山产量超预期" subtitle="Bloomberg" meta="5h ago" onClick={() => {}} />
    </Section>
  )
}

export function CommandBarExample() {
  return (
    <CommandBar>
      <CommandBarInput placeholder="搜索关键词…" aria-label="搜索" />
      <CommandBarButton aria-label="搜索">
        <Search className="h-4 w-4" />
      </CommandBarButton>
      <CommandBarButton variant="danger" aria-label="批量删除">
        <Trash2 className="h-4 w-4" />
        删除
      </CommandBarButton>
    </CommandBar>
  )
}

/** Combined showcase for local dev / preview */
export function DesignSystemShowcase() {
  return (
    <div className="space-y-12 bg-[var(--ds-bg-base)] p-8">
      <Section title="Panel">
        <PanelExample />
      </Section>
      <Section title="StatStrip">
        <Panel>
          <StatStripExample />
        </Panel>
      </Section>
      <Section title="DataRow">
        <Panel className="p-0">
          <DataRowExample />
        </Panel>
      </Section>
      <Section title="CommandBar">
        <CommandBarExample />
      </Section>
      <Section title="Drawer">
        <DrawerExample />
      </Section>
    </div>
  )
}
