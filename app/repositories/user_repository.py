from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User


class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_telegram_id(self, telegram_id: int) -> User | None:
        result = await self.session.execute(select(User).where(User.telegram_id == telegram_id))
        return result.scalar_one_or_none()

    async def create(self, telegram_id: int, full_name: str) -> User:
        user = User(telegram_id=telegram_id, full_name=full_name, is_logged_in=True)
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def set_login_status(self, telegram_id: int, status: bool) -> None:
        user = await self.get_by_telegram_id(telegram_id)
        if user:
            user.is_logged_in = status
            await self.session.commit()
