import os
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base

# Load .env into environment variables
load_dotenv()

# Grab the DATABASE_URL we set in .env
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL is not set in .env")

# Create the async engine (works with SQLite or Postgres URIs)
engine = create_async_engine(DATABASE_URL, echo=True)

# Create a factory for async sessions
SessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Base class for ORM models
Base = declarative_base()

# Dependency for FastAPI to yield a database session per request
async def get_db():
    async with SessionLocal() as session:
        yield session

