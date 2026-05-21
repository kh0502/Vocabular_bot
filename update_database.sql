-- Run this only if you already created the old database before this update.
-- It adds the new column for counting wrong answers.

ALTER TABLE game_items
ADD COLUMN IF NOT EXISTS wrong_count INTEGER NOT NULL DEFAULT 0;


-- AI examples table. Run this if your database already exists.
CREATE TABLE IF NOT EXISTS word_examples (
    id SERIAL PRIMARY KEY,
    word_id INTEGER NOT NULL UNIQUE REFERENCES words(id) ON DELETE CASCADE,
    example_text TEXT NOT NULL
);
