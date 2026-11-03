
from sqlalchemy import Column, Integer, Boolean
from app.database import Base


class ShopSettings(Base):
    __tablename__ = "shop_settings"

    id = Column(Integer, primary_key=True, default=1)
    is_open = Column(Boolean, nullable=False, default=True)
