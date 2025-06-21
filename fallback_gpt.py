import os
import httpx
import json
from typing import List, Union, Dict, Any

SYSTEM_PROMPT = (
    "You are a helpful assistant that generates a quiz. "
    "When given a topic, respond with a JSON array of strings – "
    "each one a quiz item for that topic."
)

async def generate_quiz_with_gpt(topic: str) -> List[Union[str, Dict[str, Any]]]:
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
            {"role": "user",    "content": f"Generate a quiz for “{topic}”."}
        ],
        "max_tokens": 500,
        "n": 1,
        "temperature": 0.7,
    }

    async with httpx.AsyncClient() as client:
        resp = await client.post(url, json=payload, headers=headers)
        resp.raise_for_status()
        data = resp.json()

    content = data["choices"][0]["message"]["content"]

    # ── Strip any ```…``` code fences ─────────────────
    lines = content.splitlines()
    if lines and lines[0].startswith("```"):
        # drop the first and last fence lines if they exist
        if lines[-1].startswith("```"):
            lines = lines[1:-1]
        content = "\n".join(lines)

    # ── 1) Try to JSON‐parse a clean array ────────────────
    try:
        items = json.loads(content)
        if isinstance(items, list) and all(isinstance(i, str) for i in items):
            return items
    except json.JSONDecodeError:
        pass

    # ── 2) Fallback: split on lines and strip bullets ────
    lines = [l.strip() for l in content.splitlines() if l.strip()]
    cleaned = [l.lstrip("-0123456789. ").strip() for l in lines]
    return cleaned

