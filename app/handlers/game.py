from telegram import Update
from telegram.ext import ContextTypes
from app.db import AsyncSessionLocal
from app.repositories.user_repository import UserRepository
from app.services.game_service import GameService


async def _get_logged_user(update: Update, session):
    repo = UserRepository(session)
    user = await repo.get_by_telegram_id(update.effective_user.id)
    if not user:
        await update.message.reply_text("Сначала зарегистрируйся: /signup")
        return None
    if not user.is_logged_in:
        await update.message.reply_text("Ты вышел из аккаунта. Напиши /login.")
        return None
    return user


async def newgame(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    async with AsyncSessionLocal() as session:
        user = await _get_logged_user(update, session)
        if not user:
            return

        service = GameService(session)
        ok, message = await service.create_game(user.id)
        await update.message.reply_text(message)


async def round_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    async with AsyncSessionLocal() as session:
        user = await _get_logged_user(update, session)
        if not user:
            return

        service = GameService(session)
        ok, message = await service.start_round(update.effective_user.id, user.id)
        await update.message.reply_text(message)


async def score(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    async with AsyncSessionLocal() as session:
        user = await _get_logged_user(update, session)
        if not user:
            return

        service = GameService(session)
        await update.message.reply_text(await service.score_text(user.id))


async def review(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    async with AsyncSessionLocal() as session:
        user = await _get_logged_user(update, session)
        if not user:
            return

        service = GameService(session)
        ok, message = await service.start_review_round(update.effective_user.id, user.id)
        await update.message.reply_text(message)


async def examples(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = " ".join(context.args).strip() if context.args else None

    async with AsyncSessionLocal() as session:
        user = await _get_logged_user(update, session)
        if not user:
            return

        service = GameService(session)
        text = await service.examples_text(user.id, query)
        await update.message.reply_text(text)


async def example(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Alias for /examples
    await examples(update, context)


async def receive_answer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    if context.user_data.get("waiting_words"):
        return False

    text = (update.message.text or "").strip()
    lowered = text.lower()

    if lowered.startswith("пример ") or lowered.startswith("example "):
        query = text.split(maxsplit=1)[1].strip()
        async with AsyncSessionLocal() as session:
            user = await _get_logged_user(update, session)
            if not user:
                return True

            service = GameService(session)
            result = await service.examples_text(user.id, query)
            await update.message.reply_text(result)
            return True

    async with AsyncSessionLocal() as session:
        user = await _get_logged_user(update, session)
        if not user:
            return True

        service = GameService(session)
        state = await service.get_round_state(update.effective_user.id)
        if not state:
            return False

        result = await service.answer_current_question(update.effective_user.id, update.message.text or "")
        await update.message.reply_text(result)
        return True
