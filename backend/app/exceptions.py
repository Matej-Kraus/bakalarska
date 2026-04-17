"""Domain and HTTP exception helpers for consistent API error responses."""


class AppError(Exception):
    """Base for domain/application errors that map to HTTP responses."""

    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class NotFoundError(AppError):
    def __init__(self, message: str = "Resource not found"):
        super().__init__(message, status_code=404)


class ForbiddenError(AppError):
    def __init__(self, message: str = "Forbidden"):
        super().__init__(message, status_code=403)


class BadRequestError(AppError):
    def __init__(self, message: str):
        super().__init__(message, status_code=400)
