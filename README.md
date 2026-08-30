# Automated--CICD-Deployment-Monitor
Automated CI/CD Deployment Monitoring System using Jenkins, Docker, Python, AWS EC2, and Slack Notifications.
=======
# Automated CI/CD Deployment Monitoring System

A production-ready blueprint that combines **Jenkins**, **Docker**, **Python**, **AWS EC2**, and **Slack Notifications** to build, test, deploy, and continuously monitor a containerized application — with real-time alerts on every build, deploy, and health-check event.

---

## Architecture

```
                           ┌──────────────────────────────────────────────┐
                           │                AWS EC2 Instance             │
                           │                                              │
   Git Push ────────────►  │  ┌───────────────┐     ┌─────────────────┐  │
                           │  │    Jenkins    │     │  Python Monitor │  │
   Developer               │  │  (Docker)     │     │  (Docker)       │  │
                           │  │               │     │                 │  │
                           │  │ • Checkout    │     │ • Poll Jenkins  │  │
                           │  │ • Build       │     │   API           │  │
                           │  │ • Test        │     │ • Health check  │  │
                           │  │ • Push Image  │     │   app:5000/health│ │
                           │  │ • Deploy      │     │ • Alert on      │  │
                           │  │   (docker run)│     │   failures      │  │
                           │  └──────┬────────┘     └────────┬────────┘  │
                           │         │                       │           │
                           │         └───────────┬───────────┘           │
                           │                     │                       │
                           │            ┌────────▼────────┐              │
                           │            │  Sample Flask   │              │
                           │            │  App Container  │              │
                           │            │  :5000/health   │              │
                           │            └─────────────────┘              │
                           └─────────────────────┬────────────────────────┘
                                                 │ HTTP (Slack Webhook)
                                                 ▼
                                      ┌─────────────────────┐
                                      │   Slack Channel     │
                                      │  #ci-cd-notifications │
                                      └─────────────────────┘
```

### Data Flow
1. **Developer** pushes code → triggers the **Jenkins** pipeline (via SCM hook or polling).
2. **Jenkins** builds a Docker image, runs tests, pushes to a registry, and deploys to the EC2 host.
3. The **Python Monitoring Agent** polls the Jenkins REST API and performs HTTP health checks against the deployed app.
4. Any success, failure, or degradation triggers a **Slack notification** via webhook.

---

## Project Structure

```
AUTOMATING/
├── README.md
├── TODO.md
├── .env.example
├── docker-compose.yml
├── jenkins/
│   ├── Jenkinsfile          # Declarative CI/CD pipeline
│   └── plugins.txt          # Jenkins plugins to install
├── monitoring/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── config.py            # Env-driven configuration
│   ├── slack_notifier.py    # Slack webhook client
│   ├── health_checker.py    # HTTP health checks
│   ├── jenkins_client.py    # Jenkins REST API client
│   └── deployment_monitor.py# Main monitoring loop (entrypoint)
├── sample-app/
│   ├── app.py               # Demo Flask app with /health
│   ├── requirements.txt
│   └── Dockerfile
├── scripts/
│   ├── deploy_remote.sh     # SSH-based remote deploy helper
│   ├── run_monitor.sh       # Run monitoring agent locally
│   └── test_slack.sh        # Send a test Slack message
├── terraform/
│   ├── main.tf              # EC2 instance + security groups
│   ├── variables.tf
│   ├── outputs.tf
│   └── userdata.sh          # Bootstraps Docker + Compose
└── tests/
    └── test_monitoring.py   # Unit tests for monitoring modules
```

---

## Prerequisites

- AWS account + `awscli` configured (`aws configure`)
- Terraform ≥ 1.0
- Docker + Docker Compose (local or on EC2)
- Slack workspace with an **Incoming Webhook** URL
- A Git repo hosting the `sample-app` (or your real app)

---

## Quick Start

### 1. Provision AWS EC2 with Terraform

```bash
cd terraform
terraform init
terraform plan
terraform apply -auto-approve
```

The `userdata.sh` script installs Docker, Docker Compose, and Git, then clones
your repo (configure the repo URL in `variables.tf`).

