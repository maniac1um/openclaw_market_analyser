#!/usr/bin/env bash
# Safe cleanup for OpenClaw News Publisher — removes regenerable caches and ephemeral artifacts.
# Does NOT delete: .git, .env, databases, openclaw-state/, openclaw-portal-state/, backups/, content/reports/
#
# Usage:
#   bash scripts/local/cleanup.sh              # dry-run (default)
#   bash scripts/local/cleanup.sh --apply      # perform deletion
#   bash scripts/local/cleanup.sh --apply --aggressive   # also remove node_modules, dist, .venv
#   bash scripts/local/cleanup.sh --log-days 30
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

APPLY=0
AGGRESSIVE=0
LOG_DAYS=30

usage() {
  cat <<'EOF'
Usage: bash scripts/local/cleanup.sh [options]

Options:
  --apply         Actually delete files (default is dry-run)
  --aggressive    Also remove frontend/node_modules, frontend/dist, .venv, *.egg-info
  --log-days N    Remove local server logs older than N days (default: 30)
  --help          Show this help

Safe targets (always):
  __pycache__, .pytest_cache, .mypy_cache, .ruff_cache, htmlcov, .coverage
  skills/*/runs/*, skills/*/.openclaw/, skills/*/report_payload.json, tmp_*.json
  expired /tmp server logs

Never deleted:
  .git, .env, openclaw-state/, openclaw-portal-state/, backups/, content/reports/, PostgreSQL

EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --apply) APPLY=1; shift ;;
    --aggressive) AGGRESSIVE=1; shift ;;
    --log-days) LOG_DAYS="${2:?}"; shift 2 ;;
    --help|-h) usage; exit 0 ;;
    *) echo "Unknown option: $1" >&2; usage; exit 1 ;;
  esac
done

DRY_LABEL="[dry-run]"
if [[ "$APPLY" == "1" ]]; then
  DRY_LABEL="[apply]"
fi

removed=0

log_action() {
  echo "$DRY_LABEL $*"
}

rm_path() {
  local p="$1"
  [[ -e "$p" ]] || return 0
  if [[ "$APPLY" == "1" ]]; then
    if [[ -d "$p" ]]; then
      rm -rf "$p"
    else
      rm -f "$p"
    fi
  fi
  log_action "remove: $p"
  removed=$((removed + 1))
}

# --- Python / test caches (repo root) ---
for name in .pytest_cache .mypy_cache .ruff_cache htmlcov; do
  rm_path "$ROOT/$name"
done
rm_path "$ROOT/.coverage"

while IFS= read -r -d '' d; do
  rm_path "$d"
done < <(find "$ROOT" -type d -name '__pycache__' \
  ! -path '*/frontend/node_modules/*' \
  ! -path '*/.venv/*' \
  -print0 2>/dev/null || true)

# --- Skill ephemeral artifacts (NOT repo-root openclaw-state) ---
while IFS= read -r -d '' skill; do
  [[ "$skill" == "$ROOT/skills/"* ]] || continue

  rm_path "$skill/report_payload.json"
  for extra in gold_price_report.json badminton_price_report.json; do
    rm_path "$skill/$extra"
  done
  rm_path "$skill/.openclaw"

  if [[ -d "$skill/runs" ]]; then
    while IFS= read -r -d '' f; do
      rm_path "$f"
    done < <(find "$skill/runs" -mindepth 1 -print0 2>/dev/null || true)
    if [[ "$APPLY" == "1" ]] && [[ -d "$skill/runs" ]]; then
      rmdir "$skill/runs" 2>/dev/null && log_action "remove empty dir: $skill/runs" || true
    elif [[ -d "$skill/runs" ]]; then
      log_action "remove contents of: $skill/runs/"
    fi
  fi
done < <(find "$ROOT/skills" -mindepth 1 -maxdepth 1 -type d -print0 2>/dev/null || true)

# --- Temp JSON at repo root ---
while IFS= read -r -d '' f; do
  rm_path "$f"
done < <(find "$ROOT" -maxdepth 1 -type f -name 'tmp_*.json' -print0 2>/dev/null || true)

# --- Old .env backups from docker deploy ---
while IFS= read -r -d '' f; do
  rm_path "$f"
done < <(find "$ROOT" -maxdepth 1 -type f -name '.env.bak.*' -print0 2>/dev/null || true)

# --- Expired local server logs ---
clean_old_log() {
  local f="$1"
  [[ -f "$f" ]] || return 0
  if find "$f" -mtime "+${LOG_DAYS}" 2>/dev/null | grep -q .; then
    rm_path "$f"
  else
    log_action "keep (newer than ${LOG_DAYS}d): $f"
  fi
}

clean_old_log "${TMPDIR:-/tmp}/openclaw_news_publisher.server.log"
clean_old_log "${TMPDIR:-/tmp}/openclaw_news_publisher.uvicorn.pid"

if [[ -d "$ROOT/frontend/logs" ]]; then
  while IFS= read -r -d '' f; do
    if find "$f" -mtime "+${LOG_DAYS}" 2>/dev/null | grep -q .; then
      rm_path "$f"
    fi
  done < <(find "$ROOT/frontend/logs" -type f -print0 2>/dev/null || true)
fi

if [[ -d "$ROOT/logs" ]]; then
  while IFS= read -r -d '' f; do
    if find "$f" -mtime "+${LOG_DAYS}" 2>/dev/null | grep -q .; then
      rm_path "$f"
    fi
  done < <(find "$ROOT/logs" -type f -print0 2>/dev/null || true)
fi

# --- Aggressive optional targets ---
if [[ "$AGGRESSIVE" == "1" ]]; then
  rm_path "$ROOT/frontend/node_modules"
  rm_path "$ROOT/frontend/dist"
  rm_path "$ROOT/.venv"
  while IFS= read -r -d '' d; do
    rm_path "$d"
  done < <(find "$ROOT" -maxdepth 1 -type d -name '*.egg-info' -print0 2>/dev/null || true)
  if [[ -d "$ROOT/frontend/android/build" ]]; then
    rm_path "$ROOT/frontend/android/build"
  fi
  if [[ -d "$ROOT/frontend/android/.gradle" ]]; then
    rm_path "$ROOT/frontend/android/.gradle"
  fi
fi

echo
if [[ "$APPLY" == "1" ]]; then
  echo "Done. Applied cleanup ($removed action(s))."
  if [[ "$AGGRESSIVE" == "1" ]]; then
    echo "Aggressive mode: run 'pip install -e .' and 'cd frontend && npm ci && npm run build' before next deploy."
  fi
else
  echo "Dry-run complete ($removed item(s) would be affected)."
  echo "Re-run with: bash scripts/local/cleanup.sh --apply"
fi

echo
echo "Protected (never touched by this script):"
echo "  .git/  .env  openclaw-state/  openclaw-portal-state/  backups/  content/reports/  PostgreSQL"
