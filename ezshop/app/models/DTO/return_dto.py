from typing import Optional, List

from pydantic import BaseModel

from app.models.return_status import ReturnStatus


class ReturnLineDTO(BaseModel):
    id: Optional[int] = None
    return_id: Optional[int] = None
    product_barcode: Optional[str] = None
    quantity: Optional[int] = None
    price_per_unit: Optional[float] = None

class ReturnDTO(BaseModel):
    id: Optional[int] = None
    sale_id: Optional[int] = None
    status: Optional[ReturnStatus] = None
    created_at: Optional[str] = None
    closed_at: Optional[str] = None
    lines: Optional[List[ReturnLineDTO]] = None