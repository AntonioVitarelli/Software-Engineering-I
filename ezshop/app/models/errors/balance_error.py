from app.models.errors.app_error import AppError


class BalanceError(AppError):
    """Insufficient balance for the operation (421)"""

    def __init__(self, message: str = "Insufficient balance for the operation"):
        super().__init__(message, 421)
        self.name: str = "BalanceError"
