import pytest
from app.services import auth_service
from app.errors import AuthenticationError


def test_signin_user_wrong_password_raises_authentication_error(app, db):
    with app.app_context():
        auth_service.create_user("ridoy", "ridoy@email.com", "correctpass")

        with pytest.raises(AuthenticationError):
            auth_service.signin_user("ridoy", "wrongpass")


def test_signin_user_success(app, db):
    with app.test_request_context():
        auth_service.create_user("ridoy", "ridoy@email.com", "correctpass")
        response, status = auth_service.signin_user("ridoy", "correctpass")
        assert status == 200