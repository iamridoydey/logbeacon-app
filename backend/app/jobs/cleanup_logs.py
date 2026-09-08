from datetime import datetime, timedelta, timezone
from app import create_app
from app.config import Config
from app.repositories import log_repository
from app.queue import queue
from app.jobs.send_expiry_email import send_expiry_email


def run_cleanup():
    app = create_app()
    with app.app_context():
        cutoff = datetime.now(timezone.utc) - timedelta(days=Config.LOG_RETENTION_DAYS)
        expiring_logs = log_repository.find_logs_older_than(cutoff)

        for log in expiring_logs:
            queue.enqueue(send_expiry_email, log.id)

        print(f"Enqueued {len(expiring_logs)} log(s) nearing expiry")


if __name__ == "__main__":
    run_cleanup()