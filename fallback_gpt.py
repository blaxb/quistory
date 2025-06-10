# fallback_gpt.py

import os
import json
import openai
import asyncio
from dotenv import load_dotenv

# Load your OpenAI key
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")
if not openai.api_key:
    raise ValueError("OPENAI_API_KEY not set in .env")

# Prompt template
STARTER_PROMPT = """
You are a trivia assistant. Create a 5-question multiple choice quiz on the topic: {topic}.
Each question must include:
- "question"
- "correctAnswer"
- "wrongAnswers": 3 incorrect but believable options

Respond only in JSON array format, no extra explanation.
"""

async def generate_quiz_with_gpt(topic: str):
    prompt = STARTER_PROMPT.format(topic=topic)

    # Run the sync .create call in a thread to avoid blocking
    response = await asyncio.to_thread(
        openai.chat.completions.create,
        model="gpt-4-0613",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=800,
    )

    content = response.choices[0].message.content.strip()
    try:
        return json.loads(content)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON from GPT: {e}\n{content}")

