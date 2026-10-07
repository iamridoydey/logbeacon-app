import logging
import time

from flask import jsonify
from opentelemetry.trace import Status, StatusCode
from sqlalchemy.exc import SQLAlchemyError

from app.models import Log, Analysis
from app.observability import tracer, make_duration_histogram, execution_counter
from app.repositories import log_repository, analysis_repository

logger = logging.getLogger(__name__)

save_logs_duration = make_duration_histogram(
    "logbeacon.save.logs.duration",
    [0.1, 0.5, 1, 2, 5, 10, 30, 60],
    description="Time to commit a conversation; label outcome=success|failure",
)

fetching_logs_duration = make_duration_histogram(
    "logbeacon.fetching.logs.duration",
    [0.05, 0.1, 0.25, 0.5, 1, 2, 5, 10],
    description="Time to load history; label outcome=success|failure",
)

saving_logs_total = execution_counter(
    name="logbeacon.saving.logs",
    description="Saving logs total; label outcome=success|failure",
)

fetching_logs_total = execution_counter(
    name="logbeacon.fetching.logs",
    description="Fetching logs total; label outcome=success|failure",
)


def save_log_entry(user_id, error_log, error_solution, analysis_fields=None):
    """Single persist path. POST /log and analyze both call this."""
    start = time.perf_counter()
    outcome = "failure"

    with tracer.start_as_current_span("save_log") as span:
        span.set_attribute("logbeacon.flow", "save_log")
        span.set_attribute("enduser.id", str(user_id))
        span.set_attribute("log.length", len(error_log))
        span.set_attribute("save_log.has_analysis", analysis_fields is not None)

        try:
            new_log = Log(
                user_id=user_id,
                error_log=error_log,
                error_solution=error_solution,
            )
            log_repository.save(new_log)
            log_id = new_log.id

            new_analysis = None
            if analysis_fields is not None:
                new_analysis = Analysis(
                    log_id=log_id,
                    input_tokens=analysis_fields["input_tokens"],
                    output_tokens=analysis_fields["output_tokens"],
                    latency=analysis_fields["latency"],
                    cost=analysis_fields["cost"],
                    status=True,
                )
                analysis_repository.save(new_analysis)

            log_repository.commit()
            outcome = "success"

            span.set_attribute("log.id", log_id)
            logger.info(
                "flow=save_log persisted user_id=%s log_id=%s has_analysis=%s",
                user_id, log_id, new_analysis is not None,
            )
            return new_log, new_analysis

        except SQLAlchemyError as error:
            log_repository.rollback()
            span.record_exception(error)
            span.set_status(Status(StatusCode.ERROR))
            logger.exception("flow=save_log failed user_id=%s", user_id)
            raise

        finally:
            save_logs_duration.record(time.perf_counter() - start, {"outcome": outcome})
            saving_logs_total.add(1, {"outcome": outcome})


def get_user_logs(user_id):
    start = time.perf_counter()
    outcome = "failure"

    with tracer.start_as_current_span("fetching_logs") as span:
        span.set_attribute("logbeacon.flow", "history")
        span.set_attribute("enduser.id", str(user_id))

        try:
            with tracer.start_as_current_span("history.query"):
                results = log_repository.find_all_by_user_with_analysis(user_id)

            span.set_attribute("history.rows", len(results))
            logger.info("flow=history retrieved user_id=%s rows=%s", user_id, len(results))

            entries = []
            total_cost = 0.0
            total_input_tokens = 0
            total_output_tokens = 0

            for log, analysis in results:
                entries.append({
                    "id": log.id,
                    "created_at": log.created_at,
                    "error_log": log.error_log,
                    "error_solution": log.error_solution,
                    "input_tokens": analysis.input_tokens,
                    "output_tokens": analysis.output_tokens,
                    "latency_ms": analysis.latency,
                    "cost": str(analysis.cost),
                })
                total_cost += float(analysis.cost)
                total_input_tokens += analysis.input_tokens
                total_output_tokens += analysis.output_tokens

            outcome = "success"
            return jsonify({
                "entries": entries,
                "summary": {
                    "total_requests": len(entries),
                    "total_cost": round(total_cost, 6),
                    "total_input_tokens": total_input_tokens,
                    "total_output_tokens": total_output_tokens,
                },
            }), 200

        except Exception:
            logger.exception("flow=history failed user_id=%s", user_id)
            raise

        finally:
            fetching_logs_duration.record(time.perf_counter() - start, {"outcome": outcome})
            fetching_logs_total.add(1, {"outcome": outcome})