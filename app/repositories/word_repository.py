from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.word import Word


class WordRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def replace_words(self, user_id: int, words: list[dict]) -> int:
        await self.session.execute(delete(Word).where(Word.user_id == user_id))
        for item in words:
            self.session.add(
                Word(
                    user_id=user_id,
                    russian=item["russian"],
                    english=item["english"],
                    synonyms=", ".join(item.get("synonyms", [])),
                )
            )
        await self.session.commit()
        return len(words)

    async def list_user_words(self, user_id: int) -> list[Word]:
        result = await self.session.execute(select(Word).where(Word.user_id == user_id))
        return list(result.scalars().all())
