from sqlalchemy import Boolean, Column, Float, Integer, String
from app.database.database import Base

class ProductTypeDAO(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, autoincrement=True)
    description = Column(String, nullable=False)
    barcode = Column(String, nullable=False, unique=True)
    price_per_unit = Column(Float, nullable=False)
    note = Column(String, nullable=True)
    quantity = Column(Integer, nullable=True)
    position = Column(String, nullable=True)
    usage_count = Column(Integer, nullable=False, default=0)


    def get_description(self) -> str:
        return self.description
    
    def get_usage_count(self) -> int:
        return self.usage_count or 0
    
    def is_in_use(self) -> bool:
        return (self.usage_count or 0) > 0
    
    def increment_usage_count(self) -> None:
        self.usage_count = (self.usage_count or 0) + 1
    
    def decrement_usage_count(self) -> None:
        if (self.usage_count or 0) > 0:
            self.usage_count -= 1
    
