from sqlalchemy import ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base


class WordExample(Base):
    __tablename__ = "word_examples"

    id: Mapped[int] = mapped_column(primary_key=True)
    word_id: Mapped[int] = mapped_column(ForeignKey("words.id", ondelete="CASCADE"), unique=True, index=True)
    example_text: Mapped[str] = mapped_column(Text, nullable=False)

    word = relationship("Word")
