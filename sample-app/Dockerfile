# ─────────────────────────────────────────────────────────────
# Sample Flask application container
#   Built & deployed by the Jenkins pipeline.
# ─────────────────────────────────────────────────────────────
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY app.py .

# Non-root user for security
RUN useradd --create-home --uid 1000 appuser \
    && chown -R appuser:appuser /app
USER appuser

EXPOSE 5000

# Pass VERSION at runtime (e.g. -e VERSION=1.0.0)
ENV VERSION=dev

CMD ["python", "app.py"]
