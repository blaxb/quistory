import os
import uvicorn
import traceback

# Debug dump to verify env
print("⎯⎯⎯    ENV START ⎯⎯⎯")
for k, v in os.environ.items():
    print(f"{k}={v}")
print("⎯⎯⎯    ENV END   ⎯⎯⎯")

# Patch HTTPX header normalization
import httpx._models
_orig = httpx._models._normalize_header_value
def _patched(v, encoding):
    if isinstance(v, str):
        return v.encode(encoding or "ascii", errors="ignore")
    return _orig(v, encoding)
httpx._models._normalize_header_value = _patched

from fastapi import FastAPI, HTTPException, Header, Depends
from pydantic import BaseModel
from typing import List, Literal, Union, Any
from fallback_gpt import generate_quiz_with_gpt

# ── Schemas ──────────────────────────────────────────
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

class AdminTopic(BaseModel):
    topic_name: str
    facts: List[Any]

# ── App init ─────────────────────────────────────────
app = FastAPI(title="Guess.ai Quiz API", debug=True)

ADMIN_KEY = os.getenv("ADMIN_API_KEY")
def require_admin(x_api_key: str = Header(..., alias="X-API-KEY")):
    if x_api_key != ADMIN_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")

# ── Health check ─────────────────────────────────────
@app.api_route("/", methods=["GET", "HEAD"])
async def root():
    return {
        "status": "ok",
        "message": "Guess.ai Quiz API is running. POST your JSON to /generate-quiz"
    }

# ── Public endpoint ───────────────────────────────────
@app.post("/generate-quiz", response_model=QuizResponse)
async def generate_quiz(payload: QuizRequest):
    topic = payload.topic.strip()
    try:
        raw = await generate_quiz_with_gpt(topic)
        if all(isinstance(i, str) for i in raw):
            return ListQuiz(quiz_type="list", items=raw)
        return MCQQuiz(quiz_type="mcq", quiz=[q.model_dump() for q in raw])
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"GPT error: {e}")

# ── Admin endpoints ───────────────────────────────────
@app.post("/admin/topics", dependencies=[Depends(require_admin)])
async def create_topic(payload: AdminTopic):
    return {"status": "created", "topic": payload.topic_name}

@app.get("/admin/topics", dependencies=[Depends(require_admin)])
async def list_topics():
    return []

# ── Run server ────────────────────────────────────────
if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)

