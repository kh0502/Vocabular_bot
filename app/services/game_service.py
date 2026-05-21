import random
from sqlalchemy import select, update, delete, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.game import Game, GameItem
from app.models.round import RoundState
from app.models.word import Word
from app.services.parser import is_correct_answer
from app.repositories.example_repository import ExampleRepository
from app.services.ai_example_service import AIExampleService


class GameService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_game(self, user_id: int) -> tuple[bool, str]:
        words_result = await self.session.execute(select(Word).where(Word.user_id == user_id))
        words = list(words_result.scalars().all())

        if len(words) < 20:
            return False, f"Нужно минимум 20 слов. Сейчас у тебя: {len(words)}."

        await self.session.execute(
            update(Game)
            .where(Game.user_id == user_id, Game.is_active == True)
            .values(is_active=False)
        )

        selected_words = random.sample(words, 20)
        game = Game(user_id=user_id, is_active=True)
        self.session.add(game)
        await self.session.flush()

        for word in selected_words:
            self.session.add(GameItem(game_id=game.id, word_id=word.id, score=0, wrong_count=0, is_completed=False))

        await self.session.commit()
        return True, "Новая игра создана. Я выбрал 20 случайных слов. Напиши /round чтобы начать."

    async def get_active_game(self, user_id: int) -> Game | None:
        result = await self.session.execute(
            select(Game).where(Game.user_id == user_id, Game.is_active == True).order_by(Game.id.desc())
        )
        return result.scalars().first()

    async def start_round(self, telegram_id: int, user_id: int) -> tuple[bool, str]:
        return await self._start_custom_round(telegram_id, user_id, review_only=False)

    async def start_review_round(self, telegram_id: int, user_id: int) -> tuple[bool, str]:
        return await self._start_custom_round(telegram_id, user_id, review_only=True)

    async def _start_custom_round(self, telegram_id: int, user_id: int, review_only: bool) -> tuple[bool, str]:
        game = await self.get_active_game(user_id)
        if not game:
            return False, "У тебя нет активной игры. Напиши /newgame."

        previous_state = await self.get_round_state(telegram_id)
        previous_ids = set()
        if previous_state and previous_state.previous_item_ids:
            previous_ids = {int(x) for x in previous_state.previous_item_ids.split(",") if x}

        conditions = [GameItem.game_id == game.id, GameItem.is_completed == False]
        if review_only:
            conditions.append(GameItem.wrong_count >= 3)
        if previous_ids:
            conditions.append(GameItem.id.not_in(previous_ids))

        result = await self.session.execute(select(GameItem).where(*conditions))
        available = list(result.scalars().all())

        if len(available) < 5:
            conditions = [GameItem.game_id == game.id, GameItem.is_completed == False]
            if review_only:
                conditions.append(GameItem.wrong_count >= 3)
            result = await self.session.execute(select(GameItem).where(*conditions))
            available = list(result.scalars().all())

        if not available:
            if review_only:
                return False, "Пока нет слов для повторения. Они появятся, когда ты ответишь неправильно 3 раза на одно слово."
            game.is_active = False
            await self.session.commit()
            return False, "Поздравляю! Игра закончена. Все слова набрали 3 балла."

        selected = random.sample(available, min(5, len(available)))
        selected_ids = [str(item.id) for item in selected]

        await self.session.execute(delete(RoundState).where(RoundState.telegram_id == telegram_id))
        self.session.add(
            RoundState(
                telegram_id=telegram_id,
                game_id=game.id,
                question_item_ids=",".join(selected_ids),
                current_index=0,
                previous_item_ids=",".join(selected_ids),
                mode="review" if review_only else "translate",
            )
        )
        await self.session.commit()

        intro = "🔁 Режим повторения.\n\n" if review_only else ""
        return True, intro + await self.build_current_question(telegram_id)

    async def get_round_state(self, telegram_id: int) -> RoundState | None:
        result = await self.session.execute(select(RoundState).where(RoundState.telegram_id == telegram_id))
        return result.scalar_one_or_none()

    async def build_current_question(self, telegram_id: int) -> str:
        state = await self.get_round_state(telegram_id)
        if not state:
            return "Раунд не найден. Напиши /round."

        item_ids = [int(x) for x in state.question_item_ids.split(",") if x]
        if state.current_index >= len(item_ids):
            return "Раунд завершён. Напиши /round для следующей пятёрки."

        item_id = item_ids[state.current_index]
        result = await self.session.execute(
            select(GameItem, Word).join(Word, Word.id == GameItem.word_id).where(GameItem.id == item_id)
        )
        row = result.first()
        if not row:
            return "Слово не найдено."

        item, word = row
        mode_title = "Повторение" if state.mode == "review" else "Вопрос"
        return (
            f"{mode_title} {state.current_index + 1}/{len(item_ids)}\n"
            f"Переведи на английский:\n\n"
            f"🇷🇺 {word.russian}\n\n"
            f"Балл: {item.score}/3\n"
            f"Ошибок: {item.wrong_count}"
        )

    async def answer_current_question(self, telegram_id: int, answer: str) -> str:
        state = await self.get_round_state(telegram_id)
        if not state:
            return "Сейчас нет активного раунда. Напиши /round."

        item_ids = [int(x) for x in state.question_item_ids.split(",") if x]
        if state.current_index >= len(item_ids):
            return "Этот раунд уже завершён. Напиши /round."

        item_id = item_ids[state.current_index]
        result = await self.session.execute(
            select(GameItem, Word).join(Word, Word.id == GameItem.word_id).where(GameItem.id == item_id)
        )
        row = result.first()
        if not row:
            return "Ошибка: слово не найдено."

        item, word = row
        correct = is_correct_answer(answer, word.english, word.synonyms)

        if correct:
            item.score = min(3, item.score + 1)
            feedback = f"✅ Правильно! Ответ: {word.english}"
        else:
            item.score = max(0, item.score - 1)
            item.wrong_count += 1
            synonyms = f"\nСинонимы: {word.synonyms}" if word.synonyms else ""
            feedback = f"❌ Неправильно. Правильный ответ: {word.english}{synonyms}\nКоличество ошибок по этому слову: {item.wrong_count}"
            if item.wrong_count == 3:
                feedback += "\n🔁 Это слово добавлено в режим повторения /review."

        if item.score >= 3:
            item.is_completed = True
            feedback += "\n🏆 Это слово набрало 3 балла и удалено из активной игры."

        state.current_index += 1
        await self.session.commit()

        if state.current_index >= len(item_ids):
            if state.mode == "review":
                return feedback + "\n\nРаунд повторения завершён. Напиши /review для следующего повторения."
            return feedback + "\n\nРаунд завершён. Напиши /round для следующей пятёрки."

        next_question = await self.build_current_question(telegram_id)
        return feedback + "\n\n" + next_question

    async def score_text(self, user_id: int) -> str:
        game = await self.get_active_game(user_id)
        if not game:
            return "Активной игры нет. Напиши /newgame."

        result = await self.session.execute(
            select(GameItem, Word).join(Word, Word.id == GameItem.word_id).where(GameItem.game_id == game.id).order_by(GameItem.is_completed, GameItem.score.desc())
        )
        rows = result.all()
        completed = sum(1 for item, _ in rows if item.is_completed)
        total = len(rows)
        review_count = sum(1 for item, _ in rows if item.wrong_count >= 3 and not item.is_completed)

        lines = [f"📊 Прогресс: {completed}/{total} слов завершено", f"🔁 Слов для повторения: {review_count}\n"]
        for item, word in rows:
            status = "✅" if item.is_completed else "🔄"
            review = " | review" if item.wrong_count >= 3 and not item.is_completed else ""
            lines.append(f"{status} {word.russian} — {word.english}: {item.score}/3, ошибок: {item.wrong_count}{review}")
        return "\n".join(lines)

    async def examples_text(self, user_id: int, query: str | None = None) -> str:
        """
        First checks the database for a saved example.
        If there is no saved example, it asks Gemini API, saves the result,
        and sends it to the user.
        """
        if not query:
            return (
                "Напиши слово после команды.\n\n"
                "Пример:\n"
                "/example pondered\n\n"
                "Или обычным сообщением:\n"
                "пример pondered"
            )

        like = f"%{query.lower()}%"
        result = await self.session.execute(
            select(Word)
            .where(
                Word.user_id == user_id,
                or_(
                    Word.english.ilike(like),
                    Word.russian.ilike(like),
                    Word.synonyms.ilike(like),
                ),
            )
            .order_by(Word.id.desc())
        )
        word = result.scalars().first()

        if not word:
            return (
                f"Я не нашёл слово: {query}\n"
                "Проверь, что ты добавил его через /addwords."
            )

        example_repo = ExampleRepository(self.session)
        saved = await example_repo.get_by_word_id(word.id)

        if saved:
            return (
                "📌 Пример найден в базе:\n\n"
                f"🇷🇺 {word.russian}\n"
                f"🇬🇧 {word.english}\n\n"
                f"{saved.example_text}"
            )

        ai = AIExampleService()
        generated = await ai.generate_example(word.russian, word.english, word.synonyms)
        await example_repo.save(word.id, generated)

        return (
            "🤖 Примера не было в базе, поэтому я создал его через Gemini и сохранил.\n\n"
            f"🇷🇺 {word.russian}\n"
            f"🇬🇧 {word.english}\n\n"
            f"{generated}"
        )
