import os
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

# -----------------------
# Pydantic request/response schemas
# -----------------------
class QuizQuestion(BaseModel):
    question: str
    correctAnswer: str
    wrongAnswers: List[str]

class QuizRequest(BaseModel):
    topic: str

class QuizResponse(BaseModel):
    quiz: List[QuizQuestion]

# -----------------------
# FastAPI app
# -----------------------
app = FastAPI(title="Guess.ai Quiz API")

@app.on_event("startup")
async def on_startup():
    # Ensure all tables exist
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

@app.post("/generate-quiz", response_model=QuizResponse)
async def generate_quiz(
    payload: QuizRequest,
    db: AsyncSession = Depends(get_db)
):
    topic = payload.topic.strip().lower()

    # 1. Try to fetch from the database
    stmt = select(QuizTopic).where(QuizTopic.topic_name == topic)
    result = await db.execute(stmt)
    topic_obj = result.scalars().first()

    if topic_obj:
        # Use your verified facts
        quiz_models = build_quiz_from_facts(topic_obj.facts)
    else:
        # Fallback to GPT, but catch any errors and return a safe message
        try:
            raw_quiz = await generate_quiz_with_gpt(topic)
            quiz_models = build_quiz_from_facts(raw_quiz)
        except Exception:
            # Return a simple ASCII-safe error
            raise HTTPException(status_code=500, detail="GPT fallback error")

    # Convert Pydantic model instances to plain dicts
    quiz_dicts = [q.model_dump() for q in quiz_models]
    return QuizResponse(quiz=quiz_dicts)

# -----------------------
# Run the app
# -----------------------
if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)

