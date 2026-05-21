from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base


class Word(Base):
    __tablename__ = "words"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    russian: Mapped[str] = mapped_column(Text, nullable=False)
    english: Mapped[str] = mapped_column(String(255), nullable=False)
    synonyms: Mapped[str] = mapped_column(Text, default="")

    user = relationship("User", back_populates="words")
