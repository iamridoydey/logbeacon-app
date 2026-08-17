from flask import jsonify
from app.db import db
from app.repositories import log_repository
from app.models import Log


# Create log record in database
def create_log(user_id, error_log, error_solution):
    try:
        new_log = Log(
            user_id=user_id,
            error_log=error_log,
            error_solution=error_solution
        )
        
        log_repository.save(new_log)
        log_repository.commit()

        return jsonify({
            "id": new_log.id,
            "error_log": new_log.error_log,
            "error_solution": new_log.error_solution,
            "created_at": new_log.created_at
        }), 201

    except Exception as error:
        log_repository.rollback()
        return jsonify({"error": str(error)}), 500
    

# Get all logs from database
def get_user_logs(user_id):
    results = log_repository.find_all_by_user_with_analysis(user_id)

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

    return jsonify({
        "entries": entries,
        "summary": {
            "total_requests": len(entries),
            "total_cost": round(total_cost, 6),
            "total_input_tokens": total_input_tokens,
            "total_output_tokens": total_output_tokens,
        }
    }), 200