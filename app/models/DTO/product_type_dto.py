from pydantic import BaseModel, Field
from typing import Optional

class ProductTypeDTO(BaseModel):
    id: Optional[int] = None
    description: str #= Field(min_length=1)
    barcode: str #= Field(min_length=12, max_length=14)
    price_per_unit: float #= Field(gt=0)
    note: Optional[str] = None #= Field(min_length=1)
    quantity: Optional[int] = None
    position: Optional[str] = None

class ProductTypeUpdateDTO(BaseModel):
    description: Optional[str] = None
    barcode: Optional[str] = None
    price_per_unit: Optional[float] = None
    note: Optional[str] = None
    quantity: Optional[int] = None
    position: Optional[str] = None