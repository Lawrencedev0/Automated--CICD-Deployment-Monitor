# ─────────────────────────────────────────────────────────────
# Python Deployment Monitoring Agent
#   Lightweight image that continuously watches Jenkins + app
#   health and pushes Slack notifications.
# ─────────────────────────────────────────────────────────────
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# Install dependencies first for better layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the monitoring package
COPY config.py slack_notifier.py health_checker.py jenkins_client.py deployment_monitor.py ./

# Run non-root (security best practice)
RUN useradd --create-home --uid 1000 monitor \
    && chown -R monitor:monitor /app
USER monitor

CMD ["python", "deployment_monitor.py"]
