import re


def parse_word_list(text: str) -> list[dict]:
    """
    Parses lines like:
    русский — english | synonyms: one, two, three
    русский - english | synonyms: one, two
    """
    words = []

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        # Remove numbering like "1." or "1)"
        line = re.sub(r"^\s*\d+[\.\)]\s*", "", line)

        if "—" in line:
            left, right = line.split("—", 1)
        elif " - " in line:
            left, right = line.split(" - ", 1)
        else:
            continue

        russian = left.strip()
        right = right.strip()

        english_part = right
        synonyms = []

        if "|" in right:
            english_part, extra = right.split("|", 1)
            extra = extra.strip()
            extra = re.sub(r"^synonyms?\s*:\s*", "", extra, flags=re.IGNORECASE)
            synonyms = [s.strip() for s in extra.split(",") if s.strip()]

        english = english_part.strip()
        english = re.sub(r"\s+", " ", english)

        if russian and english:
            words.append(
                {
                    "russian": russian,
                    "english": english,
                    "synonyms": synonyms,
                }
            )

    return words


def normalize_answer(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^\w\s'-]", "", text, flags=re.UNICODE)
    text = re.sub(r"\s+", " ", text)
    return text


def is_correct_answer(answer: str, english: str, synonyms_text: str) -> bool:
    user_answer = normalize_answer(answer)
    accepted = [english]

    if synonyms_text:
        accepted.extend([s.strip() for s in synonyms_text.split(",") if s.strip()])

    accepted_normalized = {normalize_answer(x) for x in accepted}

    return user_answer in accepted_normalized
