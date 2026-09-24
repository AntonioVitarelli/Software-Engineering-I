from pydantic import BaseModel, Field
from typing import Optional
from app.models.DTO.loyalty_card_dto import LoyaltyCardDTO

class CustomerDTO(BaseModel):
    id: Optional[int] = None
    name: str
    card: Optional[LoyaltyCardDTO] = None
    