from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.example import WordExample


class ExampleRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_word_id(self, word_id: int) -> WordExample | None:
        result = await self.session.execute(
            select(WordExample).where(WordExample.word_id == word_id)
        )
        return result.scalar_one_or_none()

    async def save(self, word_id: int, example_text: str) -> WordExample:
        existing = await self.get_by_word_id(word_id)
        if existing:
            existing.example_text = example_text
            await self.session.commit()
            await self.session.refresh(existing)
            return existing

        item = WordExample(word_id=word_id, example_text=example_text)
        self.session.add(item)
        await self.session.commit()
        await self.session.refresh(item)
        return item
