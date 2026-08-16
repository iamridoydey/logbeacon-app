from flask import jsonify, session
from werkzeug.security import generate_password_hash, check_password_hash
import secrets
import hashlib
from app.db import db
from app.repositories import user_repository
from app.models import User


# Create user account
def create_user(username, email, password):
    api_key = secrets.token_urlsafe(32)
    api_key_hash = hashlib.sha256(api_key.encode()).hexdigest()

    try:
        # Check whether the user already exist or not
        registered = user_repository.find_by_username(username)

        if registered:
            return jsonify({"error": "User already exist"}), 409

        new_user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password),
            api_key_hash=api_key_hash
        )

        user_repository.save(new_user)


        return jsonify({
            "message": f"User {username} created",
            "api_key": api_key
        }), 201

    except Exception as error:
        user_repository.rollback()
        print(error)
        return jsonify({"error": str(error)}), 500



# Signin user
def signin_user(username, password):
    user = user_repository.find_by_username(username)

    print(user)

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