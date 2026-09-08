class AppError(Exception):
    """Base class for all custom application errors."""
    status_code = 500
    message = "An unexpected error occurred"

    def __init__(self, message=None, status_code=None):
        super().__init__(message or self.message)
        if message:
            self.message = message
        if status_code:
            self.status_code = status_code

    def to_dict(self):
        return {"error": self.message}


class ValidationError(AppError):
    status_code = 400
    message = "Invalid request data"


class AuthenticationError(AppError):
    status_code = 401
    message = "Authentication required"


class NotFoundError(AppError):
    status_code = 404
    message = "Resource not found"


class ConflictError(AppError):
    status_code = 409
    message = "Resource already exists"


class ExternalServiceError(AppError):
    status_code = 502
    message = "External service failed"