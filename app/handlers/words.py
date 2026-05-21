from telegram import Update
from telegram.ext import ContextTypes
from app.db import AsyncSessionLocal
from app.repositories.user_repository import UserRepository
from app.repositories.word_repository import WordRepository
from app.services.parser import parse_word_list


async def addwords(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    context.user_data["waiting_words"] = True
    await update.message.reply_text(
        "Отправь список слов одним сообщением.\n\n"
        "Формат:\n"
        "русское значение — english | synonyms: synonym1, synonym2"
    )


async def receive_words(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    if not context.user_data.get("waiting_words"):
        return False

    context.user_data["waiting_words"] = False
    text = update.message.text or ""
    words = parse_word_list(text)

    if not words:
        await update.message.reply_text("Я не смог распознать слова. Проверь формат и попробуй /addwords ещё раз.")
        return True

    async with AsyncSessionLocal() as session:
        user_repo = UserRepository(session)
        user = await user_repo.get_by_telegram_id(update.effective_user.id)

        if not user or not user.is_logged_in:
            await update.message.reply_text("Сначала напиши /signup или /login.")
            return True

        word_repo = WordRepository(session)
        count = await word_repo.replace_words(user.id, words)

    await update.message.reply_text(
        f"✅ Слова сохранены: {count}\n"
        f"Теперь напиши /newgame, чтобы создать игру."
    )
    return True
