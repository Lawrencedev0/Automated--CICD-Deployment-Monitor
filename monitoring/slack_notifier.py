"""Slack notification client built on the Incoming Webhook HTTP API."""
import json
import logging

import requests

from config import config

logger = logging.getLogger(__name__)

# Colors matching Slack's message conventions
COLOR_SUCCESS = "good"
COLOR_FAILURE = "danger"
COLOR_WARNING = "warning"


class SlackNotifier:
    """Thin wrapper around the Slack Incoming Webhook endpoint."""

    def __init__(self, webhook_url: str = None, channel: str = None,
                 username: str = None, icon: str = None):
        self.webhook_url = webhook_url or config.SLACK_WEBHOOK_URL
        self.channel = channel or config.SLACK_CHANNEL
        self.username = username or config.SLACK_USERNAME
        self.icon = icon or config.SLACK_ICON

    def _post(self, payload: dict):
        """Send an attachment payload to the webhook. Never raises."""
        if not self.webhook_url:
            logger.warning("SLACK_WEBHOOK_URL not set — skipping notification: %s",
                           payload)
            return False

        if self.channel:
            payload["channel"] = self.channel

        try:
            resp = requests.post(
                self.webhook_url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=10,
            )
            resp.raise_for_status()
            logger.info("Slack notification sent (%s)", resp.status_code)
            return True
        except requests.RequestException as exc:
            logger.error("Failed to send Slack notification: %s", exc)
            return False

    def _send(self, title: str, text: str, color: str, fields: list = None):
        attachment = {
            "color": color,
            "title": title,
            "text": text,
            "ts": int(__import__("time").time()),
        }
        if fields:
            attachment["fields"] = fields
        payload = {
            "username": self.username,
            "icon_emoji": self.icon,
            "attachments": [attachment],
        }
        return self._post(payload)

    def send_success(self, title: str, text: str = "", fields: list = None):
        return self._send(title, text, COLOR_SUCCESS, fields)

    def send_failure(self, title: str, text: str = "", fields: list = None):
        return self._send(title, text, COLOR_FAILURE, fields)

    def send_warning(self, title: str, text: str = "", fields: list = None):
        return self._send(title, text, COLOR_WARNING, fields)

    def send_test(self):
        """One-off test message used by scripts/test_slack.sh."""
        return self.send_success("CI/CD Monitor",
                                 "Test message — your webhook is working!")


def build_build_result_fields(build: dict) -> list:
    """Convert a Jenkins build dict into Slack attachment fields."""
    return [
        {"title": "Job", "value": build.get("job", ""), "short": True},
        {"title": "Build #", "value": str(build.get("number", "")), "short": True},
        {"title": "Result", "value": build.get("result", "UNKNOWN"), "short": True},
        {"title": "URL", "value": build.get("url", ""), "short": False},
    ]
