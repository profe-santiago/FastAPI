from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Boolean, Numeric
from datetime import datetime
from app.database import Base


class Product(Base):
    __tablename__ = "products"

    id:          Mapped[int]   = mapped_column(primary_key=True, index=True)
    name:        Mapped[str]   = mapped_column(String(200))
    description: Mapped[str]   = mapped_column(String(500), default="")
    price:       Mapped[float] = mapped_column(Numeric(10, 2))
    stock:       Mapped[int]   = mapped_column(default=0)
    is_active:   Mapped[bool]  = mapped_column(Boolean, default=True)
    created_at:  Mapped[datetime] = mapped_column(default=datetime.utcnow)
