from app.routes.auth import bp as auth_bp

def register_routes(app):
    """
    Register all the route blueprint to the application to provide all route in flask application.
    """
    app.register_blueprint(auth_bp)