"""Sample Flask app used as the deployment target for the CI/CD pipeline.

Exposes:
  GET /          -> simple greeting
  GET /health    -> JSON health probe (used by the monitoring agent)
  GET /version   -> read from env VERSION (populated by the pipeline)
"""
import os
import time

from flask import Flask, jsonify

app = Flask(__name__)

START_TIME = time.time()
VERSION = os.environ.get("VERSION", "dev")


@app.route("/")
def index():
    return jsonify({
        "service": "sample-app",
        "status": "running",
        "version": VERSION,
    })


@app.route("/health")
def health():
    return jsonify({
        "status": "ok",
        "uptime_seconds": round(time.time() - START_TIME, 2),
        "version": VERSION,
    })


@app.route("/version")
def version():
    return jsonify({"version": VERSION})


if __name__ == "__main__":
    # Host 0.0.0.0 so the container is reachable from outside.
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
