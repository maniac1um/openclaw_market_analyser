#!/usr/bin/env bash
# One-click deploy: OpenClaw News Publisher + PostgreSQL (Docker Compose).
# Requires: Docker Engine + Docker Compose v2.
# Does NOT install OpenClaw Gateway (chat/workflow still need ws://...:18789 on host).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

PORT="${OPENCLAW_BIND_PORT:-8000}"
ENV_DOCKER="$ROOT/scripts/deploy/env.docker.example"
FORCE_ENV=0

usage() {
  cat <<'EOF'
Usage: bash scripts/deploy/one-click-docker.sh [options]

Options:
  --force-env   Overwrite .env with Docker template (backs up existing .env)
  --down        Stop and remove compose stack (keeps pgdata volume)
  --help        Show this help

EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --force-env) FORCE_ENV=1; shift ;;
    --down)
      docker compose --profile full down
      echo "Stack stopped. Data volume 'pgdata' retained unless you run: docker compose --profile full down -v"
      exit 0
      ;;
    --help|-h) usage; exit 0 ;;
    *) echo "Unknown option: $1" >&2; usage; exit 1 ;;
  esac
done

if ! command -v docker >/dev/null 2>&1; then
  echo "ERROR: docker not found. Install Docker Engine first." >&2
  exit 1
fi

if ! docker compose version >/dev/null 2>&1; then
  echo "ERROR: docker compose (v2 plugin) not found." >&2
  exit 1
fi

echo "==> OpenClaw + PostgreSQL one-click deploy (Docker)"
echo "==> Project root: $ROOT"

if [[ ! -f .env ]] || [[ "$FORCE_ENV" == "1" ]]; then
  if [[ -f .env ]] && [[ "$FORCE_ENV" == "1" ]]; then
    cp .env ".env.bak.$(date +%Y%m%d%H%M%S)"
    echo "==> Backed up existing .env"
  fi
  cp "$ENV_DOCKER" .env
  echo "==> Wrote .env from scripts/deploy/env.docker.example"
elif ! grep -q '@postgres:5432' .env 2>/dev/null; then
  echo "WARN: .env exists but DSN may not target compose postgres (@postgres:5432)."
  echo "      Use --force-env to regenerate, or edit OPENCLAW_*_DATABASE_URL manually."
fi

echo "==> Building images"
docker compose --profile full build

echo "==> Starting app + postgres (profile: full)"
docker compose --profile full up -d

echo "==> Waiting for services"
deadline=$((SECONDS + 120))
ok=0
while [[ $SECONDS -lt $deadline ]]; do
  if curl -sf "http://127.0.0.1:${PORT}/healthz" >/dev/null \
    && curl -sf "http://127.0.0.1:${PORT}/healthz/db" | grep -q '"ok":true'; then
    ok=1
    break
  fi
  sleep 2
done

if [[ "$ok" != "1" ]]; then
  echo "ERROR: Service did not become healthy within 120s." >&2
  echo "Inspect: docker compose --profile full logs -f" >&2
  exit 1
fi

echo
echo "Done. Open:"
echo "  - Home:     http://127.0.0.1:${PORT}/"
echo "  - Workflow: http://127.0.0.1:${PORT}/workflow"
echo "  - Docs:     http://127.0.0.1:${PORT}/docs"
echo "  - Health:   http://127.0.0.1:${PORT}/healthz/db"
echo
echo "PostgreSQL (host): 127.0.0.1:5432"
echo "  Users/DBs: openclaw_app, openclaw_monitor, openclaw_news (password: openclaw_dev)"
echo
echo "Stop stack:  bash scripts/deploy/one-click-docker.sh --down"
echo "View logs:   docker compose --profile full logs -f"
echo
echo "Note: OpenClaw Gateway (ws://127.0.0.1:18789) is NOT bundled."
echo "      Start Gateway on the host for chat; container uses host.docker.internal."
