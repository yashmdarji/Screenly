from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class SessionCreate(BaseModel):
    target_role: str = Field(default="AI/ML Engineer")
    candidate_name: Optional[str] = "Candidate"
    candidate_email: Optional[str] = None
    experience_level: Optional[str] = "Junior / Mid"
    resume_text: Optional[str] = None


class SessionSummary(BaseModel):
    id: str
    candidate_name: str
    candidate_email: Optional[str]
    target_role: str
    experience_level: str
    status: str
    current_question_index: int
    total_questions: int
    created_at: datetime

    class Config:
        from_attributes = True


class SessionDetail(SessionSummary):
    parsed_skills: Optional[Dict[str, Any]] = None
    evaluation_topics: Optional[List[str]] = None
