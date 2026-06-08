# OpenClaw 前端可视化优化方案

**角色**：Frontend Visualization Agent  
**日期**：2026-06-08  
**范围**：工作流页面 · Markdown 渲染 · 价格趋势图  
**约束**：本文档为设计方案；删除指定 UI 入口时**保留全部后端接口与实现**，不改动 `app/` 后端代码。

---

## 1. 执行摘要

当前前端在三个核心可视化场景存在明显缺口：

| 场景 | 现状 | 目标 |
|------|------|------|
| **Markdown** | 仅 `ReportDetail.tsx` 内联 `ReactMarkdown`；聊天、新闻摘要、`report_markdown` 字段未渲染 | 统一 `MarkdownContent` 组件，支持 GFM 表格/代码块/标题/引用 |
| **工作流** | 单文件 `WorkflowPage.tsx`，含创建监测与联合分析表单；无任务详情弹窗 | 模块化 `components/workflow/`，新增 **Workflow Details Modal**（任务详情 + 执行记录 + 状态） |
| **价格趋势** | 内联 Canvas，固定 30 日日均聚合；无交互 | 抽取 `components/charts/`，展示**全部观测点**，支持 8 档时间窗 + 缩放/拖动/悬停 |

同时从 UI 层**移除**「创建监测任务」「触发联合分析」入口（Landing、Onboarding、空状态文案一并调整），`api.workflowBootstrap` / `api.workflowAnalysis` 保留供 Agent / API 调用。

---

## 2. 现状审计

### 2.1 目录结构（当前）

```
frontend/src/
├── pages/
│   ├── WorkflowPage.tsx          # 工作流（单体，含待删 UI）
│   └── PriceTrendPage.tsx        # 价格趋势（内联 Canvas）
├── features/
│   ├── reports/ReportDetail.tsx  # 唯一 Markdown 渲染点
│   ├── chat/ChatPage.tsx         # 助手消息纯文本
│   └── landing/DemoPriceChart.tsx # 与 PriceTrendPage 重复的 Canvas 逻辑
└── components/
    ├── ui/                       # 基础 UI（无 Modal 组件）
    └── layout/AppShell.tsx
```

**缺失目录**（本方案新建）：

- `frontend/src/components/markdown/`
- `frontend/src/components/workflow/`
- `frontend/src/components/charts/`

### 2.2 Markdown 渲染审计

| 位置 | 文件 | 当前渲染方式 | 是否缺失 Markdown |
|------|------|--------------|-------------------|
| 报告 AI 结论 | `features/reports/ReportDetail.tsx` | `ReactMarkdown` + `remarkGfm` + `.prose-report` | ✅ 已渲染（但未抽取为共享组件） |
| 报告完整正文 | 同上 | 仅用 `report.analysis`；**忽略** `report.report_markdown` | ⚠️ 字段未使用 |
| AI 对话助手消息 | `features/chat/ChatPage.tsx` `MessageBubble` | `whitespace-pre-wrap` 纯文本 | ❌ 缺失 |
| 新闻摘要 | `ReportDetail.tsx` / `NewsPage.tsx` | 纯文本 `line-clamp` | ⚠️ 若含 Markdown 则缺失（低优先级） |
| Landing 示例报告 | `features/landing/DemoReportPreview.tsx` | 复用 `ReportDetailView` | 间接依赖 ReportDetail |
| Topic Cards API | `api.topicCards()` | 前端未消费 | N/A |

**已有基础设施**：

- 依赖：`react-markdown@10`、`remark-gfm@4`（`package.json`）
- 样式：`.prose-report` 在 `index.css`（h1–h3、p、ul、a、code、pre、table）
- 安全：`lib/urlSafety.ts` 中 `markdownUrlTransform` / `safeExternalHref`

**样式缺口**（统一组件时需补全）：

- `blockquote`（引用块）
- `table` 的 `th`/`td` 边框与斑马纹
- `h4`–`h6`
- `ol` 有序列表
- `hr`、删除线等 GFM 扩展

### 2.3 工作流页面审计

**数据流**（`WorkflowPage.tsx`）：

```
api.workflowState()  → overview / gateway / internal_scheduler / external_scheduler_*
api.workflowDiagnostics() → checks[]
```

