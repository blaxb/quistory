import asyncio
from sqlalchemy.future import select
from database import SessionLocal
from models import QuizTopic

async def seed_list():
    async with SessionLocal() as db:
        name = "nc colleges"
        # Check if exists
        res = await db.execute(select(QuizTopic).where(QuizTopic.topic_name == name))
        if res.scalars().first():
            print("Already seeded.")
            return
        # List of NC colleges
        colleges = [
            "NC State", "UNC Chapel Hill", "Duke", "Wake Forest",
            "East Carolina", "Appalachian State", "Elizabeth City State",
            "Fayetteville State", "UNC Charlotte", "Winston Salem State"
        ]
        topic = QuizTopic(topic_name=name, facts=colleges)
        db.add(topic)
        await db.commit()
        print("✅ Seeded list‐type topic ‘nc colleges’.")

if __name__ == "__main__":
    asyncio.run(seed_list())

