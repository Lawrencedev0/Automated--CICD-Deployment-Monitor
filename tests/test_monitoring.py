"""Unit tests for the Python monitoring modules.

Run with:
    pip install -r monitoring/requirements.txt
    pytest tests/ -v
"""
import os
import sys
import unittest
from unittest import mock

# Make the monitoring package importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "monitoring"))

from config import Config  # noqa: E402
from health_checker import HealthChecker  # noqa: E402
from jenkins_client import JenkinsClient  # noqa: E402
from slack_notifier import SlackNotifier, build_build_result_fields  # noqa: E402


class ConfigTest(unittest.TestCase):
    def test_defaults(self):
        cfg = Config()
        self.assertEqual(cfg.JENKINS_URL, "http://localhost:8080")
        self.assertEqual(cfg.HEALTH_EXPECT_STATUS, 200)
        self.assertEqual(cfg.POLL_INTERVAL, 30.0)

    def test_validate_missing_webhook(self):
        cfg = Config()
        cfg.SLACK_WEBHOOK_URL = ""
        self.assertIn("SLACK_WEBHOOK_URL", cfg.validate())

    def test_validate_ok(self):
        cfg = Config()
        cfg.SLACK_WEBHOOK_URL = "https://hooks.slack.com/services/x"
        self.assertEqual(cfg.validate(), [])

    def test_jenkins_auth(self):
        cfg = Config()
        cfg.JENKINS_USER = "u"
        cfg.JENKINS_TOKEN = "t"
        self.assertEqual(cfg.jenkins_auth, ("u", "t"))


class SlackNotifierTest(unittest.TestCase):
    def setUp(self):
        self.notifier = SlackNotifier(
            webhook_url="https://hooks.slack.com/services/test",
            channel="#ci",
        )

    @mock.patch("slack_notifier.requests.post")
    def test_send_success(self, mock_post):
        mock_post.return_value.status_code = 200
        mock_post.return_value.raise_for_status.return_value = None
        ok = self.notifier.send_success("Title", "Body")
        self.assertTrue(ok)
        payload = mock_post.call_args.kwargs["json"]
        self.assertEqual(payload["channel"], "#ci")
        self.assertEqual(payload["attachments"][0]["color"], "good")
        self.assertEqual(payload["attachments"][0]["title"], "Title")

    @mock.patch("slack_notifier.requests.post")
    def test_send_failure(self, mock_post):
        mock_post.return_value.status_code = 200
        mock_post.return_value.raise_for_status.return_value = None
        ok = self.notifier.send_failure("Down", "App is down")
        self.assertTrue(ok)
        self.assertEqual(mock_post.call_args.kwargs["json"]["attachments"][0]["color"],
                         "danger")

    @mock.patch("slack_notifier.requests.post")
    def test_post_exception(self, mock_post):
        mock_post.side_effect = Exception("network down")
        ok = self.notifier.send_success("T", "B")
        self.assertFalse(ok)

    def test_no_webhook(self):
        n = SlackNotifier(webhook_url="")
        self.assertFalse(n.send_success("T", "B"))


class HealthCheckerTest(unittest.TestCase):
    def setUp(self):
        self.checker = HealthChecker(url="http://x/health", expect_status=200)

    @mock.patch("health_checker.requests.get")
    def test_check_ok(self, mock_get):
        mock_get.return_value.status_code = 200
        self.assertTrue(self.checker.check())

    @mock.patch("health_checker.requests.get")
    def test_check_fail_status(self, mock_get):
        mock_get.return_value.status_code = 500
        self.assertFalse(self.checker.check())

    @mock.patch("health_checker.requests.get")
    def test_check_exception(self, mock_get):
        mock_get.side_effect = Exception("boom")
        self.assertFalse(self.checker.check())

    def test_transition(self):
        checker = HealthChecker(url="http://x/health", expect_status=200)
        with mock.patch("health_checker.requests.get") as m:
            m.return_value.status_code = 500
            healthy, recovered = checker.check_with_transition()
            self.assertFalse(healthy)
            self.assertFalse(recovered)

            m.return_value.status_code = 200
            healthy, recovered = checker.check_with_transition()
            self.assertTrue(healthy)
            self.assertTrue(recovered)  # recovered from prior failure


class JenkinsClientTest(unittest.TestCase):
    @mock.patch("jenkins_client.requests.get")
    def test_get_job(self, mock_get):
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {"name": "sample-app"}
        client = JenkinsClient(url="http://jenkins:8080")
        data = client.get_job("sample-app")
        self.assertEqual(data["name"], "sample-app")
        mock_get.assert_called_once_with(
            "http://jenkins:8080/job/sample-app/api/json",
            params=None, auth=None, timeout=15)

    @mock.patch("jenkins_client.requests.get")
    def test_job_is_healthy(self, mock_get):
        # job meta -> lastBuild name, then build -> SUCCESS
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.side_effect = [
            {"lastBuild": {"number": 5}},
            {"result": "SUCCESS"},
        ]
        client = JenkinsClient(url="http://jenkins:8080")
        self.assertTrue(client.job_is_healthy("sample-app"))

    @mock.patch("jenkins_client.requests.get")
    def test_job_is_unhealthy(self, mock_get):
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.side_effect = [
            {"lastBuild": {"number": 5}},
            {"result": "FAILURE"},
        ]
        client = JenkinsClient(url="http://jenkins:8080")
        self.assertFalse(client.job_is_healthy("sample-app"))

    @mock.patch("jenkins_client.requests.get")
    def test_no_builds_is_healthy(self, mock_get):
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {"lastBuild": None}
        client = JenkinsClient(url="http://jenkins:8080")
        self.assertTrue(client.job_is_healthy("sample-app"))


class BuildFieldsTest(unittest.TestCase):
    def test_fields(self):
        build = {"job": "sample-app", "number": 3, "result": "SUCCESS", "url": "x"}
        fields = build_build_result_fields(build)
        values = {f["title"]: f["value"] for f in fields}
        self.assertEqual(values["Job"], "sample-app")
        self.assertEqual(values["Build #"], "3")
        self.assertEqual(values["Result"], "SUCCESS")


if __name__ == "__main__":
    unittest.main()
