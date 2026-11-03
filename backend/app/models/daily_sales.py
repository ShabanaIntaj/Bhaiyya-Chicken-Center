
from sqlalchemy import Column, Integer, Date, Numeric, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.sql import func

from app.database import Base


class DailySales(Base):
    __tablename__ = "daily_sales"

    id = Column(Integer, primary_key=True, index=True)

    sale_date = Column(Date, nullable=False, unique=True)

    total_quantity = Column(Numeric(10, 3), nullable=False)

    recorded_by = Column(Integer, ForeignKey("users.id"), nullable=False)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
