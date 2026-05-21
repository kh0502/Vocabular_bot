from sqlalchemy import BigInteger, Integer, String, Text, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base


class RoundState(Base):
    __tablename__ = "round_states"

    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    game_id: Mapped[int] = mapped_column(Integer, nullable=False)
    question_item_ids: Mapped[str] = mapped_column(Text, nullable=False)
    current_index: Mapped[int] = mapped_column(Integer, default=0)
    previous_item_ids: Mapped[str] = mapped_column(Text, default="")
    mode: Mapped[str] = mapped_column(String(50), default="translate")
    updated_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
