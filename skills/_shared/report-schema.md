# 统一报告结构（OpenClaw Skills 共用）

**适用版本**：OpenClaw News Publisher 多用户 SaaS（2026-06 起）  
**对齐服务端**：`app/schemas/report.py` → `OpenClawReportIn`  
**用途**：Agent 组装、校验、发布报告前的唯一字段语义源。

---

## 概述

报告在 SaaS 中有两层表示：

| 层 | 说明 |
|----|------|
| **入站 Payload** | Agent `POST /api/v1/openclaw/reports` 的请求体（不含 `owner_user_id`） |
| **已发布视图** | 服务端入库后附加 `ingest_id`（即 `report_id`）、`owner_user_id`、`status` 等 |

**禁止**在入站 JSON 中伪造 `owner_user_id`；归属由服务端根据 `X-Api-Key` / JWT 注入。

---

## 统一结构定义

```json
{
  "report_id": "550e8400-e29b-41d4-a716-446655440000",
  "owner_user_id": "00000000-0000-0000-0000-000000000002",
  "monitor_id": "9551be2b-3e27-4935-a595-d1699163a3e9",
  "keyword": "羽毛球",
  "generated_title": "近7日羽毛球价格与新闻联合分析",
  "generated_at": "2026-06-06T10:00:00+08:00",
  "analysis": "……完整分析正文（Markdown 纯文本，禁止 HTML）……",
  "sources": ["monitoring-summary", "news-library"],
  "items": [
    {
      "title": "标题",
      "source": "来源媒体",
      "url": "https://example.com/news/1",
      "published_at": "2026-06-05T08:00:00+08:00",
      "price": 89.9,
      "currency": "CNY",
      "summary": "可选摘要"
    }
  ]
}
```

入站时还需包含服务端必填的 **`task_id`**、**`time_range`**（见下表）。`report_id` / `owner_user_id` 仅出现在响应或已发布记录中。

---

## 字段说明

### report_id

| 属性 | 值 |
|------|-----|
| **类型** | `string`（UUID） |
| **入站必填** | **否**（服务端分配） |
| **已发布必填** | **是** |
| **别名** | `ingest_id`（API 路径与响应字段名） |
| **用途** | 报告唯一标识；轮询 `GET /openclaw/reports/{ingest_id}`；门户列表/详情主键 |
| **规则** | Agent 不得自行生成并当作已入库 ID；仅接受 POST 202 响应中的值 |

### owner_user_id

| 属性 | 值 |
|------|-----|
| **类型** | `string`（UUID） |
| **入站必填** | **禁止出现在请求体** |
| **已发布必填** | **是**（DB `reports.user_id`） |
| **用途** | 多用户隔离；列表/详情/删除 scope |
| **规则** | 由服务端从 API Key / JWT 解析；跨用户访问他人 `report_id` → **404** |

### monitor_id

| 属性 | 值 |
|------|-----|
| **类型** | `string`（UUID） |
| **入站必填** | **否**（推荐填写） |
| **用途** | 关联价格监测任务；审计「报告基于哪条监测」；联合分析回链 |
| **规则** | 若提供，须属于当前 `owner_user_id`（与 API Key 一致），否则关联校验失败或分析时 404 |
| **备注** | 当前 `OpenClawReportIn` 未强制该字段；作为 **SaaS 扩展** 写入 `task_id` 前缀或 `sources` 元数据亦可，未来服务端可正式入库 |

### keyword

| 属性 | 值 |
|------|-----|
| **类型** | `string` |
| **入站必填** | **是** |
| **长度** | 1–200 字符 |
| **用途** | 报告主题词；门户筛选；新闻库联动 |
| **规则** | 非空；禁止仅空白；应与监测/新闻语义一致 |

### generated_title

| 属性 | 值 |
|------|-----|
| **类型** | `string` |
| **入站必填** | **是** |
| **长度** | 1–500 字符 |
| **用途** | 门户与列表展示标题 |
| **规则** | 禁止 HTML 标签与可执行内容；见 [`report-security.md`](report-security.md) |

