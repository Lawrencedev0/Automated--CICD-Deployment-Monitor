"""Main entrypoint for the deployment monitoring agent.

Continuously:
  1. Polls the Jenkins job for build failures.
  2. Health-checks the deployed application.
  3. Sends Slack notifications on failures, recoveries, and staleness.

Designed to run both as a Docker container (docker-compose) and locally
(scripts/run_monitor.sh).
"""
import logging
import sys
import time

from config import config
from health_checker import HealthChecker
from jenkins_client import JenkinsClient
from slack_notifier import SlackNotifier, build_build_result_fields

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("deployment_monitor")


def validate_config_or_exit() -> None:
    """Exit gracefully when required config is missing."""
    missing = config.validate()
    if missing:
        logger.error("Missing required environment variables: %s", ", ".join(missing))
        logger.error("See .env.example for the full list.")
        sys.exit(1)


def notify_build_failure(notifier: SlackNotifier, client: JenkinsClient) -> None:
    """Send a Slack message describing the latest failed build."""
    failed = client.get_last_failed_build()
    if not failed:
        logger.warning("Jenkins reports failure but no failed build found.")
        notifier.send_failure("Jenkins build failure",
                              "The job is failing but no failed build details were found.")
        return
    notifier.send_failure(
        title="Jenkins build failure",
        text=f"Job *{config.JENKINS_JOB}* failed",
        fields=build_build_result_fields(failed),
    )


def monitor_loop(notifier: SlackNotifier, client: JenkinsClient,
                 checker: HealthChecker, interval: float) -> None:
    """Run the monitoring loop forever (until interrupted)."""
    app_healthy = True
    logger.info("Monitoring started. Jenkins=%s job=%s app=%s interval=%ss",
                config.JENKINS_URL, config.JENKINS_JOB,
                config.APP_HEALTH_URL, interval)

    while True:
        try:
            # 1) Jenkins build health
            if not client.job_is_healthy():
                notifier.send_warning(
                    title="Jenkins job unhealthy",
                    text=f"Job *{config.JENKINS_JOB}* is not currently healthy.",
                )
                notify_build_failure(notifier, client)

            # 2) Application health
            healthy, recovered = checker.check_with_transition()
            if not healthy:
                if app_healthy:  # only alert on state change
                    app_healthy = False
                    notifier.send_failure(
                        title="Application DOWN",
                        text=f"Health check failed for {config.APP_HEALTH_URL}",
                    )
            else:
                if recovered:
                    notifier.send_success(
                        title="Application recovered",
                        text=f"{config.APP_HEALTH_URL} is healthy again.",
                    )
                app_healthy = True

        except Exception as exc:  # pragma: no cover - defensive
            logger.exception("Error in monitor loop: %s", exc)

        time.sleep(interval)


def main():
    validate_config_or_exit()

    notifier = SlackNotifier()
    client = JenkinsClient()
    checker = HealthChecker()

    # Fire a startup notification so operators know the monitor is live.
    notifier.send_success(
        title="Monitoring agent started",
        text=(
            f"Watching Jenkins {config.JENKINS_URL} (job *{config.JENKINS_JOB}*) "
            f"and app {config.APP_HEALTH_URL}."
        ),
    )

    try:
        monitor_loop(notifier, client, checker, config.POLL_INTERVAL)
    except KeyboardInterrupt:
        logger.info("Monitor stopped by user.")
        notifier.send_warning("Monitoring agent stopped",
                              "The CI/CD monitor was stopped by an operator.")
        sys.exit(0)


if __name__ == "__main__":
    main()
