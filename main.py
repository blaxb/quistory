import os
import uvicorn
from fastapi import FastAPI, HTTPException, Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from pydantic import BaseModel
from typing import List, Literal, Union, Any

from database import get_db, engine, Base, SessionLocal
from models import QuizTopic
from quiz_logic import build_quiz_from_facts
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
# Admin schema: facts can be anything
# -----------------------
class AdminTopic(BaseModel):
    topic_name: str
    facts: List[Any]    # accept list of strings or dicts

# -----------------------
# App init
# -----------------------
app = FastAPI(title="Guess.ai Quiz API")

ADMIN_KEY = os.getenv("ADMIN_API_KEY")

def require_admin(x_api_key: str = Header(..., alias="X-API-KEY")):
    if x_api_key != ADMIN_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")

@app.on_event("startup")
async def on_startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# -----------------------
# Public endpoint
# -----------------------
@app.post("/generate-quiz", response_model=QuizResponse)
async def generate_quiz(
    payload: QuizRequest,
    db: AsyncSession = Depends(get_db)
):
    topic = payload.topic.strip().lower()
    stmt = select(QuizTopic).where(QuizTopic.topic_name == topic)
    result = await db.execute(stmt)
    topic_obj = result.scalars().first()

    if topic_obj:
        # list‐type if all facts are strings
        if all(isinstance(i, str) for i in topic_obj.facts):
            return ListQuiz(quiz_type="list", items=topic_obj.facts)
        mcq = build_quiz_from_facts(topic_obj.facts)
        return MCQQuiz(quiz_type="mcq", quiz=[q.model_dump() for q in mcq])

    # GPT fallback
    try:
        raw = await generate_quiz_with_gpt(topic)
        if all(isinstance(i, str) for i in raw):
            return ListQuiz(quiz_type="list", items=raw)
        mcq = build_quiz_from_facts(raw)
        return MCQQuiz(quiz_type="mcq", quiz=[q.model_dump() for q in mcq])
    except Exception:
        raise HTTPException(status_code=500, detail="GPT fallback error")

# -----------------------
# Admin endpoints
# -----------------------
@app.post("/admin/topics", dependencies=[Depends(require_admin)])
async def create_topic(payload: AdminTopic):
    async with SessionLocal() as db:
        res = await db.execute(select(QuizTopic).where(QuizTopic.topic_name == payload.topic_name))
        if res.scalars().first():
            raise HTTPException(status_code=400, detail="Topic already exists")
        # Store whatever facts were sent
        new = QuizTopic(topic_name=payload.topic_name, facts=payload.facts)
        db.add(new)
        await db.commit()
    return {"status": "created", "topic": payload.topic_name}

@app.get("/admin/topics", dependencies=[Depends(require_admin)])
async def list_topics():
    async with SessionLocal() as db:
        res = await db.execute(select(QuizTopic))
        topics = res.scalars().all()
    return [{"topic_name": t.topic_name, "facts": t.facts} for t in topics]

@app.put("/admin/topics/{topic_name}", dependencies=[Depends(require_admin)])
async def update_topic(topic_name: str, payload: AdminTopic):
    async with SessionLocal() as db:
        res = await db.execute(select(QuizTopic).where(QuizTopic.topic_name == topic_name))
        obj = res.scalars().first()
        if not obj:
            raise HTTPException(status_code=404, detail="Topic not found")
        obj.facts = payload.facts
        await db.commit()
    return {"status": "updated", "topic": topic_name}

# -----------------------
# Run the app
# -----------------------
if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)

