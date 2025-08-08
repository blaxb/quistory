import asyncio
from typing import List
from fallback_gpt import generate_quiz_with_gpt


def generate_quiz(topic: str) -> List[str]:
    """
    Synchronous wrapper around the async generator.
    Always returns List[str].
    Works whether or not an event loop is already running.
    """
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        # If we're already in an event loop (e.g., some ASGI setups),
        # spin a fresh loop just for this call.
        new_loop = asyncio.new_event_loop()
        try:
            return new_loop.run_until_complete(generate_quiz_with_gpt(topic))
        finally:
            new_loop.close()
    else:
        return asyncio.run(generate_quiz_with_gpt(topic))

