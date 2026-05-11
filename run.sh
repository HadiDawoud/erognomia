#!/usr/bin/env bash
# Run Ergonomia: FastAPI backend + Next.js frontend in one terminal.
# Usage: ./run.sh        (from repo root, after: chmod +x run.sh)

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

if [[ -f "$ROOT/.env" ]]; then
  set -a
  # shellcheck disable=SC1091
  source "$ROOT/.env"
  set +a
fi

API_HOST="${API_HOST:-127.0.0.1}"
API_PORT="${API_PORT:-8001}"
export NEXT_PUBLIC_API_BASE="${NEXT_PUBLIC_API_BASE:-http://127.0.0.1:${API_PORT}}"
export HF_HUB_OFFLINE="${HF_HUB_OFFLINE:-1}"
export TRANSFORMERS_OFFLINE="${TRANSFORMERS_OFFLINE:-1}"

PYTHON_BIN=""
if [[ -x "$ROOT/.venv/bin/python" ]]; then
  PYTHON_BIN="$ROOT/.venv/bin/python"
elif command -v python3 >/dev/null 2>&1; then
  PYTHON_BIN="$(command -v python3)"
else
  echo "error: need python3 or $ROOT/.venv/bin/python" >&2
  exit 1
fi

if [[ -x "$ROOT/.venv/bin/uvicorn" ]]; then
  UVICORN=( "$ROOT/.venv/bin/uvicorn" )
elif "$PYTHON_BIN" -m uvicorn --help >/dev/null 2>&1; then
  UVICORN=( "$PYTHON_BIN" -m uvicorn )
else
  echo "error: uvicorn not found — run: pip install -r requirements.txt (preferably in .venv)" >&2
  exit 1
fi

if ! command -v curl >/dev/null 2>&1; then
  :
elif curl -fsS "${OLLAMA_BASE_URL:-http://127.0.0.1:11434}/api/tags" >/dev/null 2>&1; then
  echo "ollama: daemon reachable."
else
  echo "hint: start Ollama so chat replies work (e.g. ollama serve, model pulled)." >&2
fi

PIDS=()

cleanup() {
  local pid
  for pid in "${PIDS[@]}"; do
    if kill -0 "$pid" 2>/dev/null; then
      kill "$pid" 2>/dev/null || true
    fi
  done
}

trap cleanup EXIT INT TERM

echo "API: http://${API_HOST}:${API_PORT}/  docs: http://${API_HOST}:${API_PORT}/docs"
"${UVICORN[@]}" src.api.main:app --reload --host "$API_HOST" --port "$API_PORT" &
PIDS+=( "$!" )

if [[ -f "$ROOT/frontend/package.json" ]]; then
  echo "UI: http://localhost:3000 (talks to API on port ${API_PORT})"
  (
    cd "$ROOT/frontend"
    if [[ ! -d node_modules ]]; then
      npm install
    fi
    npm run dev
  ) &
  PIDS+=( "$!" )
else
  echo "warning: frontend/package.json missing — only starting API." >&2
fi

echo "Press Ctrl+C to stop everything."
wait
