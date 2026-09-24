from typing import Optional, List

from pydantic import BaseModel

from app.models.sale_status import SaleStatus

class SaleLineDTO(BaseModel):
    id: Optional[int] = None
    sale_id: Optional[int] = None
    product_barcode: Optional[str] = None
    quantity: Optional[int] = None
    price_per_unit: Optional[float] = None
    discount_rate: Optional[float] = None

class SaleDTO(BaseModel):
    id: Optional[int] = None
    status: Optional[SaleStatus] = None
    discount_rate: Optional[float] = None
    created_at: Optional[str] = None
    closed_at: Optional[str] = None
    lines: Optional[List[SaleLineDTO]] = None