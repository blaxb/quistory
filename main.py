import os
import uvicorn
import traceback
import httpx
from fastapi import FastAPI, HTTPException, Depends, Header
from pydantic import BaseModel
from typing import List, Literal, Union, Any

from fallback_gpt import generate_quiz_with_gpt

# -----------------------
# Schemas for response
# -----------------------
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

# -----------------------
# Admin schema
# -----------------------
class AdminTopic(BaseModel):
    topic_name: str
    facts: List[Any]

# -----------------------
# App init
# -----------------------
app = FastAPI(title="Guess.ai Quiz API", debug=True)

ADMIN_KEY = os.getenv("ADMIN_API_KEY")

def require_admin(x_api_key: str = Header(..., alias="X-API-KEY")):
    if x_api_key != ADMIN_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")

# Force httpx/OpenAI to use ASCII-only headers
httpx._models.DEFAULT_HEADERS["user-agent"] = "openai-python/1.0"

# -----------------------
# Public endpoint
# -----------------------
@app.post("/generate-quiz", response_model=QuizResponse)
async def generate_quiz(payload: QuizRequest):
    topic = payload.topic.strip()
    try:
        raw = await generate_quiz_with_gpt(topic)
        # simple list of strings?
        if all(isinstance(i, str) for i in raw):
            return ListQuiz(quiz_type="list", items=raw)
        # otherwise MCQ objects
        mcq_items = [q.model_dump() for q in raw]  # assume fallback returns dicts compatible
        return MCQQuiz(quiz_type="mcq", quiz=mcq_items)
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"GPT error: {e}")

# -----------------------
# Admin endpoints
# -----------------------
@app.post("/admin/topics", dependencies=[Depends(require_admin)])
async def create_topic(payload: AdminTopic):
    # Here you could still store admin topics in your DB if desired
    # For now we'll just pretend it's a no-op
    return {"status": "created", "topic": payload.topic_name}

@app.get("/admin/topics", dependencies=[Depends(require_admin)])
async def list_topics():
    # No real storage in this version
    return []

# -----------------------
# Run the app
# -----------------------
if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)

