import logging
from datetime import datetime, timedelta, timezone

from app import create_app
from app.config import Config
from app.jobs.send_expiry_email import send_expiry_email
from app.queue import queue
from app.repositories import log_repository

logger = logging.getLogger(__name__)


def run_cleanup():
    app = create_app()
    with app.app_context():
        cutoff = datetime.now(timezone.utc) - timedelta(days=Config.LOG_RETENTION_DAYS)
        expiring_logs = log_repository.find_logs_older_than(cutoff)

        for log in expiring_logs:
            queue.enqueue(send_expiry_email, log.id)
            logger.info("redis queue enqueued send_expiry_email log_id=%s", log.id)

        logger.info("cleanup enqueued jobs count=%s", len(expiring_logs))


if __name__ == "__main__":
    run_cleanup()