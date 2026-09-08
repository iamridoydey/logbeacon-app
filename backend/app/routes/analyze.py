from flask import Blueprint, request, jsonify, g
from app.decorators import require_login_or_api_key
from app.services import analyze_service
from app.errors import ValidationError
from app.config import Config

bp = Blueprint('analyze', __name__, url_prefix='/analyze')


@bp.route('', methods=['POST'])
@require_login_or_api_key
def analyze():
    data = request.get_json()

    if not data:
        raise ValidationError("Missing or invalid JSON format")

    error_log = data.get('error_log')

    if not error_log:
        raise ValidationError("Missing error_log")

    if len(error_log) > Config.MAX_ERROR_LENGTH:
        raise ValidationError(f"error_log exceeds {Config.MAX_ERROR_LENGTH} characters")

    return analyze_service.analyze_error(g.current_user.id, error_log)