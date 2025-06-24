# main.py
import traceback
import re
from uuid import uuid4
from typing import List, Literal, Union, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from rapidfuzz import fuzz

from fallback_gpt import generate_quiz_with_gpt  # your existing GPT wrapper

app = FastAPI(title="Guess.ai Quiz API")

# In‐memory store for quizzes
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
    """Lowercase & strip non-alphanumeric."""
    return re.sub(r"[^0-9a-z]", "", text.strip().lower())

# ─── Health check ──────────────────────────────────────
@app.get("/healthz")
def healthz():
    return {"status": "ok"}

# ─── Generate quiz + stash answers ─────────────────────
@app.post("/generate-quiz", response_model=QuizResponse)
async def generate_quiz(payload: QuizRequest):
    try:
        raw = await generate_quiz_with_gpt(payload.topic.strip())
        session_id = str(uuid4())

        # list-style quiz
        if all(isinstance(i, str) for i in raw):
            quizzes[session_id] = raw
            return ListQuiz(session_id=session_id, quiz_type="list", items=raw)

        # MCQ style
        mcqs = [MCQQuestion(**q) for q in raw]
        quizzes[session_id] = [q.correctAnswer for q in mcqs]
        return MCQQuiz(session_id=session_id, quiz_type="mcq", quiz=mcqs)

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

# ─── Check a guess against stored answers ───────────────
@app.post("/check-guess", response_model=CheckGuessOut)
def check_guess(data: CheckGuessIn):
    answers = quizzes.get(data.session_id, [])
    norm_guess = normalize(data.guess)

    for ans in answers:
        norm_ans = normalize(ans)

        # 1) exact full-string match
        if norm_guess == norm_ans:
            return CheckGuessOut(correct=True, matched_answer=ans)

        # 2) exact last-name match (for multi-word answers)
        last_token = normalize(ans.split()[-1])
        if norm_guess == last_token and len(norm_guess) >= 3:
            return CheckGuessOut(correct=True, matched_answer=ans)

        # 3) fuzzy full-string match at 80% threshold
        if fuzz.ratio(norm_guess, norm_ans) >= 80:
            return CheckGuessOut(correct=True, matched_answer=ans)

    return CheckGuessOut(correct=False)

