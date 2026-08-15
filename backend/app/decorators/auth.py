# decorators/auth.py
import hashlib
from functools import wraps
from flask import g, session, request, jsonify
from app.models import User


def require_login(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        user_id = session.get('user_id')

        if not user_id:
            return jsonify({"error": "Authentication required"}), 401

        user = User.query.get(user_id)
        if not user or not user.is_active:
            return jsonify({"error": "Invalid or inactive user"}), 401

        g.current_user = user
        return f(*args, **kwargs)

    return decorated


def require_api_key(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization', '')

        if not auth_header.startswith('Bearer '):
            return jsonify({"error": "Missing or invalid Authorization header"}), 401

        api_key = auth_header.removeprefix('Bearer ').strip()
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()

        user = User.query.filter_by(api_key_hash=key_hash).first()
        if not user or not user.is_active:
            return jsonify({"error": "Invalid API key"}), 401

        g.current_user = user
        return f(*args, **kwargs)

    return decorated