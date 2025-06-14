import os
import asyncio
import httpx

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise RuntimeError("Missing OPENAI_API_KEY")

SYSTEM_PROMPT = (
    "You are a helpful assistant that generates a quiz. "
    "When given a topic, respond with a JSON array of strings "
    "– each one a quiz item for that topic."
)

async def generate_quiz_with_gpt(topic: str) -> list[str]:
    """Call OpenAI via HTTPX and return a simple list of quiz items."""
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json",
        # No other headers, so nothing non-ASCII slips through
    }
    payload = {
        "model": "gpt-3.5-turbo",
        "messages": [
            {"role": "system",  "content": SYSTEM_PROMPT},
            {"role": "user",    "content": f"Generate a quiz list on “{topic}”."}
        ],
        "max_tokens": 500,
        "n": 1,
        "temperature": 0.7,
    }

    async with httpx.AsyncClient() as client:
        resp = await client.post(url, json=payload, headers=headers)
        resp.raise_for_status()
        data = resp.json()

    # Extract the assistant’s content
    content = data["choices"][0]["message"]["content"]

    # Expect either a JSON list or a plain newline list. Try JSON first:
    try:
        items = httpx.decouple.json.loads(content)
        if isinstance(items, list) and all(isinstance(i, str) for i in items):
            return items
    except Exception:
        pass

    # Fallback: split by lines and strip bullets/numbers
    lines = [line.strip() for line in content.splitlines() if line.strip()]
    cleaned = [line.lstrip("-0123456789. ") for line in lines]
    return cleaned

