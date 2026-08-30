"""HTTP health-checker for the deployed application."""
import logging
import time

import requests

from config import config

logger = logging.getLogger(__name__)


class HealthChecker:
    """Performs periodic HTTP checks against the app's health endpoint."""

    def __init__(self, url: str = None, expect_status: int = None,
                 timeout: float = None):
        self.url = url or config.APP_HEALTH_URL
        self.expect_status = expect_status or config.HEALTH_EXPECT_STATUS
        self.timeout = timeout or config.HEALTH_TIMEOUT
        self._last_ok = None  # None = never checked yet

    def check(self) -> bool:
        """Perform one health check. Returns True when healthy, False otherwise."""
        logger.info("Health checking %s", self.url)
        try:
            resp = requests.get(self.url, timeout=self.timeout)
            ok = resp.status_code == self.expect_status
            logger.info("Health check %s -> HTTP %s",
                        "PASSED" if ok else "FAILED", resp.status_code)
            return ok
        except requests.RequestException as exc:
            logger.warning("Health check error: %s", exc)
            return False

    def check_with_transition(self) -> tuple:
        """Health check with transition tracking.

        Returns (healthy, just_recovered) where just_recovered is True when the
        app transitions from unhealthy -> healthy.
        """
        healthy = self.check()
        recovered = bool(healthy and self._last_ok is False)
        self._last_ok = healthy
        return healthy, recovered

    def wait_until_ready(self, attempts: int = 10, delay: float = 3.0,
                         on_attempt=None) -> bool:
        """Poll until the app is healthy or attempts run out."""
        for i in range(1, attempts + 1):
            if self.check():
                return True
            if on_attempt:
                on_attempt(i)
            time.sleep(delay)
        return False
