# 跨平台开发

> Windows 11 与 Ubuntu 24.04 协作同一 GitHub 仓库的注意事项。

## 做什么

避免「本机正常、换系统就挂」：换行符、venv、路径、环境变量差异。

## 关键组件

| 问题域 | 约定 |
|--------|------|
| 换行 | 仓库 `.gitattributes` → LF；Windows 设 `core.autocrlf=false` |
| Python | 各机独立 `.venv`，`pip install -e ".[dev]"` |
| 配置 | `.env` 不提交；各机单独创建 |
| 路径 | 用 `pathlib`，不写死盘符 |
| Git | Ubuntu 单独配 SSH/身份 |

| 相同命令 | |
|----------|--|
| 启动 | `uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload` |
| 测试 | `pytest -q` |

## 数据流

```
GitHub (LF) ──clone──► Win / Ubuntu 各自 venv + .env
                           │
                      同一套 API 契约、同一 pytest
```

## 示例

```bash
# Ubuntu 新机器
git clone <repo> && cd openclaw_news_publisher
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env   # 填本机 DSN

# Windows PowerShell 等价
python -m venv .venv; .\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
```

JSON 请求统一 UTF-8：`Content-Type: application/json; charset=utf-8`。

| 本地开发 | [../01-getting-started/local-dev.md](../01-getting-started/local-dev.md) |
