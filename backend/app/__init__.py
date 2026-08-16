from flask import Flask

from app.config import Config
from app.db import db
from app.routes import register_routes
from app.errors import register_error_handlers


def create_app(test_config=None):
    """
    Flask application factory.

    Creates and configures a new Flask application instance.
    """

    app = Flask(__name__)

    # Load the default application configuration.
    app.config.from_object(Config)

    # Allow tests to override normal configuration.
    if test_config:
        app.config.update(test_config)

    # Register error handlers
    register_error_handlers(app)

    # Connect Flask-SQLAlchemy to this Flask application.
    db.init_app(app)

    # Registration of the models
    with app.app_context():
        from app import models 

    """
    Provide the app to register the blueprint
    to the app
    """
    register_routes(app)

    return app