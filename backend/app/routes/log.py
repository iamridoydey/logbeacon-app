import logging

from flask import Blueprint, g, jsonify, request

from app.config import Config
from app.decorators import require_login
from app.services import log_service

logger = logging.getLogger(__name__)

bp = Blueprint('log', __name__, url_prefix='/log')


@bp.route('', methods=['POST'])
@require_login
def create_log():
    data = request.get_json()

    if not data:
        logger.warning("create_log rejected: missing json")
        return jsonify({"error": "Missing or invalid JSON format"}), 400

    error_log = data.get('error_log')
    error_solution = data.get('error_solution')

    if not error_log or not error_solution:
        logger.warning("create_log rejected: missing fields user_id=%s", g.current_user.id)
        return jsonify({"error": "Missing error_log or error_solution"}), 400

    if len(error_log) > Config.MAX_ERROR_LENGTH:
        logger.warning(
            "create_log rejected: error_log too long user_id=%s length=%s",
            g.current_user.id,
            len(error_log),
        )
        return jsonify({"error": f"error_log exceeds {Config.MAX_ERROR_LENGTH} characters"}), 400

    logger.info("create_log requested user_id=%s", g.current_user.id)
    return log_service.create_log(g.current_user.id, error_log, error_solution)



@bp.route('', methods=['GET'])
@require_login
def get_logs():
    logger.info("history retrieval requested user_id=%s", g.current_user.id)
    return log_service.get_user_logs(g.current_user.id)