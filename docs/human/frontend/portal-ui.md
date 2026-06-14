# 门户前端 UI

React SPA 的导航、布局与设计系统约定（2026-06 起）。

## 技术栈

| 层 | 选型 |
|----|------|
| 框架 | React 19 + TypeScript |
| 构建 | Vite 8 |
| 样式 | Tailwind CSS v4 + CSS 变量（`--bg` / `--text` 等） |
| 路由 | React Router v7 |
| 数据 | TanStack Query |
| 图表 | uPlot |

源码入口：`frontend/src/`；设计系统组件：`frontend/src/components/ui/ds/`。

## 应用壳（AppShell）

```text
┌─────────────────────────────────────────────┐
│ AppTopBar  ☰  搜索  [🌙/☀️]  [对话]  用户    │
├─────────────────────────────────────────────┤
│              主内容区（Outlet）               │
└─────────────────────────────────────────────┘
```

| 元素 | 说明 |
|------|------|
| **☰ 左侧 Drawer** | 260px，`translateX` 滑入；遮罩仅半透明 dim，**无 backdrop-blur** |
| **主题切换** | 右上角 🌙/☀️；`localStorage.theme` = `dark` \| `light`；`<html class="dark">` |
| **对话列表 Drawer** | 仅首页（`/app`）显示；右侧 300px |
| **固定 Sidebar** | ❌ 不使用 |

布局文件：

- `frontend/src/components/layout/AppShell.tsx`
- `frontend/src/components/layout/AppTopBar.tsx`
- `frontend/src/components/layout/AppNavDrawer.tsx`
- `frontend/src/lib/theme.ts`、`ThemeProvider.tsx`

## 路由与页面

| 路径 | 页面 | 布局要点 |
|------|------|----------|
| `/app` | 工作区（OpenClaw 对话） | 全屏聊天，无额外 padding |
| `/app/reports` | 专题分析列表 | 居中 `max-width: 900px` |
| `/app/reports/:id` | 报告详情 | 全屏阅读，`max-width: 900px` |
| `/app/news` | 新闻列表 | 居中 `max-width: 900px` |
| `/app/news/:id` | 新闻详情 | 全屏阅读，`max-width: 800px` |
| `/app/price-trend` | 价格趋势 | 图表 + 观测列表 |
| `/app/workflow` | 工作流 | Panel + 表格 |
| `/app/keyword-tracking` | 关键词 | 跨模块概览 |
| `/app/account` | 账户 | API Key 管理 |

旧路径 `/reports/:id`、`/news/:id` 会 302 到 `/app/reports/:id`、`/app/news/:id`。

## 列表与详情交互

**专题分析 / 新闻** 采用「居中列表 + 全屏详情」：

1. 列表页：居中 Panel（900px），`DataRow` 展示标题、时间、摘要/关键词。
2. 点击条目：**路由跳转**至详情页（非 Drawer），便于长文 Markdown 阅读。
3. 详情页：返回列表链接 + 标题 + 元数据 + `MarkdownContent` 正文。

相关文件：

- `frontend/src/pages/ReportsPage.tsx`、`ReportDetailPage.tsx`
- `frontend/src/pages/NewsPage.tsx`、`NewsDetailPage.tsx`
- `frontend/src/features/reports/ReportDetailContent.tsx`
- `frontend/src/features/news/NewsArticleContent.tsx`

**Drawer 适用场景**：导航菜单、对话历史、新手引导等**短内容**；不用于展示完整新闻/报告正文。

## 设计系统（ds）

| 组件 | 用途 |
|------|------|
| `Panel` | 玻璃面板；hover 时边框变亮 |
| `DataRow` | 列表行；hover 高亮 |
| `Drawer` | 侧滑层；默认右侧 480px，导航左侧 260px |
| `Skeleton` / `TableSkeleton` | 加载占位 |
| `CommandBar` | 搜索/工具栏 |
| `Section` / `StatStrip` | 区块标题与 KPI 条 |

主题 token 定义于 `frontend/src/index.css`（`:root` / `.dark`）。

## 主题

- 首屏：`index.html` 内联脚本读取 `localStorage.theme`，避免闪烁。
- 运行时：`ThemeProvider` 同步 `html.dark` 与持久化。
- 兼容旧键：`oc_dark` 会在首次读取时迁移。

## 本地开发

```bash
cd frontend && npm install && npm run dev   # http://localhost:5173
```

生产构建由根目录 `deploy.sh` 或 Docker 多阶段镜像完成：

```bash
bash deploy.sh --docker          # 推荐：Compose 重建并健康检查
bash deploy.sh --docker --skip-pull  # 跳过 git pull
```

## 相关文档

- [开发者指南](../development/developer-guide.md)
- [门户对话](../features/portal-chat.md)
- [Android 内测](../mobile/android-app.md)
