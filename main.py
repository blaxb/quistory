import traceback
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Literal, Union, Any

from fallback_gpt import generate_quiz_with_gpt

# ─── Schemas ───────────────────────────────────────────
class MCQQuestion(BaseModel):
    question: str
    correctAnswer: str
    wrongAnswers: List[str]

class ListQuiz(BaseModel):
    quiz_type: Literal["list"]
    items: List[str]

class MCQQuiz(BaseModel):
    quiz_type: Literal["mcq"]
    quiz: List[MCQQuestion]

QuizResponse = Union[ListQuiz, MCQQuiz]

class QuizRequest(BaseModel):
    topic: str

# ─── App init ───────────────────────────────────────────
app = FastAPI(title="Guess.ai Quiz API")

@app.get("/healthz")
def healthz():
    return {"status": "ok"}

@app.post("/generate-quiz", response_model=QuizResponse)
async def generate_quiz(payload: QuizRequest):
    topic = payload.topic.strip()
    try:
        raw = await generate_quiz_with_gpt(topic)

        # If we got back a simple list of strings:
        if all(isinstance(i, str) for i in raw):
            return ListQuiz(quiz_type="list", items=raw)

        # Otherwise assume it's MCQ‐compatible dicts:
        mcqs = [MCQQuestion(**q) for q in raw]  # q must have question/correctAnswer/wrongAnswers
        return MCQQuiz(quiz_type="mcq", quiz=mcqs)

    except Exception as e:
        traceback.print_exc()
        # return the error message so you can see it in your client
        raise HTTPException(status_code=500, detail=str(e))

