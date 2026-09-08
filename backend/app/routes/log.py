from flask import Blueprint, request, jsonify, g
from app.decorators import require_login
from app.services import log_service
from app.config import Config


bp = Blueprint('log', __name__, url_prefix='/log')


@bp.route('', methods=['POST'])
@require_login
def create_log():
    data = request.get_json()

    if not data:
        return jsonify({"error": "Missing or invalid JSON format"}), 400

    error_log = data.get('error_log')
    error_solution = data.get('error_solution')

    if not error_log or not error_solution:
        return jsonify({"error": "Missing error_log or error_solution"}), 400

    if len(error_log) > Config.MAX_ERROR_LENGTH:
        return jsonify({"error": f"error_log exceeds {Config.MAX_ERROR_LENGTH} characters"}), 400

    return log_service.create_log(g.current_user.id, error_log, error_solution)



@bp.route('', methods=['GET'])
@require_login
def get_logs():
    return log_service.get_user_logs(g.current_user.id)