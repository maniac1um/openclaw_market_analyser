#!/usr/bin/env bash
# 本地开发：后台启动 FastAPI，前台提示启动前端 dev server
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"

if [[ ! -d .venv ]]; then
  echo "请先创建虚拟环境: python3 -m venv .venv && source .venv/bin/activate && pip install -e '.[dev]'" >&2
  exit 1
fi

bash scripts/local/start-server.sh

echo ""
echo "后端已启动。请在另一终端运行："
echo "  cd frontend && npm install && npm run dev"
echo "然后访问 http://localhost:5173"
