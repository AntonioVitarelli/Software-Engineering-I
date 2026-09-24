from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from app.database.database import Base


class LoyaltyCardDAO(Base):
    __tablename__ = "loyalty_cards"

    id = Column(String(10), primary_key=True)
    points = Column(Integer, nullable=False, default=0)

    customer = relationship("CustomerDAO", back_populates="loyalty_card", uselist=False)
