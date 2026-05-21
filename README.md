# Vocabulary Game Telegram Bot

Telegram bot for learning vocabulary.  
You send a list of words in this format:

```text
первобытный, древнейший — primeval | synonyms: ancient, prehistoric, primitive, primordial
порошковый — powdered | synonyms: ground, crushed, pulverized
обдумал, размышлял — pondered | synonyms: thought about, considered, reflected on
```

The bot creates a game:
- randomly chooses **20 words** from the list;
- asks only **5 questions per round**;
- asks in **Russian**, user answers in **English**;
- accepts the main English word and synonyms;
- each word has score from **0 to 3**;
- correct answer: **+1**;
- wrong answer: **-1**, but not below 0;
- word is removed from active game after score reaches **3**;
- words from the previous round will not appear in the next round.

---

## 1. Install Python packages

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

If PowerShell blocks activation, run:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

Then activate again:

```powershell
.venv\Scripts\activate
```

---

## 2. Create PostgreSQL database

Option A: with Docker:

```bash
docker compose up -d
```

Option B: create database manually in PostgreSQL:

```sql
CREATE DATABASE vocab_game_bot;
```

---

## 3. Create `.env`

Copy `.env.example` to `.env` and put your bot token:

```env
BOT_TOKEN=123456:ABCDEF...
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/vocab_game_bot
```

---

## 4. Run bot

```bash
python -m app.main
```

---

## Bot commands

```text
/start - start bot
/signup - create profile
/login - login by Telegram ID
/logout - logout
/addwords - send word list
/newgame - create new game from your words
/round - get 5 questions
/score - show progress
/review - repeat words with 3 wrong answers
/examples - show examples and when to use words
/help - help
```

---

## Word format

Recommended format:

```text
русское значение — english | synonyms: synonym1, synonym2, synonym3
```

You can also use `-` instead of `—`.

Example:

```text
быстрый взгляд / быстро взглянуть — glance | synonyms: quick look, look briefly
```



---

## New functions

### `/review`

This command starts a review round. It asks only the words where you made **3 or more mistakes**.

```text
/review
```

### `/examples`

This command shows where and when you can use words.

Show examples for active game words:

```text
/examples
```

Search one word:

```text
/examples pondered
```


---

## AI examples

Now the bot can connect to Google Gemini API.

How it works:

1. You write:

```text
/example pondered
```

or:

```text
пример pondered
```

2. The bot checks PostgreSQL table `word_examples`.
3. If an example already exists, it sends it from the database.
4. If there is no example, it sends a request to Google Gemini API.
5. The generated answer is saved in PostgreSQL, so next time the bot will not call AI again.

Add this to `.env`:

```env
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-2.5-flash-lite
```

Install the new library:

```bash
pip install google-genai==1.38.0
```

If you already installed all requirements, run:

```bash
pip install -r requirements.txt
```

New commands for BotFather:

```text
example - Show AI example for one word
examples - Show AI example for one word
```


---

## Google Gemini API setup

This version uses **Google Gemini API**, not OpenAI.

Add this to `.env`:

```env
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-2.5-flash-lite
```

Install packages:

```bash
pip install -r requirements.txt
```

How to use examples:

```text
/example pondered
```

or:

```text
пример pondered
```

How it works:

1. Bot checks PostgreSQL table `word_examples`.
2. If the example exists, bot sends it from database.
3. If the example does not exist, bot asks Google Gemini API.
4. Bot saves Gemini's answer in PostgreSQL.
5. Next time the same word is taken from database.
