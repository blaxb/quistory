import traceback
import re
from uuid import uuid4
from typing import List, Literal, Union, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from rapidfuzz import fuzz

from fallback_gpt import generate_quiz_with_gpt

app = FastAPI(title="Guess.ai Quiz API")

# In‐memory store of answers per session
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
    # strip spaces/punctuation, lowercase
    return re.sub(r"[^0-9a-z]", "", text.strip().lower())

# ─── Health check ──────────────────────────────────────
@app.get("/healthz")
def healthz():
    return {"status": "ok"}

# ─── Generate quiz ─────────────────────────────────────
@app.post("/generate-quiz", response_model=QuizResponse)
async def generate_quiz(payload: QuizRequest):
    try:
        raw = await generate_quiz_with_gpt(payload.topic.strip())
        session_id = str(uuid4())

        # If it's a simple list of strings:
        if all(isinstance(i, str) for i in raw):
            quizzes[session_id] = raw
            return ListQuiz(session_id=session_id, quiz_type="list", items=raw)

        # Otherwise assume MCQ dicts:
        mcqs = [MCQQuestion(**q) for q in raw]
        quizzes[session_id] = [q.correctAnswer for q in mcqs]
        return MCQQuiz(session_id=session_id, quiz_type="mcq", quiz=mcqs)

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

# ─── Check a guess ─────────────────────────────────────
@app.post("/check-guess", response_model=CheckGuessOut)
def check_guess(data: CheckGuessIn):
    answers = quizzes.get(data.session_id, [])
    guess = normalize(data.guess)

    for ans in answers:
        na = normalize(ans)

        # 1) Exact match
        if guess == na:
            return CheckGuessOut(correct=True, matched_answer=ans)

        # 2) Whole-word match (e.g. last name or acronym) if guess length >= 2
        #    Note: since normalize removes spaces, split on original ans
        words = [normalize(w) for w in ans.split()]
        if len(guess) >= 2 and guess in words:
            return CheckGuessOut(correct=True, matched_answer=ans)

        # 3) Fuzzy match only for longer strings (both guess and answer >= 4 chars)
        #    with a strict 90% threshold
        if len(guess) >= 4 and len(na) >= 4 and fuzz.ratio(guess, na) >= 90:
            return CheckGuessOut(correct=True, matched_answer=ans)

    return CheckGuessOut(correct=False)

