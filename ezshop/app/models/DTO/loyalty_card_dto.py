from typing import Optional

from pydantic import BaseModel
from typing import Optional
class LoyaltyCardDTO(BaseModel):
    card_id: Optional[str] = None
    points: Optional[int] = None
    
    