**现有区块**：

1. 概览卡片（Gateway、报告数、监测任务数、外部调度数）
2. **创建监测任务**（`api.workflowBootstrap`）— **待删除 UI**
3. **触发联合分析**（`api.workflowAnalysis`）— **待删除 UI**
4. 系统诊断列表
5. 最近调度运行（`external_scheduler_runs` 前 8 条，无详情弹窗）

**后端可用字段**（`WorkflowState` / 关联 API）：

| 数据源 | 字段 | 用途 |
|--------|------|------|
| `overview.price_monitoring.recent` | `monitor_id`, `keyword`, `observation_count`, `last_captured_at` | 监测任务列表 |
| `external_scheduler_configs` | `job_name`, `monitor_id`, `cron_expr`, `enabled`, … | 调度配置 |
| `external_scheduler_runs` | `job_name`, `status`, `monitor_id`, `message`, `last_seen_at` | 执行记录 |
| `internal_scheduler` | `enabled`, `started`, `interval_minutes`, … | 内置调度状态 |
| `api.listMonitors()` | 完整监测列表 | Modal 任务详情补充 |

**缺口**：

- 无任务/作业维度的详情视图
- 运行记录与监测任务未关联（无法从任务行点开 Modal）
- 无通用 Modal/Dialog 基础组件

### 2.4 价格趋势图审计

**当前实现**（`PriceTrendPage.tsx` + `DemoPriceChart.tsx`）：

- 原生 `<canvas>` 手绘折线 + 面积填充
- 数据源：`api.timeseries(monitorId, 30)` → **按日 `DATE_TRUNC` 聚合**，非原始观测点
- 观测明细表：`api.observations(monitorId, 100)` → 与图表数据**未联动**
- 固定标题「30 日均价趋势」，无时间窗切换
- **无**缩放、拖动、悬停 Tooltip
- 深色模式通过 `document.documentElement.classList` 读取，逻辑重复两份

**后端 API 能力**：

```
GET /api/v1/public/monitoring/{id}/timeseries?window_days=1..365  # 日聚合
GET /api/v1/public/monitoring/{id}/observations?limit=1..1000     # 原始点，ASC 排序
```

| 时间窗 | 日聚合 timeseries | 原始 observations |
|--------|-------------------|-------------------|
| 1h / 6h / 24h | ❌ 粒度太粗（按天） | ✅ 前端按 `captured_at` 过滤 |
| 7d / 30d / 90d | ✅ `window_days` 参数 | ✅ 可叠加显示每点 |
| All | ✅ `window_days=365`（上限） | ⚠️ `limit` 上限 1000，超量需分页或后端扩展 |

**结论**：「显示所有观测点」应以 **`observations` 为主数据源**；长周期可保留日聚合作为性能降级层，但默认展示原始点。短周期（1h–24h）必须走 observations 客户端过滤。

---

## 3. Markdown 统一方案

### 3.1 新建共享组件

```
frontend/src/components/markdown/
├── MarkdownContent.tsx    # 统一入口
└── markdown.css           # 或扩展现有 .prose-report → .prose-markdown
```

**`MarkdownContent` 接口**：

```tsx
type MarkdownContentProps = {
  children: string
  className?: string
  /** 默认 true；聊天场景可关闭部分块级样式 */
  compact?: boolean
}
```

**实现要点**：

- `ReactMarkdown` + `remarkPlugins={[remarkGfm]}`
- `urlTransform={markdownUrlTransform}`（复用 `lib/urlSafety.ts`）
- 外链 `<a>` 统一 `target="_blank" rel="noreferrer"`
- 代码块：`<pre><code>` 保持 `.prose-markdown pre` 暗色背景
- GFM 表格：`<table>` 包裹 `overflow-x-auto` 容器（移动端横向滚动）
- 引用：`blockquote` 左边框 + 浅色背景

### 3.2 迁移清单

| 优先级 | 文件 | 改动 |
|--------|------|------|
| P0 | `features/reports/ReportDetail.tsx` | 替换内联 `ReactMarkdown` → `<MarkdownContent>`；优先渲染 `report_markdown \|\| report.analysis` |
| P0 | `features/chat/ChatPage.tsx` | 助手 `MessageBubble` 使用 `<MarkdownContent compact>` |
| P1 | `index.css` | `.prose-report` 重命名或别名至 `.prose-markdown`，补全 blockquote / table / ol 样式 |
| P2 | `pages/NewsPage.tsx` | 详情区 `summary` 若检测到 Markdown 特征再渲染（可选） |

