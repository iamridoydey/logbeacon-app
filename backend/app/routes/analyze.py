import logging

from flask import Blueprint, g, request

from app.config import Config
from app.decorators import require_login_or_api_key
from app.errors import ValidationError
from app.services import analyze_service

logger = logging.getLogger(__name__)

bp = Blueprint('analyze', __name__, url_prefix='/analyze')


@bp.route('', methods=['POST'])
@require_login_or_api_key
def analyze():
    data = request.get_json()

    if not data:
        logger.warning("analyze rejected: missing json")
        raise ValidationError("Missing or invalid JSON format")

    error_log = data.get('error_log')

    if not error_log:
        logger.warning("analyze rejected: missing error_log user_id=%s", g.current_user.id)
        raise ValidationError("Missing error_log")

    if len(error_log) > Config.MAX_ERROR_LENGTH:
        logger.warning(
            "analyze rejected: error_log too long user_id=%s length=%s",
            g.current_user.id,
            len(error_log),
        )
        raise ValidationError(f"error_log exceeds {Config.MAX_ERROR_LENGTH} characters")

    logger.info("analyze requested user_id=%s length=%s", g.current_user.id, len(error_log))
    return analyze_service.analyze_error(g.current_user.id, error_log)