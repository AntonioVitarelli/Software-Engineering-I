from app.models.errors.app_error import AppError

class InsufficientPointsError(AppError):
    """
    Raised when trying to subtract more points than available on a loyalty card.
    Mapped to HTTP 500 per Swagger spec.
    """
    def __init__(self, message: str = "Insufficient points on the card"):
        super().__init__(message, 500)
        self.name = "CustomerCardError"