### 3.3 支持矩阵

| Markdown 特性 | remark-gfm | 样式类 |
|---------------|------------|--------|
| 标题 h1–h6 | ✅ | `.prose-markdown h1`… |
| 段落 / 换行 | ✅ | `p` |
| **GFM 表格** | ✅ | `table`, `th`, `td` |
| **代码块** | ✅ | `pre`, `code` |
| 行内代码 | ✅ | `code` |
| **引用** | ✅ | `blockquote`（需新增样式） |
| 列表 ul/ol | ✅ | `ul`, `ol` |
| 链接 | ✅ | `a` + urlTransform |
| 删除线 / 任务列表 | ✅ GFM | 按需补样式 |

---

## 4. 工作流页面重构

### 4.1 目标信息架构

```
工作流控制台
├── 概览指标条（保留）
├── 监测任务列表（新：可点击行 → Modal）
├── 外部调度配置列表（新：可点击 → Modal）
├── 最近执行记录（增强：状态徽章 + 点击查看详情）
└── 系统诊断（保留）
```

**移除**：

- 「创建监测任务」Card 整块（含 `keyword` state、`bootstrapMutation`、`data-onboarding="monitor-keyword"`）
- 「触发联合分析」Card 整块（含 `monitorId` state、`analysisMutation`、`data-onboarding="analysis-run"`）

**保留于 `lib/api.ts`（不删）**：

- `api.workflowBootstrap`
- `api.workflowAnalysis`

### 4.2 组件拆分

```
frontend/src/components/workflow/
├── WorkflowOverviewCards.tsx      # 顶部 4 指标卡
├── MonitorTaskTable.tsx           # 监测任务表
├── SchedulerConfigTable.tsx       # 外部调度配置表
├── SchedulerRunList.tsx           # 最近执行记录
├── WorkflowDiagnosticsPanel.tsx   # 诊断（从 WorkflowPage 抽出）
├── WorkflowDetailsModal.tsx       # ★ 核心：详情弹窗
└── types.ts                       # 运行状态、Tab 枚举
```

`pages/WorkflowPage.tsx` 瘦身为布局壳 + React Query 数据下发。

### 4.3 Workflow Details Modal 设计

**触发方式**：

- 点击监测任务行 → `mode: 'monitor'`
- 点击调度配置行 → `mode: 'config'`
- 点击执行记录行 → `mode: 'run'`

**布局**（桌面居中 Modal，移动全屏 Sheet — 参考 `WelcomeGuideDrawer` 的 overlay 模式）：

