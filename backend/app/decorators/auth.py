from functools import wraps
from flask import request, session, g, jsonify
from app.db import db
from app.models import User
from app.repositories import user_repository
import hashlib


def require_login(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({"error": "Authentication required"}), 401

        user = db.session.get(User, user_id)
        if not user:
            return jsonify({"error": "Authentication required"}), 401

        g.current_user = user
        return f(*args, **kwargs)
    return decorated


def require_api_key(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization', '')

        if not auth_header.startswith('Bearer '):
            return jsonify({"error": "Missing or invalid API key"}), 401

        api_key = auth_header.removeprefix('Bearer ').strip()
        api_key_hash = hashlib.sha256(api_key.encode()).hexdigest()

        user = user_repository.find_by_api_key_hash(api_key_hash)
        if not user:
            return jsonify({"error": "Invalid API key"}), 401

        g.current_user = user
        return f(*args, **kwargs)
    return decorated


def require_login_or_api_key(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if session.get('user_id'):
            return require_login(f)(*args, **kwargs)
        return require_api_key(f)(*args, **kwargs)
    return decorated