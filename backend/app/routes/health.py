from flask import Blueprint, jsonify
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.db import db

bp = Blueprint('health', __name__, url_prefix='/health')


@bp.route('', methods=['GET'])
def health():
    try:
        db.session.execute(text('SELECT 1'))
        return jsonify({"status": "ok", "database": "connected"}), 200
    except SQLAlchemyError as error:
        return jsonify({"status": "error", "database": "unreachable", "detail": str(error)}), 503