```
┌─────────────────────────────────────────────────────────┐
│  [×]  工作流详情 — {keyword | job_name}                  │
├─────────────────────────────────────────────────────────┤
│  Tab: [任务详情] [最近执行] [执行状态]                    │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  （Tab 内容区，见下表）                                   │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

#### Tab 1 — 任务详情

| 字段 | 监测任务 mode | 调度配置 mode |
|------|---------------|---------------|
| ID | `monitor_id` | `job_name` + `monitor_id` |
| 关键词 | `keyword` | 反查 monitors |
| 创建时间 | `created_at` | — |
| 观测数 / URL 数 | `observation_count`, `url_count` | — |
| Cron | — | `cron_expr` + `timezone` |
| 启用状态 | 采集状态推断 | `enabled` Badge |
| 备注 | — | `notes` |
| 快捷链接 | → 价格趋势页（带 `monitor_id` query） | — |

#### Tab 2 — 最近执行记录

- 筛选：当前 `monitor_id` 或 `job_name` 关联的 `external_scheduler_runs`
- 列表列：`job_name` | `status` | `message` | `last_seen_at` | `source`
- 默认展示最近 20 条，支持「加载更多」（`api.workflowState` 或新增调用 `GET /public/workflow/external-runs?limit=120`）
- 空状态：「暂无执行记录」

#### Tab 3 — 执行状态

综合展示当前任务/作业的**实时状态**：

| 状态源 | 展示 |
|--------|------|
| Gateway | `gateway.ok` → 在线/离线 Badge |
| 内置调度 `internal_scheduler` | enabled / started / interval |
| 最近一条 run | `status` + `message` + 相对时间 |
| 诊断摘要 | 可选：调用 `workflowDiagnostics` 中与 monitor 相关的 check |

**状态色彩**（复用 `Badge`）：

- `ok` / `success` → `success`
- `error` / `failed` → `danger`
- `running` / `pending` → `warning`
- 其他 → `muted`

### 4.4 新建基础 UI

`components/ui/Modal.tsx`（或 `Dialog.tsx`）：

- `open`, `onClose`, `title`, `children`
- ESC / 点击遮罩关闭
- `role="dialog"` + `aria-modal`
- 移动端 `max-h-[90vh] overflow-y-auto`

---

## 5. 价格趋势图方案

### 5.1 技术选型

| 方案 | 优点 | 缺点 | 建议 |
|------|------|------|------|
| 继续手写 Canvas | 零依赖 | 缩放/悬停/拖动工作量大 | ❌ |
| **uPlot** | 极轻量、高性能、内置 zoom | API 偏底层 | ✅ 推荐 |
| lightweight-charts | 金融场景成熟 | 体积较大 | 备选 |
| Recharts | React 声明式 | 大量点时性能一般 | 不推荐 |

**建议依赖**：`uplot` + `uplot-react`（或薄封装 hook）

### 5.2 组件结构

```
frontend/src/components/charts/
├── PriceTrendChart.tsx       # 主图表（uPlot 封装）
├── ChartTimeRangePicker.tsx  # 1h | 6h | 24h | 7d | 30d | 90d | All
├── ChartTooltip.tsx          # 悬停详情（价格、时间、商品名）
├── usePriceSeries.ts         # 数据获取 + 时间窗过滤
├── chartTheme.ts             # 亮/暗色 uPlot 主题
└── types.ts                  # PricePoint, TimeRange
```

`features/landing/DemoPriceChart.tsx` 改为复用 `PriceTrendChart` + 静态 demo 数据。

### 5.3 时间窗定义

```ts
type TimeRange = '1h' | '6h' | '24h' | '7d' | '30d' | '90d' | 'all'

const RANGE_MS: Record<TimeRange, number | null> = {
  '1h':  3_600_000,
  '6h':  21_600_000,
  '24h': 86_400_000,
  '7d':  7 * 86_400_000,
  '30d': 30 * 86_400_000,
  '90d': 90 * 86_400_000,
  all:   null,
}
```

**数据策略**：

```
TimeRange ∈ {1h, 6h, 24h}
  → api.observations(id, limit=1000)
  → 客户端 filter(captured_at >= now - range)
  → 每点独立绘制（显示所有观测点）

TimeRange ∈ {7d, 30d, 90d}
  → 主：observations 过滤后全点展示
  → 辅：timeseries(window_days) 可作为对比虚线（可选）

TimeRange = all
  → observations(limit=1000) 全量
  → 若 observation_count > 1000：UI 提示「展示最近 1000 条」
  → 后续可选后端分页（本阶段不改后端）
