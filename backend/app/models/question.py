import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Text, JSON, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from backend.app.database import Base


class InterviewQuestion(Base):
    __tablename__ = "interview_questions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String(36), ForeignKey("interview_sessions.id", ondelete="CASCADE"), nullable=False)
    question_index = Column(Integer, nullable=False)

    topic = Column(String(100), nullable=False)
    difficulty = Column(String(30), default="Medium")  # Easy, Medium, Hard, Advanced
    question_text = Column(Text, nullable=False)
    context_rationale = Column(Text, nullable=True)     # Why this question was chosen based on resume
    expected_concepts = Column(JSON, nullable=True)     # List of keywords/concepts expected in answer

    # Grounding RAG Traceability
    # List of { "chunk_id", "book_title", "author", "chapter", "section", "text", "similarity" }
    grounding_chunks = Column(JSON, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    session = relationship("InterviewSession", back_populates="questions")
    response = relationship("CandidateResponse", back_populates="question", uselist=False, cascade="all, delete-orphan")
