import logging

from flask import Blueprint, request

from app.errors import ValidationError
from app.services import auth_service

logger = logging.getLogger(__name__)

bp = Blueprint('auth', __name__, url_prefix='/auth')


# Register new account route
@bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    if not data:
        logger.warning("register rejected: missing json")
        raise ValidationError("Missing or invalid JSON format")
    
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')

    if not username or not email or not password:
        logger.warning("register rejected: missing fields")
        raise ValidationError("Missing one of username/email/password")

    logger.info("register requested username=%s", username)
    return auth_service.create_user(username, email, password)


# Singin route
@bp.route('/signin', methods=['POST'])
def signin():
    data = request.get_json()

    if not data:
        logger.warning("signin rejected: missing json")
        raise ValidationError("Missing or invalid JSON format")

    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        logger.warning("signin rejected: missing fields")
        raise ValidationError("Missing username or password")

    logger.info("signin requested username=%s", username)
    return auth_service.signin_user(username, password)


# Signout route
@bp.route('/signout', methods=['POST'])
def signout():
    logger.info("signout requested")
    return auth_service.signout_user()