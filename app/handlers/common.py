from telegram import Update
from telegram.ext import ContextTypes
from app.db import AsyncSessionLocal
from app.repositories.user_repository import UserRepository


HELP_TEXT = """🎮 Vocabulary Game Bot

Команды:
/signup - создать профиль
/login - войти
/logout - выйти
/addwords - добавить список слов
/newgame - создать игру из 20 случайных слов
/round - получить 5 вопросов
/score - посмотреть баллы
/review - повторить слова с 3 ошибками
/examples - показать примеры использования слов
/help - помощь

Формат слов:
русское значение — english | synonyms: synonym1, synonym2
"""


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Привет! Я бот для игры со словами. Напиши /signup, потом /addwords.\n\n" + HELP_TEXT
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(HELP_TEXT)


async def signup(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    tg_user = update.effective_user
    async with AsyncSessionLocal() as session:
        repo = UserRepository(session)
        user = await repo.get_by_telegram_id(tg_user.id)
        if user:
            user.is_logged_in = True
            await session.commit()
            await update.message.reply_text("Ты уже зарегистрирован. Я включил login status.")
            return

        full_name = tg_user.full_name or tg_user.username or str(tg_user.id)
        await repo.create(tg_user.id, full_name)
        await update.message.reply_text("✅ Регистрация успешна. Теперь отправь список слов через /addwords.")


async def login(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    async with AsyncSessionLocal() as session:
        repo = UserRepository(session)
        user = await repo.get_by_telegram_id(update.effective_user.id)
        if not user:
            await update.message.reply_text("Ты ещё не зарегистрирован. Напиши /signup.")
            return
        await repo.set_login_status(update.effective_user.id, True)
        await update.message.reply_text("✅ Ты вошёл в аккаунт.")


async def logout(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    async with AsyncSessionLocal() as session:
        repo = UserRepository(session)
        user = await repo.get_by_telegram_id(update.effective_user.id)
        if not user:
            await update.message.reply_text("Ты ещё не зарегистрирован.")
            return
        await repo.set_login_status(update.effective_user.id, False)
        await update.message.reply_text("🚪 Ты вышел из аккаунта.")
