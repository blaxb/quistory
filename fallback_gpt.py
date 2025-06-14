kkk# fallback_gpt.py

from dotenv import load_dotenv
load_dotenv()    # ← load OPENAI_API_KEY from your .env locally

import os
import httpx
import json
from typing import List

SYSTEM_PROMPT = (
    "You are a helpful assistant that generates a quiz. "
    "When given a topic, respond with a JSON array of strings – "
    "each one a quiz item for that topic."
)

async def generate_quiz_with_gpt(topic: str) -> List[str]:
    """Call OpenAI via HTTPX and return a simple list of quiz items."""
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
            {"role": "user",    "content": f"Generate a quiz list on \"{topic}\"."}
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

    # 1) Try JSON-parsed list
    try:
        items = json.loads(content)
        if isinstance(items, list) and all(isinstance(i, str) for i in items):
            return items
    except json.JSONDecodeError:
        pass

    # 2) Fallback: split lines, strip bullets or numbering
    lines = [line.strip() for line in content.splitlines() if line.strip()]
    cleaned = [line.lstrip("-0123456789. ").strip() for line in lines]
    return cleaned

