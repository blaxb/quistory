# main.py
import re
import traceback
from uuid import uuid4
from typing import List

import httpx
from fastapi import FastAPI
from pydantic import BaseModel

from fallback_gpt import generate_quiz_with_gpt

app = FastAPI(title="Guess.ai Quiz API")
quizzes: dict[str, List[str]] = {}

# ─── Pydantic schema ───────────────────────────────────
class ListQuiz(BaseModel):
    session_id: str
    quiz_type: str  # always "list"
    items: List[str]

class QuizRequest(BaseModel):
    topic: str

# ─── Helpers ───────────────────────────────────────────
def normalize(text: str) -> str:
    return re.sub(r"[^0-9a-z]", "", text.strip().lower())

async def safe_verify(items: List[str]) -> List[str]:
    verified = []
    async with httpx.AsyncClient(timeout=5) as client:
        for item in items:
            slug = item.replace(" ", "_")
            try:
                r = await client.get(
                    f"https://en.wikipedia.org/api/rest_v1/page/summary/{slug}"
                )
                if r.status_code == 200:
                    verified.append(item)
            except Exception:
                # just skip on error
                pass
    return verified

# ─── Health check ──────────────────────────────────────
@app.get("/healthz")
def healthz():
    return {"status": "ok"}

# ─── Generate quiz (always ListQuiz) ───────────────────
@app.post("/generate-quiz", response_model=ListQuiz)
async def generate_quiz(payload: QuizRequest):
    topic = payload.topic.strip()
    session_id = str(uuid4())
    items: List[str] = []

    # 1) Detect "top N ..." to tailor the GPT prompt
    m = re.match(r"top\s+(\d+)\s+(.*)", topic, re.IGNORECASE)
    if m:
        count = int(m.group(1))
        base = m.group(2)
        prompt = (
            f"Give me exactly {count} distinct items for: {base}. "
            "Return ONLY a JSON array of strings."
        )
    else:
        prompt = topic

    # 2) Call GPT safely
    try:
        raw = await generate_quiz_with_gpt(prompt)
        if isinstance(raw, list) and all(isinstance(i, str) for i in raw):
            items = raw
        else:
            # unexpected format: ignore
            items = []
    except Exception as e:
        print(f"[generate_quiz] GPT error:", e)
        items = []

    # 3) Verify with Wikipedia
    try:
        verified = await safe_verify(items)
        if verified:
            items = verified
    except Exception as e:
        print(f"[generate_quiz] verification error:", e)

    # 4) Store & return
    quizzes[session_id] = items
    return ListQuiz(session_id=session_id, quiz_type="list", items=items)

