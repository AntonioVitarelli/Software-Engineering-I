from enum import Enum
from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional


class OrderStatusDTO(str, Enum):
    ISSUED = "ISSUED"
    PAID = "PAID"
    COMPLETED = "COMPLETED"


class OrderDTO(BaseModel):
    id: int
    product_barcode: str
    quantity: int
    price_per_unit: float
    status: OrderStatusDTO
    issue_date: Optional[datetime] = None
    
class OrderCreateDTO(BaseModel):
    product_barcode: str
    quantity: int
    price_per_unit: float

    class ConfigDict:
        extra = "ignore"
