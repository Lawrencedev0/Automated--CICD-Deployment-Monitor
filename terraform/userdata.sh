#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────
# EC2 user_data — bootstraps the CI/CD monitoring host.
# Installs Docker, Docker Compose, Git, and clones the project.
# ─────────────────────────────────────────────────────────────
set -euo pipefail

exec > /var/log/cloud-init-output.log 2>&1

export DEBIAN_FRONTEND=noninteractive

echo "==> Updating apt"
apt-get update -y
apt-get upgrade -y

echo "==> Installing base packages"
apt-get install -y \
    ca-certificates \
    curl \
    gnupg \
    git \
    unzip \
    python3 \
    python3-pip \
    jq

echo "==> Installing Docker (official repo)"
install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg \
    | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
chmod a+r /etc/apt/keyrings/docker.gpg

echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
  https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" \
  > /etc/apt/sources.list.d/docker.list

apt-get update -y
apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

echo "==> Enabling Docker on boot"
systemctl enable docker
systemctl start docker

echo "==> Adding ubuntu user to docker group"
usermod -aG docker ubuntu

echo "==> Installing Docker Compose v2 plugin"
docker compose version

echo "==> Cloning project repository"
if [ -n "${repo_url}" ]; then
    git clone "${repo_url}" /opt/cicd-monitoring || echo "Clone failed — skipping"
else
    echo "repo_url not set — skipping clone (deploy files manually)."
fi

echo "==> Creating project directory"
mkdir -p /opt/cicd-monitoring

echo "==> Bootstrap complete"
echo "✔ Docker: $(docker --version)"
echo "✔ Compose: $(docker compose version)"
echo "✔ Instance ready. SSH with: ssh ubuntu@<PUBLIC_IP>"
