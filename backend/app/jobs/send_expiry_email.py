import smtplib
from email.mime.text import MIMEText
from app import create_app
from app.config import Config
from app.repositories import log_repository, user_repository


def _send_email(to_email, error_log, error_solution):
    body = (
        f"Your saved log is expiring soon. Here's a copy before it's removed:\n\n"
        f"Error:\n{error_log}\n\n"
        f"Solution:\n{error_solution}\n"
    )

    msg = MIMEText(body)
    msg['Subject'] = "LogBeacon — your saved log is expiring"
    msg['From'] = Config.FROM_EMAIL
    msg['To'] = to_email

    with smtplib.SMTP(Config.SMTP_HOST, Config.SMTP_PORT) as server:
        server.starttls()
        server.login(Config.SMTP_USER, Config.SMTP_PASSWORD)
        server.send_message(msg)


def send_expiry_email(log_id):
    app = create_app()
    with app.app_context():
        log = log_repository.find_by_id(log_id)

        if not log:
            return  # already deleted, or never existed — nothing to do

        user = user_repository.find_by_id(log.user_id)
        if not user:
            return

        _send_email(user.email, log.error_log, log.error_solution)

        # only reached if _send_email didn't raise — safe to delete now
        log_repository.delete(log)