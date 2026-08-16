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
    logs = log_repository.find_all_by_user(user_id)

    result = [
        {
            "id": log.id,
            "error_log": log.error_log,
            "error_solution": log.error_solution,
            "created_at": log.created_at
        }
        for log in logs
    ]

    return jsonify(result), 200