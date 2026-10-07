import logging
import smtplib
from datetime import datetime, timedelta, timezone
from email.mime.text import MIMEText

from app.config import Config
from app.repositories import log_repository, user_repository
from app.observability import tracer, execution_counter

logger = logging.getLogger(__name__)

# Created once, when this file is first imported.
# One counter for every outcome, split by labels. The "job" label lets a future
# job reuse the same metric. Prometheus name: logbeacon_job_executions_total
job_executions = execution_counter(
    name="logbeacon.job.executions",
    description="RQ job runs; labels job=<name>, outcome=success|skipped|failure",
)


def _send_email(to_email, error_log, error_solution):
    body = (
        f"Your saved log is expiring soon. Here's a copy before it's removed:\n\n"
        f"Error:\n{error_log}\n\n"
        f"Solution:\n{error_solution}\n"
    )

    msg = MIMEText(body)
    msg["Subject"] = "LogBeacon — your saved log is expiring"
    msg["From"] = Config.FROM_EMAIL
    msg["To"] = to_email

    # timeout: without it a hung mail server would block the worker forever
    with smtplib.SMTP(Config.SMTP_HOST, Config.SMTP_PORT, timeout=15) as server:
        server.starttls()
        server.login(Config.SMTP_USER, Config.SMTP_PASSWORD)
        server.send_message(msg)


def cleanup_logs(log_id):
    from app import create_app

    outcome = "failure"   # becomes "skipped" or "success" on the paths below

    try:
        app = create_app()

        with app.app_context():
            with tracer.start_as_current_span("cleanup_logs") as span:
                span.set_attribute("logbeacon.flow", "cleanup_logs")
                span.set_attribute("log.id", log_id)

                log = log_repository.find_by_id(log_id)

                if not log:
                    outcome = "skipped"
                    logger.info("flow=cleanup_logs skipped missing log_id=%s", log_id)
                    return

                user = user_repository.find_by_id(log.user_id)

                if not user:
                    outcome = "skipped"
                    logger.warning(
                        "flow=cleanup_logs skipped missing user log_id=%s user_id=%s",
                        log_id,
                        log.user_id,
                    )
                    return

                # Safety check: never delete a log younger than the retention period,
                # even if this job runs early (manual run, bug, config change).
                # Log.created_at is a plain TIMESTAMP with no timezone, so compare
                # against a naive UTC time (this assumes the database clock is UTC).
                cutoff = (
                    datetime.now(timezone.utc) - timedelta(days=Config.LOG_RETENTION_DAYS)
                ).replace(tzinfo=None)

                if log.created_at > cutoff:
                    outcome = "skipped"
                    logger.warning(
                        "flow=cleanup_logs skipped, log not old enough "
                        "log_id=%s created_at=%s",
                        log_id,
                        log.created_at,
                    )
                    return

                span.set_attribute("enduser.id", str(user.id))

                logger.info(
                    "flow=cleanup_logs processing log_id=%s user_id=%s",
                    log_id,
                    user.id,
                )

                with tracer.start_as_current_span("send_expiry_email"):
                    _send_email(user.email, log.error_log, log.error_solution)

                with tracer.start_as_current_span("delete_log"):
                    log_repository.delete(log)
                    log_repository.commit()

                outcome = "success"
                logger.info(
                    "flow=cleanup_logs expiry email sent and log deleted log_id=%s",
                    log_id,
                )

    except Exception:
        logger.exception("flow=cleanup_logs failed log_id=%s", log_id)
        raise   # re-raise so RQ marks the job as failed

    finally:
        # Runs for success, skipped, and failure: exactly one count per run.
        job_executions.add(1, {"job": "cleanup_logs", "outcome": outcome})