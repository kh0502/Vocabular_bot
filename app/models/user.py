from sqlalchemy import BigInteger, String, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    is_logged_in: Mapped[bool] = mapped_column(Boolean, default=True)

    words = relationship("Word", back_populates="user", cascade="all, delete-orphan")
    games = relationship("Game", back_populates="user", cascade="all, delete-orphan")
