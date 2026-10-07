"""
Shared telemetry helpers. Only the OpenTelemetry API is used here; the SDK
(exporters, sampling) is started by auto-instrumentation in gunicorn.conf.py.
If the SDK is not running (tests, `flask run`), everything here does nothing.
"""
from opentelemetry import metrics, trace

tracer = trace.get_tracer("logbeacon.backend")
meter = metrics.get_meter("logbeacon.backend")

# print("METER PROVIDER:", type(metrics.get_meter_provider()))


def make_duration_histogram(name, boundaries, description=""):
    """Create a seconds histogram. Call it ONCE per metric, at the top of a
    file (global scope), never inside a function that runs per request."""
    return meter.create_histogram(
        name,
        unit="s",
        description=description,
        explicit_bucket_boundaries_advisory=boundaries,
    )


def execution_counter(name, description=""):
    """Create a counter that only goes up (e.g. job runs). Same rule:
    call it ONCE per metric, at the top of a file."""
    return meter.create_counter(name, unit="1", description=description)