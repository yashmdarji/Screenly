from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any, List
from backend.app.database import get_db
from backend.app.models.session import InterviewSession, SessionStatus
from backend.app.models.question import InterviewQuestion
from backend.app.models.response import CandidateResponse
from backend.app.models.evaluation import SessionScorecard
from backend.app.schemas.question import QuestionOut, AnswerSubmission, FollowUpSubmission
from backend.app.schemas.evaluation import AnswerEvaluationResult
from backend.app.schemas.resume import ResumeParseResult, SkillTaxonomy
from backend.app.services.rag_engine import rag_engine
from backend.app.services.question_generator import QuestionGeneratorService
from backend.app.services.evaluator import EvaluatorService
from backend.app.config import settings

router = APIRouter(prefix="/api/interview", tags=["Interactive Interview"])


@router.get("/{session_id}/current-question", response_model=QuestionOut)
def get_current_question(session_id: str, db: Session = Depends(get_db)):
    """
    Retrieves or dynamically generates the current interview question
    using RAG retrieval grounded in textbook knowledge and candidate background.
    """
    session = db.query(InterviewSession).filter(InterviewSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Interview session not found.")

    if session.status == SessionStatus.COMPLETED.value:
        raise HTTPException(status_code=400, detail="Interview session has already been completed.")

    current_idx = session.current_question_index

    # Check if question for this index already exists
    existing_question = db.query(InterviewQuestion).filter(
        InterviewQuestion.session_id == session_id,
        InterviewQuestion.question_index == current_idx
    ).first()

    if existing_question:
        return QuestionOut(
            id=existing_question.id,
            session_id=session.id,
            question_index=existing_question.question_index,
            total_questions=session.total_questions,
            topic=existing_question.topic,
            difficulty=existing_question.difficulty,
            question_text=existing_question.question_text,
            context_rationale=existing_question.context_rationale,
            grounding_chunks=existing_question.grounding_chunks or []
        )

    # Determine adaptive difficulty based on previous response
    difficulty = "Medium"
    if current_idx > 0:
        prev_response = db.query(CandidateResponse).join(InterviewQuestion).filter(
            InterviewQuestion.session_id == session_id,
            InterviewQuestion.question_index == current_idx - 1
        ).first()

        if prev_response and settings.ENABLE_ADAPTIVE_DIFFICULTY:
            if prev_response.score_overall >= 8.2:
                difficulty = "Advanced" if current_idx >= 3 else "Hard"
            elif prev_response.score_overall < 5.8:
                difficulty = "Foundational"

    # Select topic from prepared session queries
    topics_list = session.evaluation_topics or []
    if current_idx < len(topics_list):
        topic_info = topics_list[current_idx]
        topic = topic_info.get("topic", f"Core Competency {current_idx + 1}")
        search_query = topic_info.get("query", topic)
    else:
        topic = f"Advanced System Principles {current_idx + 1}"
        search_query = f"{session.target_role} trade-offs and real-world architectures"

    # RAG Retrieval: fetch grounded textbook chunks
    retrieved_chunks = rag_engine.retrieve_grounded_context(
        query=search_query,
        target_role=session.target_role,
        top_k=settings.TOP_K_RETRIEVAL
    )

    # Reconstruct resume schema
    skills_data = session.parsed_skills or {}
    resume_obj = ResumeParseResult(
        candidate_name=session.candidate_name,
        skills=SkillTaxonomy(),
        raw_skills_list=skills_data.get("skills", []),
        domains_detected=skills_data.get("domains", []),
        projects_detected=skills_data.get("projects", []),
        total_characters_parsed=len(session.resume_raw_text or "")
    )

    # Generate question with AI/ML grounded pipeline
    gen_result = QuestionGeneratorService.generate_question(
        target_role=session.target_role,
        resume=resume_obj,
        question_index=current_idx,
        topic=topic,
        difficulty=difficulty,
        retrieved_chunks=retrieved_chunks
    )

    # Persist question to DB for auditability & traceability
    new_question = InterviewQuestion(
        session_id=session.id,
        question_index=current_idx,
        topic=topic,
        difficulty=difficulty,
        question_text=gen_result["question_text"],
        context_rationale=gen_result.get("context_rationale"),
        expected_concepts=gen_result.get("expected_concepts", []),
        grounding_chunks=gen_result.get("grounding_chunks", [])
    )
    db.add(new_question)
    db.commit()
    db.refresh(new_question)

    return QuestionOut(
        id=new_question.id,
        session_id=session.id,
        question_index=new_question.question_index,
        total_questions=session.total_questions,
        topic=new_question.topic,
        difficulty=new_question.difficulty,
        question_text=new_question.question_text,
        context_rationale=new_question.context_rationale,
        grounding_chunks=new_question.grounding_chunks or []
    )


@router.post("/{session_id}/submit-answer", response_model=AnswerEvaluationResult)
def submit_candidate_answer(
    session_id: str,
    submission: AnswerSubmission,
    db: Session = Depends(get_db)
):
    """
    Submits and evaluates candidate response against the multi-dimensional rubric.
    Triggers adaptive follow-up probe if required or advances to next question.
    """
    session = db.query(InterviewSession).filter(InterviewSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Interview session not found.")

    question = db.query(InterviewQuestion).filter(
        InterviewQuestion.id == submission.question_id,
        InterviewQuestion.session_id == session_id
    ).first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found for this session.")

    # Check if answer already exists
    existing_resp = db.query(CandidateResponse).filter(CandidateResponse.question_id == question.id).first()
    if existing_resp:
        raise HTTPException(status_code=400, detail="Answer for this question has already been submitted.")

    # Evaluate answer with multi-dimensional rubric
    eval_result = EvaluatorService.evaluate_answer(
        question_text=question.question_text,
        topic=question.topic,
        expected_concepts=question.expected_concepts or [],
        grounding_chunks=question.grounding_chunks or [],
        candidate_answer=submission.answer_text,
        enable_adaptive_probing=settings.ENABLE_FOLLOWUP_PROBES
    )

    # Persist CandidateResponse
    response_record = CandidateResponse(
        session_id=session.id,
        question_id=question.id,
        answer_text=submission.answer_text,
        score_accuracy=eval_result["score_accuracy"],
        score_depth=eval_result["score_depth"],
        score_practical=eval_result["score_practical"],
        score_clarity=eval_result["score_clarity"],
        score_overall=eval_result["score_overall"],
        feedback=eval_result["feedback"],
        strengths=eval_result["strengths"],
        missing_aspects=eval_result["missing_aspects"],
        follow_up_triggered=eval_result["follow_up_triggered"],
        follow_up_question=eval_result.get("follow_up_question")
    )
    db.add(response_record)

    # If follow-up was NOT triggered, advance index immediately
    session_completed = False
    if not eval_result["follow_up_triggered"]:
        session.current_question_index += 1
        if session.current_question_index >= session.total_questions:
            session.status = SessionStatus.COMPLETED.value
            session_completed = True
            _compute_and_save_scorecard(session, db)

    db.commit()
    db.refresh(response_record)

    return AnswerEvaluationResult(
        response_id=response_record.id,
        question_id=question.id,
        score_accuracy=response_record.score_accuracy,
        score_depth=response_record.score_depth,
        score_practical=response_record.score_practical,
        score_clarity=response_record.score_clarity,
        score_overall=response_record.score_overall,
        feedback=response_record.feedback,
        strengths=response_record.strengths or [],
        missing_aspects=response_record.missing_aspects or [],
        follow_up_triggered=response_record.follow_up_triggered,
        follow_up_question=response_record.follow_up_question,
        next_question_available=(session.current_question_index < session.total_questions and not response_record.follow_up_triggered),
        session_completed=session_completed
    )


@router.post("/{session_id}/submit-followup", response_model=AnswerEvaluationResult)
def submit_follow_up_answer(
    session_id: str,
    payload: FollowUpSubmission,
    db: Session = Depends(get_db)
):
    """
    Submits candidate's response to an adaptive follow-up probe and advances interview.
    """
    session = db.query(InterviewSession).filter(InterviewSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Interview session not found.")

    response_record = db.query(CandidateResponse).filter(
        CandidateResponse.question_id == payload.question_id,
        CandidateResponse.session_id == session_id
    ).first()
    if not response_record:
        raise HTTPException(status_code=404, detail="Response record not found.")

    # Update follow-up answer and boost score moderately for addressing probe
    response_record.follow_up_answer = payload.follow_up_answer
    if len(payload.follow_up_answer.strip()) > 30:
        boost = 0.8
        response_record.score_depth = min(response_record.score_depth + boost, 10.0)
        response_record.score_practical = min(response_record.score_practical + boost, 10.0)
        response_record.score_overall = round(
            response_record.score_accuracy * 0.35 +
            response_record.score_depth * 0.30 +
            response_record.score_practical * 0.20 +
            response_record.score_clarity * 0.15,
            2
        )
        response_record.feedback += f" Follow-up probe addressed well, reinforcing practical depth."

    # Advance question index
    session.current_question_index += 1
    session_completed = False
    if session.current_question_index >= session.total_questions:
        session.status = SessionStatus.COMPLETED.value
        session_completed = True
        _compute_and_save_scorecard(session, db)

    db.commit()
    db.refresh(response_record)

    return AnswerEvaluationResult(
        response_id=response_record.id,
        question_id=payload.question_id,
        score_accuracy=response_record.score_accuracy,
        score_depth=response_record.score_depth,
        score_practical=response_record.score_practical,
        score_clarity=response_record.score_clarity,
        score_overall=response_record.score_overall,
        feedback=response_record.feedback,
        strengths=response_record.strengths or [],
        missing_aspects=response_record.missing_aspects or [],
        follow_up_triggered=False,
        follow_up_question=None,
        next_question_available=(session.current_question_index < session.total_questions),
        session_completed=session_completed
    )


def _compute_and_save_scorecard(session: InterviewSession, db: Session):
    """Calculates overall scorecard across all responses."""
    responses = db.query(CandidateResponse).filter(CandidateResponse.session_id == session.id).all()
    resp_dicts = [
        {
            "score_accuracy": r.score_accuracy,
            "score_depth": r.score_depth,
            "score_practical": r.score_practical,
            "score_clarity": r.score_clarity,
            "score_overall": r.score_overall,
            "strengths": r.strengths or [],
            "missing_aspects": r.missing_aspects or []
        }
        for r in responses
    ]

    card_data = EvaluatorService.generate_final_scorecard(
        session_id=session.id,
        candidate_name=session.candidate_name,
        target_role=session.target_role,
        experience_level=session.experience_level,
        responses=resp_dicts
    )

    existing_card = db.query(SessionScorecard).filter(SessionScorecard.session_id == session.id).first()
    if not existing_card:
        scorecard = SessionScorecard(
            session_id=session.id,
            overall_score=card_data["overall_score"],
            recommendation=card_data["recommendation"],
            summary_verdict=card_data["summary_verdict"],
            avg_accuracy=card_data["avg_accuracy"],
            avg_depth=card_data["avg_depth"],
            avg_practical=card_data["avg_practical"],
            avg_clarity=card_data["avg_clarity"],
            key_strengths=card_data["key_strengths"],
            areas_for_growth=card_data["areas_for_growth"]
        )
        db.add(scorecard)
