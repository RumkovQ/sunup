"""Short weather advice generation with a deterministic fallback."""

import aiohttp


class LLMService:
    def __init__(self, api_key: str, model: str, base_url: str):
        self.api_key, self.model, self.base_url = api_key, model, base_url

    async def clothing_advice(self, temperature: float, conditions: str, language: str = "ru") -> str:
        fallback = "Оденься по погоде." if language == "ru" else "Dress for the weather."
        if language == "both":
            fallback = "Оденься по погоде. / Dress for the weather."
        if not self.api_key:
            return fallback
        prompt_language = {"ru": "Russian", "en": "English", "both": "Russian and English"}.get(language, "Russian")
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": f"Give one short, friendly clothing tip in {prompt_language}. No preamble."},
                {"role": "user", "content": f"Temperature: {temperature} C. Conditions: {conditions}."},
            ],
            "temperature": 0.7,
            "max_tokens": 80,
        }
        try:
            headers = {"Authorization": f"Bearer {self.api_key}"}
            async with aiohttp.ClientSession() as session:
                async with session.post(f"{self.base_url}/chat/completions", json=payload, headers=headers, timeout=20) as response:
                    response.raise_for_status()
                    result = await response.json()
            return result["choices"][0]["message"]["content"].strip() or fallback
        except (aiohttp.ClientError, KeyError, IndexError, TypeError, ValueError):
            return fallback
