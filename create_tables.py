# create_tables.py

import os
import asyncio
from dotenv import load_dotenv
load_dotenv()  # Load .env file into environment variables

from database import engine, Base

async def init_models():
    print("🚀 Connecting to database...")
    async with engine.begin() as conn:
        print("🛠️ Creating tables...")
        await conn.run_sync(Base.metadata.create_all)
    print("✅ All tables created successfully!")

if __name__ == "__main__":
    asyncio.run(init_models())

