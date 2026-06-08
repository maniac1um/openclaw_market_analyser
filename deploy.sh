#!/usr/bin/env bash
# One-click deploy for OpenClaw News Publisher.
#
# Usage:
#   bash deploy.sh                  # bare-metal: git pull, build, restart local server
#   bash deploy.sh --docker         # Docker Compose (profile full)
#   bash deploy.sh --systemd        # systemd unit restart (requires sudo)
#   bash deploy.sh --skip-pull      # skip git pull
#   bash deploy.sh --skip-frontend  # skip npm build
#
# Prerequisites:
#   - .env configured (copy from .env.example)
#   - PostgreSQL reachable (three databases)
#   - For --docker: Docker Engine + Compose v2
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

MODE="bare"
SKIP_PULL=0
SKIP_FRONTEND=0
PORT="${OPENCLAW_BIND_PORT:-8000}"
PYTHON_BIN="${PYTHON_BIN:-python3}"
SYSTEMD_UNIT="${OPENCLAW_SYSTEMD_UNIT:-openclaw-news-publisher}"

usage() {
  cat <<'EOF'
Usage: bash deploy.sh [options]

Options:
  --docker          Deploy via docker compose --profile full
  --systemd         Restart systemd service after bare-metal build
  --skip-pull       Do not run git pull
  --skip-frontend   Skip frontend npm ci && npm run build
  --help            Show this help

Steps (bare-metal):
  1. git pull
  2. Python venv + pip install -e .
  3. frontend npm ci && npm run build
  4. Database migration (via app startup on next serve)
  5. Restart service (local script or systemd)
  6. Health check /healthz and /healthz/db

EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --docker) MODE="docker"; shift ;;
    --systemd) MODE="systemd"; shift ;;
    --skip-pull) SKIP_PULL=1; shift ;;
    --skip-frontend) SKIP_FRONTEND=1; shift ;;
    --help|-h) usage; exit 0 ;;
    *) echo "Unknown option: $1" >&2; usage; exit 1 ;;
  esac
done

echo "==> OpenClaw News Publisher — one-click deploy"
echo "==> Root: $ROOT"
echo "==> Mode: $MODE"

if [[ "$SKIP_PULL" != "1" ]]; then
  if ! command -v git >/dev/null 2>&1; then
    echo "ERROR: git not found." >&2
    exit 1
  fi
  echo "==> git pull"
  git pull --ff-only
fi

if [[ ! -f .env ]]; then
  echo "ERROR: .env not found. Copy .env.example to .env and configure database URLs." >&2
  exit 1
fi

health_wait() {
  local deadline=$((SECONDS + 120))
  local ok=0
  echo "==> Waiting for health checks (port $PORT)..."
  while [[ $SECONDS -lt $deadline ]]; do
    if curl -sf "http://127.0.0.1:${PORT}/healthz" >/dev/null 2>&1; then
      if curl -sf "http://127.0.0.1:${PORT}/healthz/db" 2>/dev/null | grep -q '"ok":true'; then
        ok=1
        break
      fi
      # Process up but DB not configured — still report partial success
      if ! grep -q '^OPENCLAW_DATABASE_URL=.\+' .env 2>/dev/null; then
        echo "WARN: /healthz OK but no OPENCLAW_DATABASE_URL in .env"
        ok=2
        break
      fi
    fi
    sleep 2
  done

  if [[ "$ok" == "1" ]]; then
    echo "==> Health OK: http://127.0.0.1:${PORT}/healthz/db"
  elif [[ "$ok" == "2" ]]; then
    echo "==> Health partial: http://127.0.0.1:${PORT}/healthz (no database configured)"
  else
    echo "ERROR: Service did not become healthy within 120s." >&2
    echo "  curl -v http://127.0.0.1:${PORT}/healthz" >&2
    exit 1
  fi
}

if [[ "$MODE" == "docker" ]]; then
  if ! command -v docker >/dev/null 2>&1; then
    echo "ERROR: docker not found." >&2
    exit 1
  fi
  if ! docker compose version >/dev/null 2>&1; then
    echo "ERROR: docker compose v2 not found." >&2
    exit 1
  fi

  echo "==> Building Docker images"
  docker compose --profile full build

  echo "==> Starting stack"
  docker compose --profile full up -d

  health_wait

  echo
  echo "Deploy complete (Docker)."
  echo "  Logs: docker compose --profile full logs -f app"
  echo "  Stop: bash scripts/deploy/one-click-docker.sh --down"
  exit 0
fi

# --- Bare-metal / systemd backend build ---
if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
  echo "ERROR: $PYTHON_BIN not found." >&2
  exit 1
fi

if [[ ! -d .venv ]]; then
  echo "==> Creating .venv"
  "$PYTHON_BIN" -m venv .venv
fi

# shellcheck source=/dev/null
source .venv/bin/activate

echo "==> Installing backend dependencies"
python -m pip install --upgrade pip
python -m pip install -e .

if [[ "$SKIP_FRONTEND" != "1" ]]; then
  if ! command -v npm >/dev/null 2>&1; then
    echo "ERROR: npm not found. Install Node.js 20+ or use --skip-frontend." >&2
    exit 1
  fi
  echo "==> Building frontend"
  (
    cd frontend
    npm ci
    npm run build
  )
else
  echo "==> Skipping frontend build"
  if [[ ! -d frontend/dist ]]; then
    echo "WARN: frontend/dist missing; SPA may 404 until you run npm run build." >&2
  fi
fi

echo "==> Verifying database connectivity (optional)"
if [[ -x scripts/local/verify-openclaw-databases.sh ]]; then
  bash scripts/local/verify-openclaw-databases.sh || echo "WARN: database verify failed — check .env DSNs"
fi

echo "==> Database migrations run automatically on app startup (run_multi_user_migrations)"

if [[ "$MODE" == "systemd" ]]; then
  echo "==> Restarting systemd unit: $SYSTEMD_UNIT"
  sudo systemctl daemon-reload
  sudo systemctl restart "$SYSTEMD_UNIT"
  sudo systemctl --no-pager status "$SYSTEMD_UNIT" || true
else
  echo "==> Restarting local server"
  bash scripts/local/restart-server.sh
fi

health_wait

# shellcheck source=/dev/null
if [[ -f scripts/local/workflow-post-check.sh ]]; then
  source scripts/local/workflow-post-check.sh
  workflow_post_check "$PORT" || true
fi

echo
echo "Deploy complete."
echo "  Home:     http://127.0.0.1:${PORT}/"
echo "  Health:   http://127.0.0.1:${PORT}/healthz/db"
echo "  Workflow: http://127.0.0.1:${PORT}/workflow"
