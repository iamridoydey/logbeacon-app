import pytest
from app import create_app
from app.db import db as _db

# Setting up the environment for testing
@pytest.fixture(scope="function")
def app():
    test_config = {
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "postgresql://logbeacon:logbeacon@localhost/logbeacon_dev_test",
        "SECRET_KEY": "test-secret-key",
    }
    
    flask_app = create_app(test_config)

    with flask_app.app_context():
        _db.create_all()
        yield flask_app

        # Cleanup after testing
        _db.session.remove()
        _db.drop_all()


@pytest.fixture(scope="function")
def client(app):
    return app.test_client()


@pytest.fixture(scope="function")
def db(app):
    return _db