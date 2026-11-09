import uuid
from datetime import datetime
from enum import Enum
from sqlalchemy import Column, String, DateTime, Text, JSON, Integer
from sqlalchemy.orm import relationship
from backend.app.database import Base


class SessionStatus(str, Enum):
    CREATED = "CREATED"
    RESUME_PARSED = "RESUME_PARSED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"


class InterviewSession(Base):
    __tablename__ = "interview_sessions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    candidate_name = Column(String(120), nullable=True, default="Candidate")
    candidate_email = Column(String(180), nullable=True)
    target_role = Column(String(80), nullable=False, default="AI/ML Engineer")
    experience_level = Column(String(40), default="Junior / Mid")

    resume_filename = Column(String(255), nullable=True)
    resume_raw_text = Column(Text, nullable=True)
    parsed_skills = Column(JSON, nullable=True)      # {"skills": [...], "domains": [...]}
    evaluation_topics = Column(JSON, nullable=True)  # List of identified evaluation topics

    status = Column(String(30), default=SessionStatus.CREATED.value)
    current_question_index = Column(Integer, default=0)
    total_questions = Column(Integer, default=5)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    questions = relationship("InterviewQuestion", back_populates="session", cascade="all, delete-orphan", order_by="InterviewQuestion.question_index")
    responses = relationship("CandidateResponse", back_populates="session", cascade="all, delete-orphan")
    scorecard = relationship("SessionScorecard", back_populates="session", uselist=False, cascade="all, delete-orphan")