### 2. Configure environment variables

```bash
cp .env.example .env
# Edit .env -> set SLACK_WEBHOOK_URL, JENKINS_URL, credentials, etc.
```

### 3. Start Jenkins + Monitoring Agent

```bash
docker-compose up -d --build
```

### 4. Unlock & configure Jenkins

- Access `http://<EC2_PUBLIC_IP>:8080`
- Initial admin password:
  ```bash
  docker exec jenkins cat /var/jenkins_home/secrets/initialAdminPassword
  ```
- Install the plugins listed in `jenkins/plugins.txt` (or use the provisioning
  script approach), create a job using the `Jenkinsfile` (Pipeline → SCM → your repo).

### 5. Verify Slack notifications

```bash
bash scripts/test_slack.sh
# -> Should post "Test message" to your Slack channel
```

### 6. Run the pipeline

Push a commit to the repo (or click *Build Now*). Watch:

```
Checkout -> Build Docker Image -> Run Tests -> Push Image -> Deploy -> Health Check
```

The Python monitor and Jenkins `post` blocks will report status to Slack.

---

## Python Monitoring Agent

Run locally (outside Docker) for development:

```bash
export SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...
export APP_HEALTH_URL=http://localhost:5000/health
bash scripts/run_monitor.sh
```

### What it monitors
- **Jenkins jobs/builds** — polls `/api/json`, detects failures and tracks the last build.
- **App health** — GET `/health` with configurable timeout & expected status code.
- **Slack alerts** — posts on build failure, deployment completion, and health-check
  recovery/degradation.

### Configuration (env vars)

| Variable | Description | Default |
|----------|-------------|---------|
| `SLACK_WEBHOOK_URL` | Slack incoming webhook URL | *(required)* |
| `SLACK_CHANNEL` | Slack channel override | unset |
| `JENKINS_URL` | Base Jenkins URL | `http://localhost:8080` |
| `JENKINS_USER` | Jenkins API username | unset |
| `JENKINS_TOKEN` | Jenkins API token | unset |
| `JENKINS_JOB` | Job name to monitor | `sample-app` |
| `APP_HEALTH_URL` | Health endpoint of deployed app | `http://localhost:5000/health` |
| `HEALTH_EXPECT_STATUS` | Expected HTTP status | `200` |
| `POLL_INTERVAL` | Monitor loop interval (s) | `30` |

---

## Jenkinsfile Pipeline Stages

| Stage | Description |
|-------|-------------|
| `Checkout` | Clone the application source from SCM |
| `Build Docker Image` | `docker build` the sample app |
| `Run Tests` | Execute app smoke/unit tests inside container |
| `Push Image` | Tag & push to registry (Docker Hub / ECR) |
| `Deploy` | Stop old container, run new one on the host |
| `Health Check` | Verify `/health` responds 200 after deploy |
| `post` | Always notifies Slack with build result |

---

## Terraform Resources

- **AWS EC2** `t3.medium` (sufficient for Jenkins + containers)
- **Security Group** — allows SSH (22), Jenkins (8080), App (5000), Monitor API (unused externally)
- **IAM Profile** — optional ECR access
- **user_data** — bootstraps Docker, Compose, Git

---

## Testing

```bash
pip install -r monitoring/requirements.txt
pytest tests/ -v
```

---

## Extending the System

- **Add ECR/Registry auth** — replace the `Push Image` stage with `aws ecr` commands.
- **Scale monitoring** — point the agent at multiple `JENKINS_JOB`s or add Prometheus/Grafana.
- **Blue/Green deploys** — extend the `Deploy` stage with load-balancer weighting.
- **Secret management** — move credentials to AWS Secrets Manager / Jenkins Credentials store.

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| Jenkins can't reach Docker | Ensure Jenkins container runs `privileged: true` and mounts `/var/run/docker.sock`. |
| Slack messages not received | Verify webhook URL in `.env` and run `scripts/test_slack.sh`. |
| Terraform `user_data` not running | Check `/var/log/cloud-init-output.log` on the EC2 instance. |
| Health check fails after deploy | Confirm container exposes port 5000 and `APP_HEALTH_URL` matches. |

