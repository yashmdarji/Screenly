import uuid
from datetime import datetime
from sqlalchemy import Column, String, Float, Text, JSON, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from backend.app.database import Base


class SessionScorecard(Base):
    __tablename__ = "session_scorecards"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String(36), ForeignKey("interview_sessions.id", ondelete="CASCADE"), unique=True, nullable=False)

    overall_score = Column(Float, nullable=False, default=0.0)      # Scaled 0 to 100
    recommendation = Column(String(50), nullable=False)             # Strong Hire, Hire, Borderline, Not Recommended
    summary_verdict = Column(Text, nullable=False)

    # Radar metrics
    avg_accuracy = Column(Float, default=0.0)
    avg_depth = Column(Float, default=0.0)
    avg_practical = Column(Float, default=0.0)
    avg_clarity = Column(Float, default=0.0)

    key_strengths = Column(JSON, default=list)
    areas_for_growth = Column(JSON, default=list)
    topic_breakdown = Column(JSON, default=dict)

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    session = relationship("InterviewSession", back_populates="scorecard")
