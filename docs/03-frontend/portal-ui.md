# 门户 UI

> React 19 + Vite + Tailwind v4 · 源码 `frontend/src/`。

## 做什么

定义 SPA 布局、路由、主题与 Design System 约定，保证各页面视觉与交互一致。

## 关键组件

```
AppShell
├── AppTopBar（☰ · 搜索 · 主题 · 用户）
├── AppNavDrawer（260px 左侧导航）
└── Outlet（主内容）
```

| 技术 | 选型 |
|------|------|
| 框架 | React 19 + TypeScript |
| 路由 | React Router v7 |
| 数据 | TanStack Query |
| DS | `components/ui/ds/*` |

| 路径 | 页面 | 布局 |
|------|------|------|
| `/app` | 工作区对话 | 全屏聊天 |
| `/app/reports` | 报告列表 | 居中 max 900px |
| `/app/news` | 新闻列表 | 居中 max 900px |
| `/app/workflow` | 工作流控制台 | 全宽 |
| `/account` | 账户 / API Key | 居中 |
| `/billing` | 充值订阅 | 居中 |

| 主题 | 机制 |
|------|------|
| Dark/Light | `localStorage.theme` → `<html class="dark">` |
| 变量 | CSS `--bg` / `--text` 等 |

## 数据流

```
AuthContext 登录 → api.ts fetch + JWT Cookie
    → TanStack Query 缓存 → Page 组件渲染
        → AppShell 包裹 → Drawer 导航切换路由
```

对话页额外：`ChatProvider` 全站 WS，不随路由 unmount。

## 示例

```bash
cd frontend && npm run dev    # :5173，/api 代理到 :8000
```

新增页面三步：

1. `frontend/src/pages/XxxPage.tsx`
2. `App.tsx` 注册路由
3. `AppNavDrawer.tsx` 添加入口

| 开发规范 | [../05-dev/developer-guide.md](../05-dev/developer-guide.md) |
| 对话 | [../04-product/portal-chat.md](../04-product/portal-chat.md) |
