import logging
import os
import sys


def configure_logging(app=None):
    """JSON-friendly text logs on stdout so OTel logging instrumentation can export them."""
    level_name = os.environ.get("LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)

    root = logging.getLogger()
    if not root.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(
            logging.Formatter(
                "%(asctime)s %(levelname)s [%(name)s] %(message)s"
            )
        )
        root.addHandler(handler)
    root.setLevel(level)

    logging.getLogger("werkzeug").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

    if app is not None:
        app.logger.setLevel(level)
        app.logger.info("logging configured", extra={"log_level": level_name})