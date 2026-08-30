"""Central configuration for the CI/CD monitoring agent.

All settings are read from environment variables so the same code can run
both inside Docker (via .env) and locally (via exported vars).
"""
import os


def _env(name: str, default: str = "") -> str:
    """Read an env var, returning the default when empty/absent."""
    return os.environ.get(name, default).strip() or default


class Config:
    """Bundle of all tunable settings for the monitor."""

    # ── Slack ────────────────────────────────────────────────
    SLACK_WEBHOOK_URL = _env("SLACK_WEBHOOK_URL")
    SLACK_CHANNEL = _env("SLACK_CHANNEL")
    SLACK_USERNAME = _env("SLACK_USERNAME", "ci-cd-monitor")
    SLACK_ICON = _env("SLACK_ICON", ":robot_face:")

    # ── Jenkins ──────────────────────────────────────────────
    JENKINS_URL = _env("JENKINS_URL", "http://localhost:8080")
    JENKINS_USER = _env("JENKINS_USER")
    JENKINS_TOKEN = _env("JENKINS_TOKEN")
    JENKINS_JOB = _env("JENKINS_JOB", "sample-app")

    # ── Application health ───────────────────────────────────
    APP_HEALTH_URL = _env("APP_HEALTH_URL", "http://localhost:5000/health")
    HEALTH_EXPECT_STATUS = int(_env("HEALTH_EXPECT_STATUS", "200"))
    HEALTH_TIMEOUT = float(_env("HEALTH_TIMEOUT", "10"))

    # ── Monitor behaviour ────────────────────────────────────
    POLL_INTERVAL = float(_env("POLL_INTERVAL", "30"))

    @property
    def jenkins_auth(self):
        """Return an (user, token) tuple or None when not configured."""
        if self.JENKINS_USER and self.JENKINS_TOKEN:
            return (self.JENKINS_USER, self.JENKINS_TOKEN)
        return None

    def validate(self) -> list:
        """Return a list of missing required settings (empty if OK)."""
        missing = []
        if not self.SLACK_WEBHOOK_URL:
            missing.append("SLACK_WEBHOOK_URL")
        return missing


# Convenience singleton so modules can import `config` directly.
config = Config()
