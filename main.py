k# main.py
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

async def verify_with_wikipedia(items: List[str]) -> List[str]:
    """
    Verify each item by:
      1) Trying exact summary slug.
      2) If that fails, searching for the item and using the top hit.
      3) Only keep if we ultimately get a 200 summary.
    """
    verified: List[str] = []
    async with httpx.AsyncClient(timeout=5) as client:
        for item in items:
            slug = item.replace(" ", "_")
            got = False

            # 1) exact slug lookup
            try:
                res = await client.get(
                    f"https://en.wikipedia.org/api/rest_v1/page/summary/{slug}"
                )
                if res.status_code == 200:
                    verified.append(item)
                    got = True
                else:
                    # fallthrough to search
                    pass
            except Exception as e:
                print(f"[verify] exact lookup error for '{item}': {e}")

            if got:
                continue

            # 2) search fallback
            try:
                search_params = {
                    "action": "query",
                    "list": "search",
                    "srsearch": item,
                    "format": "json",
                    "utf8": 1,
                }
                sres = await client.get(
                    "https://en.wikipedia.org/w/api.php",
                    params=search_params,
                )
                if sres.status_code == 200:
                    data = sres.json()
                    hits = data.get("query", {}).get("search", [])
                    if hits:
                        # take the first hit's title
                        title = hits[0]["title"].replace(" ", "_")
                        # fetch its summary
                        pres = await client.get(
                            f"https://en.wikipedia.org/api/rest_v1/page/summary/{title}"
                        )
                        if pres.status_code == 200:
                            verified.append(item)
                            got = True
            except Exception as e:
                print(f"[verify] search lookup error for '{item}': {e}")

            # if still not got, item is dropped
        return verified

# ─── Endpoints ─────────────────────────────────────────
@app.get("/healthz")
def healthz():
    return {"status": "ok"}

@app.post("/generate-quiz", response_model=ListQuiz)
async def generate_quiz(payload: QuizRequest):
    topic_in = payload.topic.strip()
    session_id = str(uuid4())

    # Detect "top N ..." for exact-count GPT prompt
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
                raise ValueError("GPT did not return a list of strings")
        except Exception as e:
            print(f"[generate_quiz] GPT error: {e}")
            items = []
    else:
        # Fallback to generic GPT
        count = None
        base = topic_in
        try:
            raw = await generate_quiz_with_gpt(base)
            if isinstance(raw, list) and all(isinstance(i, str) for i in raw):
                items = raw
            else:
                raise ValueError("GPT did not return a list of strings")
        except Exception as e:
            print(f"[generate_quiz] GPT error: {e}")
            items = []

    # Warn if exact count mismatch
    if count is not None and len(items) != count:
        print(f"[generate_quiz] warning: got {len(items)}/{count} for '{topic_in}'")

    # Verify with search‐based Wikipedia lookup
    try:
        verified = await verify_with_wikipedia(items)
        if verified:
            items = verified
    except Exception as e:
        print(f"[generate_quiz] verification error: {e}")

    # Always return ListQuiz
    quizzes[session_id] = items
    return ListQuiz(session_id=session_id, quiz_type="list", items=items)

@app.post("/check-guess", response_model=CheckGuessOut)
def check_guess(data: CheckGuessIn):
    answers = quizzes.get(data.session_id, [])
    guess = normalize(data.guess)
    for ans in answers:
        na = normalize(ans)
        if guess == na or fuzz.ratio(guess, na) >= 80:
            return CheckGuessOut(correct=True, matched_answer=ans)
    return CheckGuessOut(correct=False)

