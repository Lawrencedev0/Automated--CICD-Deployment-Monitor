#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────
# run_monitor.sh — Run the Python deployment monitor locally
# (outside Docker) for development / debugging.
#
# Usage:
#   export SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...
#   bash scripts/run_monitor.sh
# ─────────────────────────────────────────────────────────────
set -e

cd "$(dirname "$0")/.."

# Load .env if present
if [ -f ".env" ]; then
    echo "→ Loading environment from .env"
    set -a
    # shellcheck disable=SC1091
    source .env
    set +a
fi

echo "→ Installing dependencies (monitoring/requirements.txt)"
python -m pip install -q --user -r monitoring/requirements.txt

echo "→ Starting deployment monitor (Ctrl+C to stop)"
PYTHONPATH=monitoring python -m deployment_monitor

