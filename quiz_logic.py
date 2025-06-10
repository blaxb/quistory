# quiz_logic.py

import random
from typing import List, Dict
from pydantic import BaseModel

class QuizQuestion(BaseModel):
    question: str
    correctAnswer: str
    wrongAnswers: List[str]

def build_quiz_from_facts(facts: List[Dict]) -> List[QuizQuestion]:
    """
    Given a list of dicts like:
      {
        "question": "...",
        "correctAnswer": "...",
        "wrongAnswers": ["...", "...", "..."]
      }
    returns a shuffled list of QuizQuestion models.
    """
    quiz: List[QuizQuestion] = []
    for fact in facts:
        quiz.append(QuizQuestion(
            question=fact["question"],
            correctAnswer=fact["correctAnswer"],
            wrongAnswers=fact["wrongAnswers"]
        ))
    random.shuffle(quiz)
    return quiz

