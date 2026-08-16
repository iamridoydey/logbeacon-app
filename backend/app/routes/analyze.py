from flask import Blueprint, request, jsonify, g
from app.decorators import require_api_key
from app.services import analyze_service
from app.config import Config

bp = Blueprint('analyze', __name__, url_prefix='/analyze')


@bp.route('', methods=['POST'])
@require_api_key
def analyze():
    data = request.get_json()

    if not data:
        return jsonify({"error": "Missing or invalid JSON format"}), 400

    error_log = data.get('error_log')

    if not error_log:
        return jsonify({"error": "Missing error_log"}), 400

    if len(error_log) > Config.MAX_ERROR_LENGTH:
        return jsonify({"error": f"error_log exceeds {Config.MAX_ERROR_LENGTH} characters"}), 400

    return analyze_service.analyze_error(g.current_user.id, error_log)