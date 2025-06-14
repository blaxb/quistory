import os
import uvicorn
import traceback
import os; print("OPENAI_API_KEY =", os.getenv("OPENAI_API_KEY"))

# ────────────────────────────────────────────────────────────────────────────
# Patch HTTPX so its header encoder will drop non-ASCII rather than error
# ────────────────────────────────────────────────────────────────────────────
import httpx._models

_orig_normalize = httpx._models._normalize_header_value
def _patched_normalize_header_value(value, encoding):
    # If the header value is a string, drop any non-ASCII chars.
    if isinstance(value, str):
        return value.encode(encoding or "ascii", errors="ignore")
    # Otherwise fall back to HTTPX’s default logic
    return _orig_normalize(value, encoding)

httpx._models._normalize_header_value = _patched_normalize_header_value

# ────────────────────────────────────────────────────────────────────────────
# Standard imports
# ────────────────────────────────────────────────────────────────────────────
from fastapi import FastAPI, HTTPException, Header, Depends
from pydantic import BaseModel
from typing import List, Literal, Union, Any

from fallback_gpt import generate_quiz_with_gpt

# ────────────────────────────────────────────────────────────────────────────
# Response Schemas
# ────────────────────────────────────────────────────────────────────────────
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

# ────────────────────────────────────────────────────────────────────────────
# Admin schema (stubbed)
# ────────────────────────────────────────────────────────────────────────────
class AdminTopic(BaseModel):
    topic_name: str
    facts: List[Any]

# ────────────────────────────────────────────────────────────────────────────
# App Initialization
# ────────────────────────────────────────────────────────────────────────────
app = FastAPI(title="Guess.ai Quiz API", debug=True)

ADMIN_KEY = os.getenv("ADMIN_API_KEY")
def require_admin(x_api_key: str = Header(..., alias="X-API-KEY")):
    if x_api_key != ADMIN_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")

@app.get("/")
async def root():
    return {
        "status": "ok",
        "message": "Guess.ai Quiz API is running. POST your JSON to /generate-quiz"
    }

# ────────────────────────────────────────────────────────────────────────────
# Public endpoint — GPT First
# ────────────────────────────────────────────────────────────────────────────
@app.post("/generate-quiz", response_model=QuizResponse)
async def generate_quiz(payload: QuizRequest):
    topic = payload.topic.strip()
    try:
        raw = await generate_quiz_with_gpt(topic)
        # if it’s just a list of strings:
        if all(isinstance(i, str) for i in raw):
            return ListQuiz(quiz_type="list", items=raw)
        # otherwise assume MCQQuestion-compatible dicts/models
        return MCQQuiz(quiz_type="mcq", quiz=[q.model_dump() for q in raw])
    except Exception as e:
        # full traceback in your logs
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"GPT error: {e}")

# ────────────────────────────────────────────────────────────────────────────
# Admin stubs (no DB backing)
# ────────────────────────────────────────────────────────────────────────────
@app.post("/admin/topics", dependencies=[Depends(require_admin)])
async def create_topic(payload: AdminTopic):
    # stubbed: you can extend this to save to a DB if you like
    return {"status": "created", "topic": payload.topic_name}

@app.get("/admin/topics", dependencies=[Depends(require_admin)])
async def list_topics():
    return []

# ────────────────────────────────────────────────────────────────────────────
# Run the server
# ────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)

