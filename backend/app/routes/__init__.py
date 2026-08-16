from app.routes.auth import bp as auth_bp
from app.routes.analyze import bp as analyze_bp

def register_routes(app):
    """
    Register all the route blueprint to the application to provide all route in flask application.
    """
    app.register_blueprint(auth_bp)
    app.register_blueprint(analyze_bp)