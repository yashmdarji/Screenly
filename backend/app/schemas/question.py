from typing import List, Optional, Dict, Any
from pydantic import BaseModel


class GroundingChunkOut(BaseModel):
    chunk_id: str
    book_title: str
    author: Optional[str] = None
    chapter_number: Optional[int] = None
    chapter_title: Optional[str] = None
    section_id: Optional[str] = None
    section_title: Optional[str] = None
    text: str
    similarity_score: float


class QuestionOut(BaseModel):
    id: str
    session_id: str
    question_index: int
    total_questions: int
    topic: str
    difficulty: str
    question_text: str
    context_rationale: Optional[str] = None
    grounding_chunks: List[GroundingChunkOut] = []


class AnswerSubmission(BaseModel):
    question_id: str
    answer_text: str


class FollowUpSubmission(BaseModel):
    question_id: str
    follow_up_answer: str
