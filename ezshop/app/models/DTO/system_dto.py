from pydantic import BaseModel


class SystemDTO(BaseModel):
    id: int | None = None
    balance: float


class SystemReponseDTO(BaseModel):
    balance: float