```

### 5.4 交互需求

| 能力 | 实现 |
|------|------|
| **缩放** | uPlot `cursor.drag.scaleX` + 滚轮缩放 |
| **拖动** | uPlot `cursor.drag.move` 平移 X 轴 |
| **悬停详情** | `cursor.sync` + 自定义 tooltip：时间、价格、商品名（`item_name`） |
| 重置视图 | 「重置缩放」按钮 |
| 响应式 | `ResizeObserver` 调整 `width` |

**图表配置要点**：

- X 轴：Unix 时间戳（秒）
- Y 轴：价格，自动 min/max padding
- 系列：折线 + 点标记（`points: { show: true }`）确保「所有观测点」可见
- 深色模式：`chartTheme.ts` 监听 `dark` class 切换 uPlot 颜色

### 5.5 PriceTrendPage 改造

```
监测任务选择器（保留）
├── 统计卡片（保留）
├── ChartTimeRangePicker（新）
├── PriceTrendChart（替换 canvas）
└── 采集明细表（保留，与图表 hover 高亮联动 — P2）
```

**空状态文案更新**（移除工作流创建引导）：

```diff
- description="前往工作流创建监测任务"
+ description="监测任务由 OpenClaw Agent 或 API 创建。请配置 Agent 后刷新本页。"
```

---

## 6. UI 入口删除清单

### 6.1 必须删除的前端 UI

| 文件 | 删除/修改内容 |
|------|---------------|
| `pages/WorkflowPage.tsx` | 删除两个 Card；删除 `keyword`/`monitorId` 表单 state；删除 `bootstrapMutation`/`analysisMutation` 的 **UI 绑定**（mutations 可整段移除，API 函数保留在 `api.ts`） |
| `pages/WorkflowPage.tsx` | 副标题改为「查看调度状态与执行记录」 |
| `pages/PriceTrendPage.tsx` | 空状态 CTA 不再链接「创建工作流」 |
| `pages/ReportsPage.tsx` | Onboarding Step 3 按钮「完成 Step 3 联合分析」→ 改为「查看工作流调度」或移除 |
| `pages/LandingPage.tsx` | 功能描述、步骤文案中「创建监测」「触发联合分析」改为 Agent/API 驱动叙事 |
| `features/onboarding/types.ts` | `step1`/`step3` 的 `coach` 目标与 `COACH_MESSAGES` 重写（不再指向已删表单项） |
| `features/onboarding/OnboardingProvider.tsx` | 移除 `ONBOARDING_EVENTS.monitorCreated` / `analysisRun` 监听；`step1` 仍可通过 `monitor_count >= 1` 服务端同步完成 |
| `features/onboarding/WelcomeGuideDrawer.tsx` | 步骤说明文案同步 |

### 6.2 明确保留

| 项 | 位置 |
|----|------|
| `api.workflowBootstrap` | `lib/api.ts` |
| `api.workflowAnalysis` | `lib/api.ts` |
| 后端路由 | `POST /public/workflow/monitor/bootstrap`、`POST /public/workflow/analysis/run` |
| OpenClaw Agent / 文档中的 API 说明 | `docs/` |

### 6.3 Onboarding 步骤调整建议

| 步骤 | 现文案 | 建议新文案 |
|------|--------|------------|
| step1 创建关键词 | 在工作流页输入关键词 | Agent 已为您创建监测任务（自动检测 `monitor_count`） |
| step3 创建定时任务 | 点击「立即分析」 | 查看工作流页调度执行记录；或通过 Agent 配置外部 Cron |

Coach Mark 目标元素改为工作流页**任务列表行**或**执行记录**，而非已删除的表单。

---

## 7. 实施阶段

### Phase 1 — 基础设施（1–2 天）

- [ ] 新建 `components/markdown/MarkdownContent.tsx` + 样式补全
- [ ] 新建 `components/ui/Modal.tsx`
- [ ] 迁移 `ReportDetail`、接入 `ChatPage` 助手消息
- [ ] 添加 `uplot` 依赖与 `chartTheme.ts`

### Phase 2 — 价格趋势（2–3 天）

- [ ] 实现 `usePriceSeries` + `PriceTrendChart` + `ChartTimeRangePicker`
- [ ] 重构 `PriceTrendPage.tsx`
- [ ] `DemoPriceChart` 复用共享图表组件
- [ ] 验证 8 档时间窗 + 缩放/拖动/悬停

### Phase 3 — 工作流（2–3 天）

- [ ] 拆分 `components/workflow/*`
- [ ] 实现 `WorkflowDetailsModal`（三 Tab）
- [ ] 瘦身 `WorkflowPage.tsx`，删除创建/分析 UI
- [ ] 监测任务表 + 执行记录可点击打开 Modal

### Phase 4 — 联动清理（1 天）

- [ ] 更新 Onboarding / Landing / 空状态文案
- [ ] 移除无用 `data-onboarding` 属性
- [ ] ESLint + `npm run build` 通过
- [ ] 手动回归：报告 Markdown、聊天、价格图、工作流 Modal

---

## 8. 文件变更总览

```
新增
  frontend/src/components/markdown/MarkdownContent.tsx
  frontend/src/components/ui/Modal.tsx
  frontend/src/components/workflow/WorkflowDetailsModal.tsx
  frontend/src/components/workflow/MonitorTaskTable.tsx
  frontend/src/components/workflow/SchedulerConfigTable.tsx
  frontend/src/components/workflow/SchedulerRunList.tsx
  frontend/src/components/workflow/WorkflowOverviewCards.tsx
  frontend/src/components/workflow/WorkflowDiagnosticsPanel.tsx
  frontend/src/components/workflow/types.ts
  frontend/src/components/charts/PriceTrendChart.tsx
  frontend/src/components/charts/ChartTimeRangePicker.tsx
  frontend/src/components/charts/usePriceSeries.ts
  frontend/src/components/charts/chartTheme.ts
  frontend/src/components/charts/types.ts

修改
  frontend/src/pages/WorkflowPage.tsx
  frontend/src/pages/PriceTrendPage.tsx
  frontend/src/features/reports/ReportDetail.tsx
  frontend/src/features/chat/ChatPage.tsx
  frontend/src/features/landing/DemoPriceChart.tsx
  frontend/src/features/onboarding/types.ts
  frontend/src/features/onboarding/OnboardingProvider.tsx
  frontend/src/pages/LandingPage.tsx
  frontend/src/pages/ReportsPage.tsx
  frontend/src/index.css
  frontend/package.json                    # +uplot

不修改
  app/**                                   # 后端全部保留
  frontend/src/lib/api.ts                  # 保留 bootstrap/analysis 方法
```

---

## 9. 验收标准

### Markdown

- [ ] 报告页 GFM 表格、代码块、标题、引用渲染正确（亮/暗色）
- [ ] 聊天助手回复支持相同 Markdown 子集
- [ ] 外链经 `markdownUrlTransform` 过滤，无 `javascript:` 注入

### 工作流

- [ ] 页面无「创建监测」「触发联合分析」表单或按钮
- [ ] 点击任务/配置/运行记录可打开 Modal
- [ ] Modal 三 Tab 数据正确：任务详情、最近执行、执行状态
- [ ] `api.workflowBootstrap` / `workflowAnalysis` 仍存在于 `api.ts`

### 价格趋势

- [ ] 图表展示当前时间窗内**全部**观测点（非仅日聚合）
- [ ] 8 档时间窗切换正常
- [ ] 鼠标：拖动平移、滚轮缩放、悬停显示时间+价格+商品名
- [ ] 移动端触摸拖动可用（uPlot touch 选项）

### 回归

- [ ] Agent 通过 API 创建监测后，工作流页列表与价格页下拉可见
- [ ] Onboarding 不因 UI 删除而卡死（服务端 sync 完成 step1/step3）

---

## 10. 风险与后续

| 风险 | 缓解 |
|------|------|
| observations `limit=1000` 不足以覆盖 All | UI 明示上限；远期可加后端 `since` 参数（非本阶段） |
| uPlot 学习曲线 | 封装 `PriceTrendChart` 隐藏配置细节 |
| 删除工作流表单后新用户无监测任务 | Landing/Onboarding 引导 Agent + 文档；空状态链到 `docs/human/api/` |
| 聊天 Markdown 与流式输出 | 流式时节流重渲染；未完成时不解析不完整代码块（可选 `compact` 模式） |

---

## 11. 附录：关键代码锚点

当前 Markdown 唯一渲染点：

```57:61:frontend/src/features/reports/ReportDetail.tsx
        <CardContent className="prose-report text-sm">
          <ReactMarkdown remarkPlugins={[remarkGfm]} urlTransform={markdownUrlTransform}>
            {report.analysis || '暂无分析内容'}
          </ReactMarkdown>
        </CardContent>
```

待删除的工作流 UI：

```94:136:frontend/src/pages/WorkflowPage.tsx
      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>创建监测任务</CardTitle>
          </CardHeader>
          ...
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>触发联合分析</CardTitle>
          </CardHeader>
          ...
        </Card>
      </div>
```

当前价格图（无交互、日聚合）：

```33:92:frontend/src/pages/PriceTrendPage.tsx
  useEffect(() => {
    const canvas = canvasRef.current
    const points = timeseriesQuery.data?.points || []
    ...
  }, [timeseriesQuery.data])
```
