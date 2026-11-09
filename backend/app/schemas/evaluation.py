from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime
from backend.app.schemas.question import GroundingChunkOut


class AnswerEvaluationResult(BaseModel):
    response_id: str
    question_id: str
    score_accuracy: float
    score_depth: float
    score_practical: float
    score_clarity: float
    score_overall: float
    feedback: str
    strengths: List[str] = []
    missing_aspects: List[str] = []
    follow_up_triggered: bool = False
    follow_up_question: Optional[str] = None
    next_question_available: bool = True
    session_completed: bool = False


class QuestionReviewItem(BaseModel):
    question_index: int
    topic: str
    difficulty: str
    question_text: str
    candidate_answer: str
    grounding_citations: List[GroundingChunkOut] = []
    score_overall: float
    score_accuracy: float
    score_depth: float
    score_practical: float
    score_clarity: float
    feedback: str
    strengths: List[str] = []
    missing_aspects: List[str] = []
    follow_up_question: Optional[str] = None
    follow_up_answer: Optional[str] = None


class ScorecardReport(BaseModel):
    session_id: str
    candidate_name: str
    candidate_email: Optional[str] = None
    target_role: str
    experience_level: str
    overall_score: float                # 0 - 100
    recommendation: str                 # Strong Hire, Hire, Borderline, Needs Improvement
    summary_verdict: str
    avg_accuracy: float                 # 0 - 10
    avg_depth: float                    # 0 - 10
    avg_practical: float                # 0 - 10
    avg_clarity: float                  # 0 - 10
    key_strengths: List[str] = []
    areas_for_growth: List[str] = []
    interview_transcript: List[QuestionReviewItem] = []
    completed_at: datetime
