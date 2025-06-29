import os
import httpx
import json
import re
from typing import List
from fastapi import HTTPException

# hard cap on items if user doesn't specify a number
MAX_ITEMS = 500

SYSTEM_PROMPT = """
You are a helpful assistant that generates a “guess-the-list” quiz.
When given a topic, respond with *only* a JSON array of strings,
each string being a correct, real-world instance of that topic.
"""

async def generate_quiz_with_gpt(topic: str) -> List[str]:
    # 1) Detect if user wants exactly N items
    m = re.search(r"\b(\d+)\b", topic)
    if m:
        desired = min(int(m.group(1)), MAX_ITEMS)
        user_prompt = (
            f"Generate a JSON array of **exactly** {desired} items to guess "
            f"for the topic: \"{topic}\"."
        )
        max_tokens = min(50 * desired, 2000)
    else:
        desired = None
        user_prompt = f"Generate a JSON array of items to guess for the topic: \"{topic}\"."
        max_tokens = 2000

    payload = {
        "model": "gpt-3.5-turbo",
        "messages": [
            {"role": "system",  "content": SYSTEM_PROMPT},
            {"role": "user",    "content": user_prompt},
        ],
        "max_tokens": max_tokens,
        "n": 1,
        "temperature": 0.2,            # ← very low temperature
    }

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("Missing OPENAI_API_KEY")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    # 2) Call OpenAI with retries
    timeout = httpx.Timeout(connect=10.0, read=60.0, write=60.0, pool=60.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        for attempt in range(3):
            try:
                resp = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    json=payload,
                    headers=headers
                )
                resp.raise_for_status()
                break
            except httpx.ReadTimeout:
                if attempt < 2:
                    continue
                raise HTTPException(
                    status_code=504,
                    detail="OpenAI API request timed out after multiple attempts"
                )

    data = resp.json()
    content = data["choices"][0]["message"]["content"].strip()

    # 3) Parse out a JSON array if possible
    items: List[str] = []
    try:
        parsed = json.loads(content)
        if isinstance(parsed, list) and all(isinstance(i, str) for i in parsed):
            items = parsed
    except json.JSONDecodeError:
        # fallback: regex extract
        arr_match = re.search(r"\[(.*)\]", content, flags=re.S)
        if arr_match:
            try:
                parsed = json.loads("[" + arr_match.group(1).rstrip().rstrip("]") + "]")
                if isinstance(parsed, list) and all(isinstance(i, str) for i in parsed):
                    items = parsed
            except json.JSONDecodeError:
                pass

    # 4) Simple line-split fallback
    if not items:
        lines = [l.strip() for l in content.splitlines() if l.strip()]
        for line in lines:
            if re.fullmatch(r"[\{\}\[\]],?", line):
                continue
            if re.match(r'^".*":\s*(\[)?', line):
                continue
            item = re.sub(r'^[\-\d\.]+\s*', '', line)
            item = item.lstrip('"').rstrip('",').strip()
            if item:
                items.append(item)

    # 5) Dedupe & apply initial limit
    unique = list(dict.fromkeys(items))
    limit = desired if desired is not None else MAX_ITEMS
    candidate_items = unique[:limit]

    # 6) Verify each via Wikipedia summary API
    verified: List[str] = []
    async with httpx.AsyncClient(timeout=10.0) as wiki:
        for item in candidate_items:
            title = item.replace(" ", "_")
            res = await wiki.get(f"https://en.wikipedia.org/api/rest_v1/page/summary/{title}")
            if res.status_code == 200:
                verified.append(item)
    return verified

