from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime
from backend.app.database import get_db
from backend.app.models.session import InterviewSession, SessionStatus
from backend.app.models.question import InterviewQuestion
from backend.app.models.response import CandidateResponse
from backend.app.models.evaluation import SessionScorecard
from backend.app.schemas.session import SessionDetail, SessionSummary
from backend.app.schemas.evaluation import ScorecardReport, QuestionReviewItem
from backend.app.schemas.question import GroundingChunkOut
from backend.app.services.resume_parser import ResumeParserService
from backend.app.services.rag_engine import rag_engine
from backend.app.config import settings

router = APIRouter(prefix="/api/sessions", tags=["Session Lifecycle"])


@router.post("/start", response_model=SessionDetail)
def start_interview_session(
    target_role: str = Form("AI/ML Engineer"),
    candidate_name: Optional[str] = Form("Candidate"),
    candidate_email: Optional[str] = Form(None),
    experience_level: Optional[str] = Form("Junior / Mid"),
    resume_file: Optional[UploadFile] = File(None),
    resume_text: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """
    Initializes a new interview session by parsing candidate resume,
    constructing targeted RAG queries, and transitioning status to IN_PROGRESS.
    """
    raw_text = ""
    filename = None

    if isinstance(resume_file, UploadFile) and resume_file.filename:
        filename = resume_file.filename
        content = resume_file.file.read()
        if filename.lower().endswith(".pdf"):
            try:
                raw_text = ResumeParserService.extract_text_from_pdf_bytes(content)
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Failed to parse PDF resume: {str(e)}")
        else:
            raw_text = content.decode("utf-8", errors="ignore")
    elif resume_text:
        raw_text = resume_text
    else:
        # Default mock profile if neither provided for frictionless testing
        raw_text = f"{candidate_name}\nSkills: Python, PyTorch, Docker, SQL, Machine Learning\nTarget: {target_role}"

    # Parse resume
    parsed = ResumeParserService.parse_resume(raw_text, target_role=target_role)

    # Use candidate name from resume if default was passed
    if candidate_name == "Candidate" and parsed.candidate_name != "Candidate":
        candidate_name = parsed.candidate_name
    if not candidate_email and parsed.email:
        candidate_email = parsed.email

    # Construct RAG evaluation topics dynamically
    evaluation_queries = rag_engine.construct_queries_for_candidate(
        target_role=target_role,
        parsed_skills=parsed.raw_skills_list,
        domains=parsed.domains_detected
    )

    # Create new session
    session = InterviewSession(
        candidate_name=candidate_name,
        candidate_email=candidate_email,
        target_role=target_role,
        experience_level=experience_level or parsed.experience_level_inferred,
        resume_filename=filename,
        resume_raw_text=raw_text,
        parsed_skills={
            "skills": parsed.raw_skills_list,
            "domains": parsed.domains_detected,
            "projects": parsed.projects_detected,
            "alignment": parsed.matched_role_alignment
        },
        evaluation_topics=evaluation_queries,
        status=SessionStatus.IN_PROGRESS.value,
        current_question_index=0,
        total_questions=settings.QUESTIONS_PER_SESSION
    )

    db.add(session)
    db.commit()
    db.refresh(session)

    return SessionDetail(
        id=session.id,
        candidate_name=session.candidate_name,
        candidate_email=session.candidate_email,
        target_role=session.target_role,
        experience_level=session.experience_level,
        status=session.status,
        current_question_index=session.current_question_index,
        total_questions=session.total_questions,
        created_at=session.created_at,
        parsed_skills=session.parsed_skills,
        evaluation_topics=[q["topic"] for q in evaluation_queries]
    )


@router.get("/{session_id}", response_model=SessionDetail)
def get_session(session_id: str, db: Session = Depends(get_db)):
    """Retrieves session status and details."""
    session = db.query(InterviewSession).filter(InterviewSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Interview session not found.")

    topics = [q.get("topic", "") for q in (session.evaluation_topics or [])]

    return SessionDetail(
        id=session.id,
        candidate_name=session.candidate_name,
        candidate_email=session.candidate_email,
        target_role=session.target_role,
        experience_level=session.experience_level,
        status=session.status,
        current_question_index=session.current_question_index,
        total_questions=session.total_questions,
        created_at=session.created_at,
        parsed_skills=session.parsed_skills,
        evaluation_topics=topics
    )


@router.get("/{session_id}/scorecard", response_model=ScorecardReport)
def get_session_scorecard(session_id: str, db: Session = Depends(get_db)):
    """
    Returns complete interview scorecard, radar metrics, and full
    question-by-question audit trail with knowledge base grounding citations.
    """
    session = db.query(InterviewSession).filter(InterviewSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Interview session not found.")

    scorecard = db.query(SessionScorecard).filter(SessionScorecard.session_id == session_id).first()
    if not scorecard:
        raise HTTPException(status_code=400, detail="Scorecard has not been generated yet. Please complete the interview.")

    # Build question transcript with grounding citations
    questions = db.query(InterviewQuestion).filter(InterviewQuestion.session_id == session_id).order_by(InterviewQuestion.question_index).all()
    transcript = []

    for q in questions:
        resp = db.query(CandidateResponse).filter(CandidateResponse.question_id == q.id).first()
        citations = []
        for c in (q.grounding_chunks or []):
            citations.append(GroundingChunkOut(
                chunk_id=c.get("chunk_id", ""),
                book_title=c.get("book_title", "Knowledge Base"),
                author=c.get("author"),
                chapter_number=c.get("chapter_number"),
                chapter_title=c.get("chapter_title"),
                section_id=c.get("section_id"),
                section_title=c.get("section_title"),
                text=c.get("text", ""),
                similarity_score=c.get("similarity_score", 0.0)
            ))

        transcript.append(QuestionReviewItem(
            question_index=q.question_index,
            topic=q.topic,
            difficulty=q.difficulty,
            question_text=q.question_text,
            candidate_answer=resp.answer_text if resp else "No answer recorded",
            grounding_citations=citations,
            score_overall=resp.score_overall if resp else 0.0,
            score_accuracy=resp.score_accuracy if resp else 0.0,
            score_depth=resp.score_depth if resp else 0.0,
            score_practical=resp.score_practical if resp else 0.0,
            score_clarity=resp.score_clarity if resp else 0.0,
            feedback=resp.feedback if resp else "Not evaluated",
            strengths=resp.strengths or [] if resp else [],
            missing_aspects=resp.missing_aspects or [] if resp else [],
            follow_up_question=resp.follow_up_question if resp else None,
            follow_up_answer=resp.follow_up_answer if resp else None
        ))

    return ScorecardReport(
        session_id=session.id,
        candidate_name=session.candidate_name,
        candidate_email=session.candidate_email,
        target_role=session.target_role,
        experience_level=session.experience_level,
        overall_score=scorecard.overall_score,
        recommendation=scorecard.recommendation,
        summary_verdict=scorecard.summary_verdict,
        avg_accuracy=scorecard.avg_accuracy,
        avg_depth=scorecard.avg_depth,
        avg_practical=scorecard.avg_practical,
        avg_clarity=scorecard.avg_clarity,
        key_strengths=scorecard.key_strengths or [],
        areas_for_growth=scorecard.areas_for_growth or [],
        interview_transcript=transcript,
        completed_at=scorecard.created_at
    )


@router.get("", response_model=List[SessionSummary])
def list_sessions(db: Session = Depends(get_db)):
    """Lists recent candidate interview sessions."""
    sessions = db.query(InterviewSession).order_by(InterviewSession.created_at.desc()).limit(20).all()
    return sessions
