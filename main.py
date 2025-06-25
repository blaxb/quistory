# main.py
import os
import re
import json
import traceback
from uuid import uuid4
from typing import List, Literal, Union, Optional

import openai
import httpx
from bs4 import BeautifulSoup
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from rapidfuzz import fuzz

from fallback_gpt import generate_quiz_with_gpt  # your existing wrapper
from dotenv import load_dotenv

# ─── Load env ──────────────────────────────────────────
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")
if not openai.api_key:
    raise RuntimeError("Set OPENAI_API_KEY in your env or .env file")

app = FastAPI(title="Guess.ai Quiz API")
quizzes: dict[str, List[str]] = {}  # session_id → answers list

# ─── Pydantic Schemas ──────────────────────────────────
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

# ─── Helpers ───────────────────────────────────────────
def normalize(text: str) -> str:
    return re.sub(r"[^0-9a-z]", "", text.strip().lower())

async def fetch_wikipedia_list(topic: str) -> List[str]:
    """
    Scrape the first <ul> from the 'List of {topic}' wiki page.
    """
    title = f"List of {topic}"
    params = {
        "action": "parse",
        "page": title,
        "prop": "text",
        "format": "json",
        "redirects": True,
    }
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get("https://en.wikipedia.org/w/api.php", params=params)
    if r.status_code != 200:
        return []
    data = r.json()
    html = data.get("parse", {}).get("text", {}).get("*", "")
    if not html:
        return []
    soup = BeautifulSoup(html, "html.parser")
    # find the first top-level <ul> and extract its <li> texts
    for ul in soup.find_all("ul"):
        items = [li.get_text().strip() for li in ul.find_all("li", recursive=False)]
        if len(items) > 1:
            return items
    return []

async def verify_with_wikipedia(items: List[str]) -> List[str]:
    """
    Only keep items that have a valid Wikipedia summary.
    """
    verified: List[str] = []
    async with httpx.AsyncClient(timeout=5) as client:
        for item in items:
            slug = item.replace(" ", "_")
            url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{slug}"
            r = await client.get(url)
            if r.status_code == 200:
                verified.append(item)
    return verified

# ─── Health check ──────────────────────────────────────
@app.get("/healthz")
def healthz():
    return {"status": "ok"}

# ─── Generate quiz ─────────────────────────────────────
@app.post("/generate-quiz", response_model=QuizResponse)
async def generate_quiz(payload: QuizRequest):
    topic = payload.topic.strip()
    # 1) Try Wikipedia
    try:
        wiki_items = await fetch_wikipedia_list(topic)
    except Exception:
        wiki_items = []
    # if Wikipedia gave us at least 5 items, trust it
    if len(wiki_items) >= 5:
        items = wiki_items
    else:
        # 2) Fallback to GPT
        raw = await generate_quiz_with_gpt(topic)
        # expect List[str] or MCQ dicts
        if all(isinstance(i, str) for i in raw):
            # verify each GPT item via Wikipedia
            verified = await verify_with_wikipedia(raw)
            items = verified or raw
        else:
            # MCQ: you can apply similar verification on correctAnswer if desired
            items = raw

    session_id = str(uuid4())
    # stash strings, or correctAnswer fields
    if all(isinstance(i, str) for i in items):
        quizzes[session_id] = items
        return ListQuiz(session_id=session_id, quiz_type="list", items=items)
    else:
        mcqs = [MCQQuestion(**q) for q in items]  # type: ignore
        quizzes[session_id] = [q.correctAnswer for q in mcqs]
        return MCQQuiz(session_id=session_id, quiz_type="mcq", quiz=mcqs)

# ─── Check a guess ─────────────────────────────────────
@app.post("/check-guess", response_model=CheckGuessOut)
def check_guess(data: CheckGuessIn):
    answers = quizzes.get(data.session_id, [])
    norm = normalize(data.guess)
    for ans in answers:
        na = normalize(ans)
        if norm == na or fuzz.ratio(norm, na) >= 80:
            return CheckGuessOut(correct=True, matched_answer=ans)
    return CheckGuessOut(correct=False)

