#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────
# test_slack.sh — Send a test notification to Slack to verify
# the webhook URL is configured correctly.
#
# Usage:
#   SLACK_WEBHOOK_URL=https://hooks.slack.com/services/... bash scripts/test_slack.sh
# ─────────────────────────────────────────────────────────────
set -euo pipefail

: "${SLACK_WEBHOOK_URL:?Set SLACK_WEBHOOK_URL}"

SLACK_CHANNEL="${SLACK_CHANNEL:-#ci-cd-notifications}"

echo "→ Sending test message to ${SLACK_CHANNEL} ..."

RESPONSE=$(curl -s -X POST -H 'Content-type: application/json' \
    --data "{\"channel\":\"${SLACK_CHANNEL}\",\"username\":\"ci-cd-monitor\",\"icon_emoji\":\":robot_face:\",\"text\":\":white_check_mark: *CI/CD Monitor* test message — your webhook is working!\"}" \
    "${SLACK_WEBHOOK_URL}")

if [ "${RESPONSE}" = "ok" ]; then
    echo "✅ Test message sent successfully."
else
    echo "❌ Slack responded: ${RESPONSE}" >&2
    exit 1
fi
