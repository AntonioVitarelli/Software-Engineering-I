from app.models.errors.app_error import AppError


class GeneralError(AppError):
    def __init__(self, message: str):
        super().__init__(
            message=message,
            status_code=500
        )
