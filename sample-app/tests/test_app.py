"""Unit tests for the sample Flask app.

These are executed inside the container by the Jenkins 'Run Tests' stage:
    docker run --rm <image> python -m unittest discover -s tests -v
"""
import os
import sys
import unittest

# Make app.py importable regardless of cwd
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import app as app_module  # noqa: E402


class SampleAppTest(unittest.TestCase):
    def setUp(self):
        app_module.app.config["TESTING"] = True
        self.client = app_module.app.test_client()

    def test_index(self):
        resp = self.client.get("/")
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertEqual(data["service"], "sample-app")
        self.assertEqual(data["status"], "running")

    def test_health(self):
        resp = self.client.get("/health")
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertEqual(data["status"], "ok")
        self.assertIn("uptime_seconds", data)

    def test_version(self):
        resp = self.client.get("/version")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("version", resp.get_json())


if __name__ == "__main__":
    unittest.main()
