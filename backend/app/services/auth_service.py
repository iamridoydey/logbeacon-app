from flask import jsonify, session
from werkzeug.security import generate_password_hash, check_password_hash
import secrets
import hashlib
from app.db import db
from app.models import User


# Create user account
def create_user(username, email, password):
    api_key = secrets.token_urlsafe(32)
    api_key_hash = hashlib.sha256(api_key.encode()).hexdigest()

    try:
        new_user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password),
            api_key_hash=api_key_hash
        )

        db.session.add(new_user)
        db.session.commit()


        return jsonify({
            "message": f"User {username} created",
            "api_key": api_key
        }), 201

    except Exception as error:
        db.session.rollback()
        return jsonify({"error": str(error)}), 500



# Signin user
def signin_user(username, password):
    user = User.query.filter_by(username=username).first()

    if not user or not check_password_hash(user.password_hash, password):
        return jsonify({"error": "Invalid username or password"}), 401

    if not user.is_active:
        return jsonify({"error": "Account is disabled"}), 403

    session['user_id'] = user.id

    return jsonify({"message": f"Welcome back, {user.username}"}), 200



# Signout user
def signout_user():
    session.pop('user_id', None)
    return jsonify({"message": "Signed out successfully"}), 200