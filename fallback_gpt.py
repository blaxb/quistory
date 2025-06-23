import os
import httpx
import json
import re
from typing import List

# ——— NEW: Explicitly ask for the items, not questions ———
SYSTEM_PROMPT = """
You are a helpful assistant that generates a “guess-the-list” quiz. 
When given a topic, you must respond with *only* a JSON array of strings,
each string being one of the things to guess. 
Do NOT produce questions—just list the actual items (e.g. for “U.S. Presidents” list “George Washington”, “John Adams”, etc.).
"""

MAX_ITEMS = 500

async def generate_quiz_with_gpt(topic: str) -> List[str]:
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
            {"role": "user",    "content": f"Generate a JSON array of items to guess for the topic: \"{topic}\"."}
        ],
        "max_tokens": 800,
        "n": 1,
        "temperature": 0.7,
    }

    async with httpx.AsyncClient() as client:
        resp = await client.post(url, json=payload, headers=headers)
        resp.raise_for_status()
        data = resp.json()

    content = data["choices"][0]["message"]["content"].strip()

    # 1) Try to parse as JSON
    try:
        parsed = json.loads(content)
        if isinstance(parsed, list) and all(isinstance(i, str) for i in parsed):
            return parsed[:MAX_ITEMS]
        if isinstance(parsed, dict):
            for v in parsed.values():
                if isinstance(v, list) and all(isinstance(i, str) for i in v):
                    return v[:MAX_ITEMS]
    except json.JSONDecodeError:
        pass

    # 2) Fallback: split lines and strip JSON noise
    lines = [l.strip() for l in content.splitlines() if l.strip()]
    cleaned: List[str] = []
    for line in lines:
        if re.fullmatch(r'[\{\}\[\]]+,?', line): continue
        if re.match(r'^".*":\s*(\[)?', line):    # skip keys
            continue
        item = re.sub(r'^[\-\d\.]+\s*', '', line)   # drop bullets/numbers
        item = item.rstrip('",')                    # drop trailing commas/quotes
        item = item.lstrip('"')                     # drop leading quote
        item = item.strip()
        if item:
            cleaned.append(item)
    return cleaned[:MAX_ITEMS]

