#!/usr/bin/env bash
set -euo pipefail

WSL_RUN_HINT='wsl -d Ubuntu --cd /home/hp/ad-edge-demo -- bash -lc "./start_demo.sh"'

usage() {
  cat <<EOF
Usage: ./start_demo.sh [--help]

Start the AD dMRI edge demo from the project root in WSL/Linux.

Required environment:
  - Run inside Linux/WSL, not Windows PowerShell/CMD/Git Bash.
  - Backend uses .venv/bin/python from this project.
  - Frontend uses Linux/WSL node and npm.
  - Configuration is read from .env.

If you are on Windows, run:
  ${WSL_RUN_HINT}
EOF
}

die() {
  printf 'ERROR: %s\n' "$*" >&2
  exit 1
}

warn() {
  printf 'WARN: %s\n' "$*" >&2
}

info() {
  printf '[start_demo] %s\n' "$*"
}

prepend_nvm_node_if_needed() {
  local node_dir
  if command -v node >/dev/null 2>&1 && command -v npm >/dev/null 2>&1; then
    return 0
  fi

  if [[ -d "$HOME/.nvm/versions/node" ]]; then
    while IFS= read -r node_dir; do
      if [[ -x "$node_dir/bin/node" && -x "$node_dir/bin/npm" ]]; then
        export PATH="$node_dir/bin:$PATH"
        info "Using Linux/WSL Node from nvm: $node_dir/bin"
        return 0
      fi
    done < <(find "$HOME/.nvm/versions/node" -mindepth 1 -maxdepth 1 -type d | sort -V -r)
  fi

  return 0
}

if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
  usage
  exit 0
fi

if [[ "$(uname -s 2>/dev/null || true)" != "Linux" ]]; then
  cat >&2 <<EOF
This script must be run inside Linux/WSL.

On Windows, use:
  ${WSL_RUN_HINT}
EOF
  exit 1
fi

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"
PROJECT_ROOT="$PWD"

if [[ ! -f "backend/main.py" || ! -f "frontend/package.json" ]]; then
  die "start_demo.sh must be located in and run from the project root."
fi

if [[ ! -f ".env" ]]; then
  cat >&2 <<EOF
.env was not found.

Create it from the example before starting the demo:
  cp .env.example .env

Then review APP_HOST, BACKEND_PORT, FRONTEND_PORT, CASE_ROOT, and OUTPUT_OVERWRITE.
EOF
  exit 1
fi

