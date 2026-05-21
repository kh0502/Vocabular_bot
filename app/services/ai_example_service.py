from google import genai

from app.config import settings


class AIExampleService:
    def __init__(self):
        if not settings.gemini_api_key:
            self.client = None
        else:
            self.client = genai.Client(api_key=settings.gemini_api_key)

    async def generate_example(self, russian: str, english: str, synonyms: str = "") -> str:
        """
        Generates an explanation using Google Gemini API.
        The function is async because telegram handlers are async,
        but the google-genai call is simple and fast enough for this project.
        """
        if not self.client:
            return (
                "Gemini API key is not configured. Add GEMINI_API_KEY to your .env file.\n\n"
                f"Word: {english}\n"
                f"Meaning: {russian}"
            )

        prompt = f"""
Create a helpful vocabulary explanation for a student.

Word: {english}
Russian meaning: {russian}
Synonyms: {synonyms or 'none'}

Return the answer in this exact structure:
1. Meaning: short explanation in simple English.
2. When to use: explain when this word is natural.
3. Examples: give 3 simple English sentences.
4. Similar words: list useful synonyms if possible.

Keep it clear and not too long.
""".strip()

        response = self.client.models.generate_content(
            model=settings.gemini_model,
            contents=prompt,
        )

        return response.text.strip() if response.text else "Gemini did not return text."
