import asyncio
from typing import List, Dict
from fallback_gpt import generate_quiz_with_gpt


def _run(coro):
    """Run an async coroutine safely from sync code (handles existing loops)."""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        new_loop = asyncio.new_event_loop()
        try:
            return new_loop.run_until_complete(coro)
        finally:
            new_loop.close()
    else:
        return asyncio.run(coro)


def generate_quiz(topic: str) -> Dict[str, object]:
    """
    Returns a dict in the exact shape the frontend expects.
    {
      "quiz_type": "list",
      "topic": "<topic>",
      "items": ["...", "...", ...]
    }
    """
    items: List[str] = _run(generate_quiz_with_gpt(topic))
    return {
        "quiz_type": "list",
        "topic": topic,
        "items": items,
    }

