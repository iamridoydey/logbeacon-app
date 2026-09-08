from flask import Blueprint, request, jsonify
from app.errors import ValidationError
from app.services import auth_service

bp = Blueprint('auth', __name__, url_prefix='/auth')


# Register new account route
@bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    print(data)
    if not data:
        raise ValidationError("Missing or invalid JSON format")
    
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')

    if not username or not email or not password:
        raise ValidationError("Missing one of username/email/password")

    return auth_service.create_user(username, email, password)


# Singin route
@bp.route('/signin', methods=['POST'])
def signin():
    data = request.get_json()

    if not data:
        raise ValidationError("Missing or invalid JSON format")

    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        raise ValidationError("Missing username or password")

    return auth_service.signin_user(username, password)


# Signout route
@bp.route('/signout', methods=['POST'])
def signout():
    return auth_service.signout_user()