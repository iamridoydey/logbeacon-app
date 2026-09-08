from flask import jsonify, Blueprint
from sqlalchemy import text
from app.db import db

bp = Blueprint('health', __name__, url_prefix='/health')


@bp.route('', methods=['GET'])
def health():
    try:
        db.session.execute(text('SELECT 1'))
        return jsonify({"status": "ok", "database": "connected"}), 200
    except Exception as error:
        return jsonify({"status": "error", "database": "unreachable", "detail": str(error)}), 503