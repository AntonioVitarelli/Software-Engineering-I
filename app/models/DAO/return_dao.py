import datetime

from sqlalchemy import Column, Integer, ForeignKey, String, Float, Enum, DateTime
from sqlalchemy.orm import relationship

from app.database.database import Base
from app.models.DAO.product_type_dao import ProductTypeDAO
from app.models.return_status import ReturnStatus


class ReturnLineDAO(Base):
    __tablename__ = "return_lines"

    id = Column(Integer, primary_key=True, autoincrement=True)
    return_id = Column(Integer, ForeignKey("returns.id"))
    product_barcode = Column(String, ForeignKey("products.barcode"))
    quantity = Column(Integer, nullable=False)
    price_per_unit = Column(Float, nullable=False)

class ReturnDAO(Base):
    __tablename__ = "returns"

    id = Column(Integer, primary_key=True, autoincrement=True)
    sale_id = Column(Integer, ForeignKey("sales.id"))
    status = Column(Enum(ReturnStatus), nullable=False, default=ReturnStatus.OPEN)
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.now)
    closed_at = Column(DateTime)
    lines = relationship("ReturnLineDAO", backref="return", cascade="all, delete-orphan")