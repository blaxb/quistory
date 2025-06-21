kimport os
import httpx
import json
from typing import List

# ────────────────────────────────────────────────────────────────────────────
# System prompt: ask only for a JSON array of concrete items (no questions!)
# ────────────────────────────────────────────────────────────────────────────
SYSTEM_PROMPT = (
    "You are a helpful assistant.  When I give you a topic that represents a "
    "category (for example “U.S. Presidents” or “NCAA Division I basketball programs”), "
    "you must respond with exactly one thing: a JSON array of the actual items "
    "in that category, as strings.  Do NOT output any questions, explanations, or "
    "bullets—only the JSON array.  \n\n"
    "Example for “U.S. Presidents”:\n"
    "[\"George Washington\", \"John Adams\", \"Thomas Jefferson\", …]"
)

async def generate_quiz_with_gpt(topic: str) -> List[str]:
    """Call OpenAI’s chat endpoint and parse out a straight list of items."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("Missing OPENAI_API_KEY")

    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": "gpt-3.5-turbo",
        "messages": [
            {"role": "system",  "content": SYSTEM_PROMPT},
            {"role": "user",    "content": f"List all “{topic}” as a JSON array of strings."}
        ],
        "max_tokens": 800,
        "n": 1,
        "temperature": 0.2,
    }

    async with httpx.AsyncClient() as client:
        resp = await client.post(url, json=payload, headers=headers)
        resp.raise_for_status()
        data = resp.json()

    raw = data["choices"][0]["message"]["content"]

    # 1) Try to parse it directly as JSON:
    try:
        items = json.loads(raw)
        if isinstance(items, list) and all(isinstance(i, str) for i in items):
            return items
    except json.JSONDecodeError:
        pass

    # 2) Fallback: split lines and strip any numbering/bullets
    lines = [ln.strip() for ln in raw.splitlines() if ln.strip()]
    cleaned = [ln.lstrip("-0123456789. ").strip() for ln in lines]
    return cleaned