load_env() {
  local line key value
  while IFS= read -r line || [[ -n "$line" ]]; do
    line="${line%$'\r'}"
    [[ -z "$line" || "$line" =~ ^[[:space:]]*# ]] && continue
    [[ "$line" != *=* ]] && continue
    key="${line%%=*}"
    value="${line#*=}"
    key="${key#"${key%%[![:space:]]*}"}"
    key="${key%"${key##*[![:space:]]}"}"
    value="${value#"${value%%[![:space:]]*}"}"
    value="${value%"${value##*[![:space:]]}"}"
    if [[ "$value" == \"*\" && "$value" == *\" ]]; then
      value="${value:1:${#value}-2}"
    elif [[ "$value" == \'*\' && "$value" == *\' ]]; then
      value="${value:1:${#value}-2}"
    fi
    case "$key" in
      APP_HOST|BACKEND_PORT|FRONTEND_PORT|CASE_ROOT|OUTPUT_OVERWRITE|APP_ENV)
        export "$key=$value"
        ;;
    esac
  done < ".env"
}

load_env

APP_HOST="${APP_HOST:-127.0.0.1}"
BACKEND_PORT="${BACKEND_PORT:-8000}"
FRONTEND_PORT="${FRONTEND_PORT:-5173}"
CASE_ROOT="${CASE_ROOT:-./data/cases}"
OUTPUT_OVERWRITE="${OUTPUT_OVERWRITE:-true}"
export APP_HOST BACKEND_PORT FRONTEND_PORT CASE_ROOT OUTPUT_OVERWRITE

case "$BACKEND_PORT" in
  ''|*[!0-9]*) die "BACKEND_PORT must be a number, got: $BACKEND_PORT" ;;
esac
case "$FRONTEND_PORT" in
  ''|*[!0-9]*) die "FRONTEND_PORT must be a number, got: $FRONTEND_PORT" ;;
esac

resolve_path() {
  local input="$1"
  if [[ "$input" = /* ]]; then
    printf '%s\n' "$input"
  else
    printf '%s\n' "$PROJECT_ROOT/${input#./}"
  fi
}

CASE_ROOT_ABS="$(resolve_path "$CASE_ROOT")"
[[ -d "$CASE_ROOT_ABS" ]] || die "CASE_ROOT does not exist: $CASE_ROOT_ABS"

mapfile -t CASE_DIRS < <(find "$CASE_ROOT_ABS" -mindepth 1 -maxdepth 1 -type d | sort)
if (( ${#CASE_DIRS[@]} == 0 )); then
  die "No case package directories found under CASE_ROOT: $CASE_ROOT_ABS"
fi

[[ -x ".venv/bin/python" ]] || die "Missing .venv/bin/python. Create/install the backend virtual environment inside WSL first."

PYTHON_PATH="$(.venv/bin/python -c 'import sys; print(sys.executable)')"
case "$PYTHON_PATH" in
  /mnt/*|*[Cc]:\\*) die "Backend Python resolved to a Windows path: $PYTHON_PATH" ;;
esac

if ! .venv/bin/python -c 'import uvicorn' >/dev/null 2>&1; then
  die "Backend dependency uvicorn is not available in .venv. Install backend requirements inside WSL."
fi

[[ -d "frontend/node_modules" ]] || die "Missing frontend/node_modules. Install frontend dependencies inside WSL first."
prepend_nvm_node_if_needed
command -v node >/dev/null 2>&1 || die "Linux/WSL node was not found in PATH. Install Node.js inside WSL; do not use Windows Node."
command -v npm >/dev/null 2>&1 || die "Linux/WSL npm was not found in PATH. Install npm inside WSL; do not use Windows npm."

NODE_PATH="$(command -v node)"
NPM_PATH="$(command -v npm)"
case "$NODE_PATH" in
  /mnt/*|*[Cc]:\\*) die "node resolves to a Windows path: $NODE_PATH. Install/use Linux Node inside WSL." ;;
esac
case "$NPM_PATH" in
  /mnt/*|*[Cc]:\\*) die "npm resolves to a Windows path: $NPM_PATH. Install/use Linux npm inside WSL." ;;
esac

BACKEND_PID=""
FRONTEND_PID=""
LOG_DIR="${TMPDIR:-/tmp}/ad-edge-demo"
mkdir -p "$LOG_DIR"
BACKEND_LOG="$LOG_DIR/backend-${BACKEND_PORT}.log"
FRONTEND_LOG="$LOG_DIR/frontend-${FRONTEND_PORT}.log"

terminate_tree() {
  local pid="$1"
  local child
  if [[ -z "$pid" ]] || ! kill -0 "$pid" >/dev/null 2>&1; then
    return 0
  fi

  while IFS= read -r child; do
    [[ -n "$child" ]] && terminate_tree "$child"
  done < <(pgrep -P "$pid" 2>/dev/null || true)

  kill "$pid" >/dev/null 2>&1 || true
}

cleanup() {
  local code=$?
  trap - INT TERM EXIT
  info "Stopping demo services..."
  terminate_tree "$FRONTEND_PID"
  terminate_tree "$BACKEND_PID"
  wait "$FRONTEND_PID" >/dev/null 2>&1 || true
  wait "$BACKEND_PID" >/dev/null 2>&1 || true
  exit "$code"
}
trap cleanup INT TERM EXIT

info "Project root: $PROJECT_ROOT"
info "CASE_ROOT: $CASE_ROOT_ABS"
info "Detected case packages: ${#CASE_DIRS[@]}"
info "OUTPUT_OVERWRITE: $OUTPUT_OVERWRITE"
info "Starting FastAPI backend with .venv/bin/python..."

.venv/bin/python -m uvicorn backend.main:app \
  --host "$APP_HOST" \
  --port "$BACKEND_PORT" \
  >"$BACKEND_LOG" 2>&1 &
BACKEND_PID="$!"

health_url="http://${APP_HOST}:${BACKEND_PORT}/api/health"
health_ok=0
for _ in {1..40}; do
  if ! kill -0 "$BACKEND_PID" >/dev/null 2>&1; then
    warn "Backend exited early. Log:"
    sed -n '1,160p' "$BACKEND_LOG" >&2 || true
    die "FastAPI backend failed to start."
  fi
  if .venv/bin/python - "$health_url" <<'PY' >/dev/null 2>&1
import json
import sys
import urllib.request

url = sys.argv[1]
with urllib.request.urlopen(url, timeout=1.0) as response:
    payload = json.load(response)
if payload.get("status") != "ok":
    raise SystemExit(1)
PY
  then
    health_ok=1
    break
  fi
  sleep 0.25
done

if [[ "$health_ok" != "1" ]]; then
  warn "Backend health check failed at $health_url. Log:"
  sed -n '1,160p' "$BACKEND_LOG" >&2 || true
  die "FastAPI backend did not become healthy in time."
fi

info "Backend health check passed: $health_url"
info "Starting Vite frontend with Linux/WSL npm..."

(
  cd frontend
  npm run dev -- --host "$APP_HOST" --port "$FRONTEND_PORT"
) >"$FRONTEND_LOG" 2>&1 &
FRONTEND_PID="$!"

sleep 1
if ! kill -0 "$FRONTEND_PID" >/dev/null 2>&1; then
  warn "Frontend exited early. Log:"
  sed -n '1,160p' "$FRONTEND_LOG" >&2 || true
  die "Vite frontend failed to start."
fi

cat <<EOF

AD dMRI edge demo is running.

Backend:  http://${APP_HOST}:${BACKEND_PORT}
Frontend: http://${APP_HOST}:${FRONTEND_PORT}

Backend log:  $BACKEND_LOG
Frontend log: $FRONTEND_LOG

This edge demo loads prepared local case packages and runs simplified DTI/V1/RI
post-processing. It does not run full DisC-Diff, FreeSurfer, or whole-brain
registration on the edge device.

Press Ctrl+C to stop both services.
EOF

wait "$BACKEND_PID" "$FRONTEND_PID"
