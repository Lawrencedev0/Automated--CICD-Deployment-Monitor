"""Minimal Jenkins REST API client for monitoring builds."""
import logging

import requests

from config import config

logger = logging.getLogger(__name__)


class JenkinsClient:
    """Client for the Jenkins remote-access API (api/json)."""

    def __init__(self, url: str = None, username: str = None,
                 token: str = None):
        self.base_url = (url or config.JENKINS_URL).rstrip("/")
        self.username = username or config.JENKINS_USER
        self.token = token or config.JENKINS_TOKEN
        self._auth = (self.username, self.token) if self.username and self.token else None

    def _get(self, path: str, params: dict = None) -> dict:
        url = f"{self.base_url}{path}"
        try:
            resp = requests.get(url, params=params, auth=self._auth, timeout=15)
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException as exc:
            logger.error("Jenkins request failed for %s: %s", url, exc)
            return {}

    def get_job(self, job: str = None) -> dict:
        """Fetch job metadata (last build, color, in_queue, etc.)."""
        job = job or config.JENKINS_JOB
        return self._get(f"/job/{job}/api/json")

    def get_last_build(self, job: str = None) -> dict:
        """Fetch the last finished build for a job."""
        job = job or config.JENKINS_JOB
        data = self.get_job(job)
        number = data.get("lastBuild", {}).get("number")
        if not number:
            return {}
        return self.get_build(job, number)

    def get_last_failed_build(self, job: str = None) -> dict:
        """Fetch the most recent failed build number, if any."""
        job = job or config.JENKINS_JOB
        data = self.get_job(job)
        number = data.get("lastFailedBuild", {}).get("number")
        if not number:
            return {}
        return self.get_build(job, number)

    def get_build(self, job: str, number: int) -> dict:
        """Fetch a specific build's details."""
        return self._get(f"/job/{job}/{number}/api/json")

    def job_is_healthy(self, job: str = None) -> bool:
        """True when the job exists and its last build succeeded."""
        job = job or config.JENKINS_JOB
        data = self.get_job(job)
        if not data:
            return False
        last = data.get("lastBuild")
        if not last:
            return True  # no builds yet = nothing broken
        build = self.get_build(job, last["number"])
        return build.get("result") == "SUCCESS"
