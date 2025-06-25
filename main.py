# main.py
import os
import re
import traceback
from uuid import uuid4
from typing import List, Literal, Union, Optional

import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from rapidfuzz import fuzz

from fallback_gpt import generate_quiz_with_gpt

app = FastAPI(title="Guess.ai Quiz API")
quizzes: dict[str, List[str]] = {}

# ─── Schemas ───────────────────────────────────────────
class ListQuiz(BaseModel):
    session_id: str
    quiz_type: Literal["list"]
    items: List[str]

class MCQQuestion(BaseModel):
    question: str
    correctAnswer: str
    wrongAnswers: List[str]

class MCQQuiz(BaseModel):
    session_id: str
    quiz_type: Literal["mcq"]
    quiz: List[MCQQuestion]

QuizResponse = Union[ListQuiz, MCQQuiz]

class QuizRequest(BaseModel):
    topic: str

class CheckGuessIn(BaseModel):
    session_id: str
    guess: str

class CheckGuessOut(BaseModel):
    correct: bool
    matched_answer: Optional[str] = None

# ─── Normalize & Verify Helpers ────────────────────────
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
            except Exception as e:
                print(f"[verify] error for {item}: {e}")
    return verified

# ─── Health check ──────────────────────────────────────
@app.get("/healthz")
def healthz():
    return {"status": "ok"}

# ─── Generate quiz + stash answers ─────────────────────
@app.post("/generate-quiz", response_model=QuizResponse)
async def generate_quiz(payload: QuizRequest):
    topic_in = payload.topic.strip()
    session_id = str(uuid4())

    # 1) detect "top N ..." pattern
    m = re.match(r"top\s+(\d+)\s+(.*)", topic_in, re.IGNORECASE)
    if m:
        count, base = int(m.group(1)), m.group(2)
        prompt = (
            f"Give me exactly {count} distinct items for: {base}. "
            "Return a JSON array of strings only."
        )
    else:
        count, base, prompt = None, topic_in, topic_in

    # 2) call GPT safely
    try:
        raw = await generate_quiz_with_gpt(prompt)
        if not isinstance(raw, list) or not all(isinstance(i, str) for i in raw):
            raise ValueError("GPT did not return a list of strings")
        items = raw
    except Exception as e:
        print(f"[generate_quiz] GPT error: {e}")
        items = []

    # 3) warn if we asked for N but got wrong count
    if count and len(items) != count:
        print(f"[generate_quiz] warning: got {len(items)}/{count} for '{topic_in}'")

    # 4) verify via Wiki

