# main.py

import uvicorn
from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from pydantic import BaseModel
from typing import List

from database import get_db, engine, Base
from models import QuizTopic
from quiz_logic import build_quiz_from_facts
from fallback_gpt import generate_quiz_with_gpt

# Pydantic schemas
class QuizQuestion(BaseModel):
    question: str
    correctAnswer: str
    wrongAnswers: List[str]

class QuizRequest(BaseModel):
    topic: str

class QuizResponse(BaseModel):
    quiz: List[QuizQuestion]

app = FastAPI(title="Guess.ai Quiz API")

@app.on_event("startup")
async def on_startup():
    # Create tables if they don't exist
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

@app.post("/generate-quiz", response_model=QuizResponse)
async def generate_quiz(
    payload: QuizRequest,
    db: AsyncSession = Depends(get_db)
):
    topic = payload.topic.strip().lower()

    # Check for existing topic in DB
    stmt = select(QuizTopic).where(QuizTopic.topic_name == topic)
    result = await db.execute(stmt)
    topic_obj = result.scalars().first()

    if topic_obj:
        # Build from verified data
        quiz_models = build_quiz_from_facts(topic_obj.facts)
    else:
        # Fallback to GPT
        try:
            raw_quiz = await generate_quiz_with_gpt(topic)
            quiz_models = build_quiz_from_facts(raw_quiz)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"GPT fallback error: {e}")

    # Convert Pydantic models to plain dicts for response validation
    quiz_dicts = [q.model_dump() for q in quiz_models]
    return QuizResponse(quiz=quiz_dicts)

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)

