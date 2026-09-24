import datetime

from sqlalchemy import Column, Integer, String, Enum, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from app.database.database import Base
from app.models.DAO.product_type_dao import ProductTypeDAO
from app.models.sale_status import SaleStatus


class SaleLineDAO(Base):
    __tablename__ = "sale_lines"

    id = Column(Integer, primary_key=True, autoincrement=True)
    sale_id = Column(Integer, ForeignKey("sales.id"))
    product_barcode = Column(String, ForeignKey("products.barcode"))
    quantity = Column(Integer, nullable=False)
    price_per_unit = Column(Float, nullable=False)
    discount_rate = Column(Float, nullable=False)

class SaleDAO(Base):
    __tablename__ = "sales"

    id = Column(Integer, primary_key=True, autoincrement=True)
    status = Column(Enum(SaleStatus), nullable=False, default=SaleStatus.OPEN)
    discount_rate = Column(Float, nullable=False, default=0.0)
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.now)
    closed_at = Column(DateTime)
    lines = relationship("SaleLineDAO", backref="sale", cascade="all, delete-orphan")




