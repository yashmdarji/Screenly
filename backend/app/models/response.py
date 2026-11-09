import uuid
from datetime import datetime
from sqlalchemy import Column, String, Float, Text, JSON, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from backend.app.database import Base


class CandidateResponse(Base):
    __tablename__ = "candidate_responses"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String(36), ForeignKey("interview_sessions.id", ondelete="CASCADE"), nullable=False)
    question_id = Column(String(36), ForeignKey("interview_questions.id", ondelete="CASCADE"), nullable=False)

    answer_text = Column(Text, nullable=False)

    # Multi-dimensional rubric scores (0.0 to 10.0)
    score_accuracy = Column(Float, default=0.0)
    score_depth = Column(Float, default=0.0)
    score_practical = Column(Float, default=0.0)
    score_clarity = Column(Float, default=0.0)
    score_overall = Column(Float, default=0.0)

    feedback = Column(Text, nullable=True)
    strengths = Column(JSON, nullable=True)
    missing_aspects = Column(JSON, nullable=True)

    # Adaptive follow-up tracking
    follow_up_triggered = Column(Boolean, default=False)
    follow_up_question = Column(Text, nullable=True)
    follow_up_answer = Column(Text, nullable=True)
    follow_up_score = Column(Float, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    session = relationship("InterviewSession", back_populates="responses")
    question = relationship("InterviewQuestion", back_populates="response")
