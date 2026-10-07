import logging
import time
from datetime import timedelta

from flask import jsonify

from app.config import Config
from app.errors import ExternalServiceError, ValidationError
from app.observability import tracer, make_duration_histogram, execution_counter
from app.queue import queue
from app.services import log_service
from app.services.groq_service import ask_groq
from app.services.pricing_service import calculate_cost

logger = logging.getLogger(__name__)

analyze_duration = make_duration_histogram(
    "logbeacon.analyze.duration",
    [1, 2, 5, 10, 20, 30, 60, 120],
    description="End-to-end analyze time; label outcome=success|failure",
)

analyze_total = execution_counter(
    name="logbeacon.analyze.requests",
    description="Valid analyze requests; label outcome=success|failure",
)


def analyze_error(user_id, error_log):
    if not user_id or not error_log:
        raise ValidationError("Missing one of user_id/error_log")

    flow_start = time.perf_counter()
    outcome = "failure"

    with tracer.start_as_current_span("analyze") as span:
        span.set_attribute("logbeacon.flow", "analyze")
        span.set_attribute("enduser.id", str(user_id))
        span.set_attribute("log.length", len(error_log))

        try:
            groq_start = time.perf_counter()

            try:
                with tracer.start_as_current_span("analyze.groq"):
                    solution = ask_groq(error_log)
            except Exception as e:
                logger.exception("flow=analyze step=groq failed user_id=%s", user_id)
                raise ExternalServiceError(
                    f"Failed to get analyze from Groq: {e}"
                ) from e

            latency_ms = int((time.perf_counter() - groq_start) * 1000)

            input_tokens = solution["input_tokens"]
            output_tokens = solution["output_tokens"]
            error_solution = solution["log_solution"]
            cost = calculate_cost(
                input_tokens=input_tokens,
                output_tokens=output_tokens,
            )

            try:
                new_log, _ = log_service.save_log_entry(
                    user_id,
                    error_log,
                    error_solution,
                    analysis_fields={
                        "input_tokens": input_tokens,
                        "output_tokens": output_tokens,
                        "latency": latency_ms,
                        "cost": cost,
                    },
                )
                log_id = new_log.id
            except Exception:
                logger.exception("flow=analyze step=persist failed user_id=%s", user_id)
                raise

            try:
                with tracer.start_as_current_span("analyze.schedule_cleanup"):
                    queue.enqueue_in(
                        timedelta(days=Config.LOG_RETENTION_DAYS),
                        "app.jobs.cleanup_logs.cleanup_logs",
                        log_id,
                    )
            except Exception:
                logger.exception(
                    "flow=analyze step=schedule_cleanup failed user_id=%s log_id=%s",
                    user_id,
                    log_id,
                )

            has_explanation = bool(error_solution and str(error_solution).strip())
            if not has_explanation:
                logger.warning(
                    "flow=analyze empty explanation user_id=%s log_id=%s",
                    user_id,
                    log_id,
                )

            span.set_attribute("log.id", log_id)
            span.set_attribute("llm.input_tokens", input_tokens)
            span.set_attribute("llm.output_tokens", output_tokens)
            span.set_attribute("analyze.latency_ms", latency_ms)

            logger.info(
                "flow=analyze succeeded user_id=%s log_id=%s latency_ms=%s "
                "input_tokens=%s output_tokens=%s cost=%s",
                user_id,
                log_id,
                latency_ms,
                input_tokens,
                output_tokens,
                cost,
            )

            outcome = "success" if has_explanation else "failure"

            return jsonify(
                {
                    "message": "Successfully completed the analyze",
                    "id": log_id,
                    "error_solution": error_solution,
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "latency_ms": latency_ms,
                    "cost": str(cost),
                }
            ), 201

        finally:
            elapsed = time.perf_counter() - flow_start
            analyze_duration.record(elapsed, {"outcome": outcome})
            analyze_total.add(1, {"outcome": outcome})