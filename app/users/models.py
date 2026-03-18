from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Boolean
from datetime import datetime
from app.database import Base

class User(Base):
    __tablename__ = "users"

    id:         Mapped[int]      = mapped_column(primary_key=True, index=True)
    name:       Mapped[str]      = mapped_column(String(100))
    email:      Mapped[str]      = mapped_column(String(255), unique=True, index=True)
    is_active:  Mapped[bool]     = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)