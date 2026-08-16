import time
from flask import jsonify
from app.models import Log, Analysis
from app.repositories import log_repository, analysis_repository
from app.errors import ValidationError, ExternalServiceError
from app.services.groq_service import ask_groq
from app.services.pricing_service import calculate_cost


def analyze_error(user_id, error_log):
    if not user_id or not error_log:
        raise ValidationError("Missing one of user_id/error_log")

    start_time = time.perf_counter()

    try:
        solution = ask_groq(error_log)
    except Exception as error:
        raise ExternalServiceError(f"LLM call failed: {str(error)}")

    latency_ms = int((time.perf_counter() - start_time) * 1000)

    input_tokens = solution["input_tokens"]
    output_tokens = solution["output_tokens"]
    error_solution = solution["log_solution"]
    cost = calculate_cost(input_tokens=input_tokens, output_tokens=output_tokens)

    try:
        new_log = Log(
            user_id=user_id,
            error_log=error_log,
            error_solution=error_solution
        )
        log_repository.save(new_log)  # add + flush — new_log.id now assigned

        new_analysis = Analysis(
            log_id=new_log.id,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            latency=latency_ms,
            cost=cost,
            status=True
        )
        analysis_repository.save(new_analysis)
        log_repository.commit()  # commits both new_log and new_analysis together

        return jsonify({
            "message": "Successfully completed the analysis",
            "id": new_log.id,
            "error_solution": error_solution,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "latency_ms": latency_ms,
            "cost": str(cost)
        }), 201

    except Exception as error:
        log_repository.rollback()
        raise