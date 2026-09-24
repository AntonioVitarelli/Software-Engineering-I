from fastapi import status
from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class ErrorDTO:
    code: int
    message: str
    name: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert ErrorDTO to dictionary for JSON serialization"""
        return {"code": self.code, "message": self.message, "name": self.name}


@dataclass
class UnauthenticadtedErrorDTO(ErrorDTO):
    @staticmethod
    def json_example() -> Dict[str, Any]:
        return UnauthorizedErrorDTO(
            code=status.HTTP_401_UNAUTHORIZED,
            message="Authorization header missing",
            name="UnauthorizedError",
        ).to_dict()


@dataclass
class UnauthorizedErrorDTO(ErrorDTO):
    @staticmethod
    def json_example() -> Dict[str, Any]:
        return UnauthorizedErrorDTO(
            code=status.HTTP_403_FORBIDDEN,
            message="Insufficient rights",
            name="ForbiddenError",
        ).to_dict()

