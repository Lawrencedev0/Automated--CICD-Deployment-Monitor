#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────
# deploy_remote.sh — Deploy the sample-app container to a remote
# EC2 host over SSH (fallback when Jenkins cannot use Docker
# out of Docker, or when deploying to a separate instance).
#
# Usage:
#   AWS_REGION=us-east-1 EC2_PUBLIC_IP=1.2.3.4 \
#   SSH_KEY_PATH=~/.ssh/ci_cd_key.pem IMAGE_NAME=sample-app \
#   ./scripts/deploy_remote.sh
# ─────────────────────────────────────────────────────────────
set -euo pipefail

: "${EC2_PUBLIC_IP:?Set EC2_PUBLIC_IP}"
: "${SSH_KEY_PATH:?Set SSH_KEY_PATH}"
: "${IMAGE_NAME:=sample-app}"
: "${IMAGE_TAG:=latest}"
: "${SSH_USER:=ubuntu}"
: "${APP_PORT:=5000}"

ssh -i "${SSH_KEY_PATH}" -o StrictHostKeyChecking=no "${SSH_USER}@${EC2_PUBLIC_IP}" <<EOF
    set -e
    echo "→ Pulling image ${IMAGE_NAME}:${IMAGE_TAG}"
    docker pull "${IMAGE_NAME}:${IMAGE_TAG}" 2>/dev/null || echo "  (image local or pull skipped)"

    echo "→ Stopping old container (if any)"
    docker rm -f "${IMAGE_NAME}" 2>/dev/null || true

    echo "→ Starting new container on port ${APP_PORT}"
    docker run -d --name "${IMAGE_NAME}" \
        -p "${APP_PORT}:5000" \
        --restart unless-stopped \
        "${IMAGE_NAME}:${IMAGE_TAG}"

    echo "→ Verifying health endpoint"
    for i in \$(seq 1 10); do
        STATUS=\$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:${APP_PORT}/health" || true)
        if [ "\${STATUS}" = "200" ]; then
            echo "Health check passed (HTTP 200)"
            exit 0
        fi
        echo "Attempt \$i: HTTP \${STATUS} — retrying..."
        sleep 3
    done
    echo "Health check FAILED" >&2
    exit 1
EOF

echo "✅ Deployment completed on ${EC2_PUBLIC_IP}"

