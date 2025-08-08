# fallback_gpt.py
import os
import json
import re
from typing import List, Optional

import httpx

# hard cap on items if user doesn't specify a number
MAX_ITEMS = 500

SYSTEM_PROMPT = """
You are a helpful assistant that generates a "guess-the-list" quiz.
When given a topic, respond with ONLY a JSON array of strings,
each string being a correct, real-world instance of that topic.

IMPORTANT:
- Only interpret a number as "I want exactly N items" if it's clearly a count request,
  e.g. "top 10 presidents", "5 items", "# of 7 champions", etc.
- Do NOT treat standalone years (e.g. "2010") or other numbers buried in context as counts.
"""

def _synthetic_items(topic: str, n: int = 12) -> List[str]:
    """Fallback so the UI keeps working even if OpenAI is unavailable."""
    base = (topic or "").strip().rstrip(".") or "General knowledge"
    return [f"{base} item {i}" for i in range(1, n + 1)]


async def generate_quiz_with_gpt(topic: str) -> List[str]:
    """
    Generate a list of items for a quiz topic using OpenAI if possible,
    otherwise return a small synthetic list so the site never 500s.
    """
    # 1) Look for an explicit count pattern (not a year)
    count_match = re.search(
        r'\b(?:top|first|last|# of)\s+(\d{1,3})\b'           # top 10, first 5, last 3, # of 12
        r'|\b(\d{1,3})\s+(?:items|questions|members)\b',     # 7 items, 5 questions, 3 members
        topic,
        flags=re.IGNORECASE,
    )

    if count_match:
        desired = int(count_match.group(1) or count_match.group(2))
        desired = min(desired, MAX_ITEMS)
        user_prompt = (
            f'Generate a JSON array of EXACTLY {desired} items to guess '
            f'for the topic: "{topic}".'
        )
        max_tokens = min(50 * desired, 2000)
    else:
        desired = None
        user_prompt = f'Generate a JSON array of items to guess for the topic: "{topic}".'
        max_tokens = 2000

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        # No key set → return synthetic list so the app keeps working.
        return _synthetic_items(topic)

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": "gpt-3.5-turbo",  # keep your original model; adjust if you have access to newer ones
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        "max_tokens": max_tokens,
        "n": 1,
        "temperature": 0.2,
    }

    # 2) Call OpenAI with retries
    timeout = httpx.Timeout(connect=10.0, read=60.0, write=60.0, pool=60.0)
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp: Optional[httpx.Response] = None
            for attempt in range(3):
                try:
                    resp = await client.post(
                        "https://api.openai.com/v1/chat/completions",
                        json=payload,
                        headers=headers,
                    )
                    resp.raise_for_status()
                    break
                except httpx.ReadTimeout:
                    if attempt < 2:
                        continue
                    # give up after 3 tries, but do not crash the site
                    return _synthetic_items(topic)
                except httpx.HTTPError:
                    # network or HTTP status error → fall back
                    return _synthetic_items(topic)

            if resp is None:
                return _synthetic_items(topic)

            data = resp.json()
            content = (data["choices"][0]["message"]["content"] or "").strip()
    except Exception:
        # any unexpected error → fail soft
        return _synthetic_items(topic)

    # 3) Try to parse a JSON array directly
    items: List[str] = []
    try:
        parsed = json.loads(content)
        if isinstance(parsed, list) and all(isinstance(i, str) for i in parsed):
            items = parsed
    except json.JSONDecodeError:
        # fallback: pull out the first [...] block
        arr_match = re.search(r"\[(.*)\]", content, flags=re.S)
        if arr_match:
            try:
                candidate = "[" + arr_match.group(1).rstrip().rstrip("]") + "]"
                parsed = json.loads(candidate)
                if isinstance(parsed, list) and all(isinstance(i, str) for i in parsed):
                    items = parsed
            except json.JSONDecodeError:
                pass

    # 4) If still empty, split on lines
    if not items:
        for line in content.splitlines():
            line = line.strip()
            if not line or re.fullmatch(r"[\{\}\[\]],?", line):
                continue
            # strip leading bullets/numbers
            line = re.sub(r'^[\-\d\.]+\s*', '', line)
            # strip trailing commas or quotes
            line = line.lstrip('"').rstrip('",').strip()
            if line:
                items.append(line)

    # 5) Dedupe & enforce the desired or max cap
    unique = list(dict.fromkeys(items))
    limit = desired if desired is not None else MAX_ITEMS
    candidate_items = unique[:limit]

    # 6) Verify each via Wikipedia summary (best-effort; keep what resolves)
    verified: List[str] = []
    try:
        async with httpx.AsyncClient(timeout=10.0) as wiki:
            for item in candidate_items:
                title = item.replace(" ", "_")
                res = await wiki.get(f"https://en.wikipedia.org/api/rest_v1/page/summary/{title}")
                if res.status_code == 200:
                    verified.append(item)
    except Exception:
        # If the wiki check fails, just return what we have
        verified = candidate_items

    # final safety fallback
    if not verified:
        return _synthetic_items(topic)

    return verified

