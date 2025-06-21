import os
import httpx
import json
from typing import List

# ────────────────────────────────────────────────────────────────────────────
# New system prompt: ask for items, not questions
# ────────────────────────────────────────────────────────────────────────────
SYSTEM_PROMPT = (
    "You are a helpful assistant that, when given a topic representing a category "
    "(e.g. “U.S. Presidents” or “NCAA Division I basketball programs”), "
    "returns exactly a JSON array of the concrete items that belong to that category. "
    "Do NOT output any questions or commentary—just the array of strings. "
    "Example output for “U.S. Presidents”: "
    "[\"George Washington\", \"John Adams\", \"Thomas Jefferson\", …]."
)

async def generate_quiz_with_gpt(topic: str) -> List[str]:
    """Call OpenAI via HTTPX and return a simple list of quiz items (answers)."""
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
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"List all “{topic}” as a JSON array of strings."}
        ],
        "max_tokens": 800,
        "n": 1,
        "temperature": 0.3,
    }

    async with httpx.AsyncClient() as client:
        resp = await client.post(url, json=payload, headers=headers)
        resp.raise_for_status()
        data = resp.json()

    content = data["choices"][0]["message"]["content"]

    # 1) Try JSON‐parsing directly
    try:
        items = json.loads(content)
        if isinstance(items, list) and all(isinstance(i, str) for i in items):
            return items
    except json.JSONDecodeError:
        pass

    # 2) Fallback: strip bullets/numbering and return lines
    lines = [line.strip() for line in content.splitlines() if line.strip()]
    cleaned = [line.lstrip("-0123456789. ").strip() for line in lines]
    return cleaned

