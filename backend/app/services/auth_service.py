import hashlib
import logging
import secrets

from flask import jsonify, session
from werkzeug.security import check_password_hash, generate_password_hash

from app.errors import AppError, AuthenticationError, ConflictError
from app.models import User
from app.repositories import user_repository

logger = logging.getLogger(__name__)


# Create user account
def create_user(username, email, password):
    api_key = secrets.token_urlsafe(32)
    api_key_hash = hashlib.sha256(api_key.encode()).hexdigest()

    try:
        # Check whether the user already exist or not
        registered = user_repository.find_by_username(username)

        if registered:
            logger.warning("registration failed: username already exists username=%s", username)
            raise ConflictError("User already exist")

        new_user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password),
            api_key_hash=api_key_hash
        )

        user_repository.save(new_user)
        logger.info("registration succeeded username=%s user_id=%s", username, new_user.id)

        return jsonify({
            "message": f"User {username} created",
            "api_key": api_key
        }), 201

    except AppError:
        user_repository.rollback()
        raise
    except Exception as error:
        user_repository.rollback()
        logger.exception("registration failed username=%s error=%s", username, error)
        raise



# Signin user
def signin_user(username, password):
    user = user_repository.find_by_username(username)

    if not user or not check_password_hash(user.password_hash, password):
        logger.warning("signin failed username=%s", username)
        raise AuthenticationError("Invalid username or password")

    if not user.is_active:
        logger.warning("signin blocked disabled account username=%s user_id=%s", username, user.id)
        raise AppError("Account is disabled", 403)

    session['user_id'] = user.id
    logger.info("signin succeeded username=%s user_id=%s", user.username, user.id)

    return jsonify({"message": f"Welcome back, {user.username}"}), 200



# Signout user
def signout_user():
    user_id = session.pop('user_id', None)
    logger.info("signout succeeded user_id=%s", user_id)
    return jsonify({"message": "Signed out successfully"}), 200