### generated_at

| 属性 | 值 |
|------|-----|
| **类型** | `string`（ISO 8601 datetime） |
| **入站必填** | **是** |
| **用途** | 报告生成时刻；排序与复盘 |
| **规则** | 须为合法 ISO 8601；建议带时区（如 `+08:00`） |

### analysis

| 属性 | 值 |
|------|-----|
| **类型** | `string` |
| **入站必填** | **是** |
| **长度** | 1–50,000 字符 |
| **用途** | 完整分析正文；可含 Markdown 标题与列表 |
| **规则** | 须有归纳结论，不得仅堆砌标题；禁止 HTML/script；预测须标注非投资建议 |

### sources

| 属性 | 值 |
|------|-----|
| **类型** | `string[]` |
| **入站必填** | **是**（可为空数组 `[]`） |
| **长度** | 最多 50 项；每项 1–200 字符 |
| **用途** | 标明分析数据来源（如 `monitoring-summary`、`news-library`、`public-reports-history`、爬虫域名） |
| **规则** | 每项非空字符串；与 `items` 可追溯 |

### items

| 属性 | 值 |
|------|-----|
| **类型** | `array` of `NewsItem` |
| **入站必填** | **是**（可为空数组 `[]`） |
| **长度** | 最多 200 条 |
| **用途** | 结构化证据条目（新闻链接、可选价格） |
| **规则** | 若为空，须在 `analysis` 中说明原因 |

#### NewsItem 子字段

| 字段 | 类型 | 必填 | 长度/规则 |
|------|------|------|-----------|
| `title` | string | **是** | 1–500 |
| `source` | string | **是** | 1–200 |
| `url` | string | **是** | 1–2000；仅 `http`/`https`；须有 host |
| `published_at` | string (ISO 8601) | **是** | 合法 datetime |
| `price` | number | 否 | 浮点 |
| `currency` | string | 否 | 最长 16；默认业务口径 CNY |
| `summary` | string | 否 | 最长 4000 |

---

## 入站专用字段（OpenClawReportIn）

以下字段为 `POST /openclaw/reports` **额外必填**，纳入完整入站契约：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `task_id` | string | **是** | 1–128 字符；业务任务 ID；与 `X-Request-Id` 配合幂等 |
| `time_range` | object | **是** | `start`、`end` 均为 ISO 8601；表示数据采集窗口 |
| `insights` | object | 否 | `sentiment`、`risk_level`、`market_impact`、`confidence`、`forecast` |

### 请求头（必填）

| 头 | 说明 |
|----|------|
| `X-Api-Key` | per-user API Key |
| `X-Request-Id` | 幂等键；缺失 → **400** |
| `Content-Type` | `application/json` |

---

## 必填规则汇总

### POST 入站最小必填集

```
task_id, keyword, time_range.start, time_range.end,
sources, items, analysis, generated_title, generated_at
+ 请求头 X-Api-Key, X-Request-Id
```

### 已发布记录完整视图

```
report_id (ingest_id), owner_user_id, keyword, generated_title,
generated_at, analysis, sources, items, status
+ 推荐 monitor_id（扩展）
```

---

## 与服务端映射

| 统一字段 | API / DB 字段 |
|----------|----------------|
| `report_id` | `ingest_id` |
| `owner_user_id` | `reports.user_id` |
| 其余入站字段 | `payload_json` / `rendered_payload` |

### 入站响应扩展（预埋）

`POST /openclaw/reports` 202 目标含 `owner_user_id`（及可选 `quota_remaining`），见 [`workspace-api-roadmap.md`](workspace-api-roadmap.md)。当前若响应无该字段，归属以服务端 DB 为准，Agent 不得请求体伪造。

---

## 相关文档

- [`report-security.md`](report-security.md) — 发布前安全校验
- [`ownership-policy.md`](ownership-policy.md) — 归属与跨用户规则
- [`multi-user-auth.md`](multi-user-auth.md) — 鉴权
- [`docs/02-backend/api.md`](../../docs/02-backend/api.md) — 入站 API 权威说明
