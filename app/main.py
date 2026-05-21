import asyncio
import logging

from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

from app.config import settings
from app.db import init_db
from app.handlers.common import start, help_command, signup, login, logout
from app.handlers.words import addwords, receive_words
from app.handlers.game import newgame, round_command, score, review, examples, example, receive_answer


logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)


async def text_router(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    handled_words = await receive_words(update, context)
    if handled_words:
        return

    handled_answer = await receive_answer(update, context)
    if handled_answer:
        return

    await update.message.reply_text("Я не понял сообщение. Напиши /help.")


async def post_init(application: Application) -> None:
    await init_db()


def main() -> None:
    app = Application.builder().token(settings.bot_token).post_init(post_init).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("signup", signup))
    app.add_handler(CommandHandler("login", login))
    app.add_handler(CommandHandler("logout", logout))
    app.add_handler(CommandHandler("addwords", addwords))
    app.add_handler(CommandHandler("newgame", newgame))
    app.add_handler(CommandHandler("round", round_command))
    app.add_handler(CommandHandler("score", score))
    app.add_handler(CommandHandler("review", review))
    app.add_handler(CommandHandler("examples", examples))
    app.add_handler(CommandHandler("example", example))

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_router))

    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
