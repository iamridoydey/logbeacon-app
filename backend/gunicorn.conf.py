import os
from uuid import uuid4

bind = "0.0.0.0:5000"
workers = int(os.getenv("WEB_CONCURRENCY", "2"))
worker_class = "gthread"
threads = int(os.getenv("GUNICORN_THREADS", "4"))

timeout = 90
graceful_timeout = 30

# The app must load AFTER post_fork.
def post_fork(server, worker):
    # Give this worker its own service.instance.id, otherwise two workers
    # export the same metric series and overwrite each other.
    existing = os.environ.get("OTEL_RESOURCE_ATTRIBUTES", "")
    extra = f"service.instance.id={uuid4()}"
    os.environ["OTEL_RESOURCE_ATTRIBUTES"] = f"{existing},{extra}" if existing else extra

    # This is the same function `opentelemetry-instrument` runs on startup.
    # We call it here, inside the worker, so the exporter threads are created
    # after the fork instead of before it.
    from opentelemetry.instrumentation.auto_instrumentation import initialize
    # from opentelemetry import metrics, trace

    initialize()
    server.log.info("OpenTelemetry auto-instrumentation started in worker %s", worker.pid)

    # server.log.info(
    # "TracerProvider=%s MeterProvider=%s",
    # type(trace.get_tracer_provider()).__name__,
    # type(metrics.get_meter_provider()).__name__,
    # )
    
    # server.log.info(
    # "OpenTelemetry auto-instrumentation started in worker %s",
    # worker.pid,
    # )