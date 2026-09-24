from sqlalchemy import Column, Integer, String, Float, DateTime, Enum
from sqlalchemy.sql import func
from app.database.database import Base
from enum import Enum as PyEnum

class OrderStatus(PyEnum):
    ISSUED = "ISSUED"
    PAID = "PAID"
    COMPLETED = "COMPLETED"

class OrderDAO(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, autoincrement=True)
    product_barcode = Column(String(14), nullable=False)
    quantity = Column(Integer, nullable=False)
    price_per_unit = Column(Float, nullable=False)
    status = Column(Enum(OrderStatus), nullable=False, default=OrderStatus.ISSUED)
    issue_date = Column(DateTime(timezone=True), nullable=False)
