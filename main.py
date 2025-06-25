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
class MCQQuestion(BaseModel):
    question: str
    correctAnswer: str
    wrongAnswers: List[str]

class ListQuiz(BaseModel):
    session_id: str
    quiz_type: Literal["list"]
    items: List[str]

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

# ─── Helpers ────────────────────────────────────────────
def normalize(text: str) -> str:
    return re.sub(r"[^0-9a-z]", "", text.strip().lower())

async def fetch_wikipedia_list(topic: str) -> List[str]:
    """
    Scrape the first useful <ul> from 'List of {topic}' on Wikipedia.
    """
    title = f"List of {topic}"
    params = {
        "action": "parse",
        "page": title,
        "prop": "text",
        "format": "json",
        "redirects": True,
    }
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get("https://en.wikipedia.org/w/api.php", params=params)
        r.raise_for_status()
        data = r.json()
        html = data.get("parse", {}).get("text", {}).get("*", "")
    except Exception:
        return []

    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html, "html.parser")
    for ul in soup.find_all("ul"):
        items = [li.get_text().strip() for li in ul.find_all("li", recursive=False)]
        if len(items) >= 5:
            return items
    return []

async def verify_with_wikipedia(items: List[str]) -> List[str]:
    """
    Only keep items that actually have a Wikipedia summary page.
    """
    verified = []
    async with httpx.AsyncClient(timeout=5) as client:
        for item in items:
            slug = item.replace(" ", "_")
            try:
                resp = await client.get(
                    f"https://en.wikipedia.org/api/rest_v1/page/summary/{slug}"
                )
                if resp.status_code == 200:
                    verified.append(item)
            except Exception:
                continue
    return verified

# ─── Health check ──────────────────────────────────────
@app.get("/healthz")
def healthz():
    return {"status": "ok"}

# ─── Generate quiz ─────────────────────────────────────
@app.post("/generate-quiz", response_model=QuizResponse)
async def generate_quiz(payload: QuizRequest):
    topic_in = payload.topic.strip()
    session_id = str(uuid4())

    # 1) Detect "top N ..." for exact-count GPT prompt
    m = re.match(r"top\s+(\d+)\s+(.*)", topic_in, re.IGNORECASE)
    if m:
        count = int(m.group(1))
        base = m.group(2)
        prompt = (
            f"Give me exactly {count} distinct items for: {base}. "
            "Return ONLY a JSON array of strings."
        )
        try:
            raw = await generate_quiz_with_gpt(prompt)
            if isinstance(raw, list) and all(isinstance(i, str) for i in raw):
                items = raw
            else:
                raise ValueError("GPT format error")
        except Exception as e:
            print(f"[generate_quiz] GPT error: {e}")
            items = []
    else:
        # 2) Try Wikipedia list scrape
        count = None
        base = topic_in
        items = await fetch_wikipedia_list(base)

        # 3) If Wikipedia failed, fallback to GPT
        if not items:
            try:
                raw = await generate_quiz_with_gpt(base)
                if isinstance(raw, list) and all(isinstance(i, str) for i in raw):
                    items = raw
                else:
                    raise ValueError("GPT format error")
            except Exception as e:
                print(f"[generate_quiz] GPT error: {e}")
                items = []

    # 4) If we asked for a count, warn on mismatch
    if count is not None and len(items) != count:
        print(f"[generate_quiz] warning: got {len(items)}/{count} for '{topic_in}'")

    # 5) Verify via Wikipedia to drop hallucinations
    try:
        verified = await verify_with_wikipedia(items)
        if verified:
            items = verified
    except Exception as e:
        print(f"[generate_quiz] verification error: {e}")

    # 6) Store & always return a ListQuiz for simple lists
    quizzes[session_id] = items
    return ListQuiz(session_id=session_id, quiz_type="list", items=items)

# ─── Check a guess ─────────────────────────────────────
@app.post("/check-guess", response_model=CheckGuessOut)
def check_guess(data: CheckGuessIn):
    answers = quizzes.get(data.session_id, [])
    guess = normalize(data.guess)
    for ans in answers:
        na = normalize(ans)
        if guess == na or fuzz.ratio(guess, na) >= 80:
            return CheckGuessOut(correct=True, matched_answer=ans)
    return CheckGuessOut(correct=False)

