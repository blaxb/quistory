import asyncio
from sqlalchemy.future import select
from database import SessionLocal
from models import QuizTopic

async def seed():
    async with SessionLocal() as session:
        topic_name = "florida state softball coaches"
        # Check if already exists
        res = await session.execute(select(QuizTopic).where(QuizTopic.topic_name == topic_name))
        if res.scalars().first():
            print("Topic already seeded.")
            return

        facts = [
            {
                "question": "Who coached FSU to their first softball national title in 2018?",
                "correctAnswer": "Lonni Alameda",
                "wrongAnswers": ["Patty Gasso", "Sue Enquist", "Karen Weekly"]
            },
            {
                "question": "Which conference does FSU softball play in?",
                "correctAnswer": "ACC",
                "wrongAnswers": ["SEC", "Big Ten", "Big 12"]
            },
            {
                "question": "What is the home stadium of FSU softball?",
                "correctAnswer": "Seminole Softball Stadium",
                "wrongAnswers": ["Doak Campbell Stadium", "Mike Martin Field", "Alumni Field"]
            },
            {
                "question": "In what year did FSU softball make its first Women’s College World Series appearance?",
                "correctAnswer": "2011",
                "wrongAnswers": ["2005", "2015", "2008"]
            },
            {
                "question": "Who is the current athletic director overseeing FSU softball?",
                "correctAnswer": "Michael Alford",
                "wrongAnswers": ["Jimbo Fisher", "Kevin O’Sullivan", "Joe Castiglione"]
            }
        ]

        new = QuizTopic(topic_name=topic_name, facts=facts)
        session.add(new)
        await session.commit()
        print("✅ Seeded example topic.")

if __name__ == "__main__":
    asyncio.run(seed())

