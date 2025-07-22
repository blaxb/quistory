# quiz_logic.py
import asyncio
from fallback_gpt import generate_quiz_with_gpt

def generate_quiz(topic: str) -> dict:
    """
    Synchronous wrapper around our async GPT list generator.
    Returns a dict that DRF can serialize directly.
    """
    # run the async function to get a List[str]
    items = asyncio.run(generate_quiz_with_gpt(topic))

    # pack into whatever shape you want; for example:
    return {
        "topic": topic,
        "items": items,
    }

