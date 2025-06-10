# fallback_gpt.py

import os
import json
import openai
from dotenv import load_dotenv

# Load .env so OPENAI_API_KEY is available
load_dotenv()

# Configure OpenAI
openai.api_key = os.getenv("OPENAI_API_KEY")

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
    """
    Calls OpenAI’s ChatCompletion to generate a quiz.
    Returns a list of dicts like:
    [
      {
        "question": "...",
        "correctAnswer": "...",
        "wrongAnswers": ["...", "...", "..."]
      },
      ...
    ]
    """
    prompt = STARTER_PROMPT.format(topic=topic)
    response = await openai.ChatCompletion.acreate(
        model="gpt-4-0613",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=800,
    )
    content = response.choices[0].message.content.strip()
    try:
        quiz = json.loads(content)
    except json.JSONDecodeError as e:
        raise ValueError(f"GPT returned invalid JSON: {e}\nContent was:\n{content}")
    return quiz

