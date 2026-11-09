import unittest
from backend.app.database import init_db, SessionLocal
from backend.app.routers.session_routes import start_interview_session, get_session, get_session_scorecard
from backend.app.routers.interview_routes import get_current_question, submit_candidate_answer
from backend.app.schemas.question import AnswerSubmission

init_db()


class TestInterviewFlow(unittest.TestCase):
    def setUp(self):
        self.db = SessionLocal()

    def tearDown(self):
        self.db.close()

    def test_full_interview_lifecycle(self):
        # 1. Start interview session
        session = start_interview_session(
            target_role="AI/ML Engineer",
            candidate_name="Alex Chen",
            candidate_email="alex.chen@example.com",
            experience_level="Mid-Level",
            resume_text="Experienced ML Engineer with PyTorch, Scikit-Learn, Docker, and RAG architectures.",
            db=self.db
        )
        self.assertIsNotNone(session.id)
        self.assertEqual(session.target_role, "AI/ML Engineer")
        self.assertEqual(session.status, "IN_PROGRESS")

        # 2. Get current question (grounded via RAG)
        question = get_current_question(session_id=session.id, db=self.db)
        self.assertIsNotNone(question.question_text)
        self.assertGreater(len(question.grounding_chunks), 0)
        top_citation = question.grounding_chunks[0]
        self.assertIsNotNone(top_citation.book_title)

        # 3. Submit candidate technical answer
        submission = AnswerSubmission(
            question_id=question.id,
            answer_text=(
                "In deep neural networks, plateaus and narrow ravines cause standard SGD to stall or oscillate. "
                "Adding a momentum term accumulates a velocity vector in directions of consistent descent, damping "
                "orthogonal oscillations. For regularization, L1 introduces sparsity via diamond norm corners, whereas "
                "L2 shrinks weights continuously toward zero."
            )
        )
        eval_result = submit_candidate_answer(session_id=session.id, submission=submission, db=self.db)
        self.assertGreater(eval_result.score_overall, 0.0)
        self.assertGreater(eval_result.score_accuracy, 0.0)
        self.assertIsNotNone(eval_result.feedback)

        # Verify session record updated
        updated_session = get_session(session_id=session.id, db=self.db)
        self.assertGreaterEqual(updated_session.current_question_index, 0)


if __name__ == "__main__":
    unittest.main()
