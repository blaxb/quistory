from sqlalchemy import Column, Integer, String, JSON
from database import Base

# --------------------
# SQLAlchemy ORM model
# --------------------
class QuizTopic(Base):
    """
    This model corresponds to a table 'quiz_topics' in the database.
    Each row stores:
      - id: auto-incrementing primary key
      - topic_name: unique text identifier (e.g., "florida state softball coach")
      - facts: JSON array of pre-made quiz questions & answers
    """
    __tablename__ = "quiz_topics"

    id = Column(Integer, primary_key=True, index=True)
    topic_name = Column(String, unique=True, nullable=False)
    facts = Column(JSON, nullable=False)

