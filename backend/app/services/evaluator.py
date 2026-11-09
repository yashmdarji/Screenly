import re
import json
from typing import Dict, Any, List, Optional
from backend.app.services.llm_service import llm_service


class EvaluatorService:
    """
    Evaluates candidate responses against multi-dimensional scoring rubrics,
    constructs targeted adaptive follow-up probes, and produces overall session scorecards.
    """

    @classmethod
    def evaluate_answer(
        cls,
        question_text: str,
        topic: str,
        expected_concepts: List[str],
        grounding_chunks: List[Dict[str, Any]],
        candidate_answer: str,
        enable_adaptive_probing: bool = True
    ) -> Dict[str, Any]:
        """
        Evaluates candidate answer across Accuracy, Depth, Practical application, and Clarity.
        """
        answer_len = len(candidate_answer.strip())

        # If answer is empty or trivial
        if answer_len < 10:
            return {
                "score_accuracy": 1.0,
                "score_depth": 1.0,
                "score_practical": 1.0,
                "score_clarity": 1.0,
                "score_overall": 1.0,
                "feedback": "No substantive response provided to address the technical requirements.",
                "strengths": [],
                "missing_aspects": expected_concepts,
                "follow_up_triggered": True,
                "follow_up_question": f"Could you provide an initial attempt on {topic}, specifically addressing how you would approach it?"
            }

        # Concept coverage check
        lower_ans = candidate_answer.lower()
        matched_concepts = []
        missing_concepts = []

        for concept in expected_concepts:
            concept_tokens = [t.lower() for t in re.findall(r'\b\w+\b', concept) if len(t) > 3]
            if any(t in lower_ans for t in concept_tokens):
                matched_concepts.append(concept)
            else:
                missing_concepts.append(concept)

        coverage_ratio = len(matched_concepts) / max(len(expected_concepts), 1)

        # Call LLM for qualitative evaluation if configured
        system_prompt = (
            "You are a rigorous technical interview evaluator. Grade the candidate's answer against the question, "
            "expected concepts, and grounded reference context.\n"
            "Score each dimension from 1.0 to 10.0:\n"
            "- score_accuracy: Technical correctness\n"
            "- score_depth: Deep conceptual understanding\n"
            "- score_practical: Real-world engineering trade-offs\n"
            "- score_clarity: Communication structure\n\n"
            "Return valid JSON strictly matching:\n"
            "{\n"
            '  "score_accuracy": 8.0,\n'
            '  "score_depth": 7.5,\n'
            '  "score_practical": 8.0,\n'
            '  "score_clarity": 8.5,\n'
            '  "feedback": "Constructive evaluation...",\n'
            '  "strengths": ["...", "..."],\n'
            '  "missing_aspects": ["..."],\n'
            '  "follow_up_question": null\n'
            "}"
        )

        user_prompt = (
            f"Question: {question_text}\n"
            f"Expected Concepts: {', '.join(expected_concepts)}\n"
            f"Candidate Answer: {candidate_answer}\n"
            f"Grounded Context Snippets: {'; '.join([c.get('text', '')[:120] for c in grounding_chunks[:2]])}"
        )

        raw_llm = llm_service.generate_completion(system_prompt, user_prompt)
        parsed = cls._parse_json(raw_llm)

        if not parsed or "score_accuracy" not in parsed:
            # Deterministic rubric grading engine
            base_score = 4.0 + (coverage_ratio * 4.5)
            # Length & quality adjustment
            if answer_len > 250:
                base_score = min(base_score + 1.0, 9.5)
            elif answer_len < 60:
                base_score = max(base_score - 1.5, 2.5)

            score_acc = round(min(base_score + (0.5 if len(matched_concepts) >= 2 else -0.5), 9.8), 1)
            score_dep = round(min(base_score * 0.95, 9.5), 1)
            score_prac = round(min(base_score * 0.9, 9.2), 1)
            score_clar = round(min(base_score + 0.3, 9.5), 1)

            strengths = [f"Addressed {c}" for c in matched_concepts[:3]]
            if not strengths:
                strengths = ["Attempted an answer touching on core terminology"]

            missing = missing_concepts if missing_concepts else ["Edge case analysis under scale"]
            feedback = (
                f"Candidate covered {len(matched_concepts)}/{len(expected_concepts)} target concepts. "
                f"Demonstrates reasonable familiarity with {topic}, though would benefit from deeper "
                f"mechanistic explanation and trade-off considerations."
            )

            parsed = {
                "score_accuracy": score_acc,
                "score_depth": score_dep,
                "score_practical": score_prac,
                "score_clarity": score_clar,
                "feedback": feedback,
                "strengths": strengths,
                "missing_aspects": missing,
                "follow_up_question": None
            }

        # Calculate weighted overall score (1.0 to 10.0)
        overall = (
            parsed["score_accuracy"] * 0.35 +
            parsed["score_depth"] * 0.30 +
            parsed["score_practical"] * 0.20 +
            parsed["score_clarity"] * 0.15
        )
        parsed["score_overall"] = round(overall, 2)

        # Trigger adaptive follow-up probe if score is borderline (< 6.8) or shallow answer
        follow_up_triggered = False
        follow_up_question = None

        if enable_adaptive_probing and (overall < 6.8 or answer_len < 100):
            follow_up_triggered = True
            missing_item = parsed["missing_aspects"][0] if parsed.get("missing_aspects") else "underlying trade-offs"
            follow_up_question = (
                f"To probe a bit deeper into your answer on {topic}: "
                f"How would your approach specifically account for {missing_item} in a high-concurrency production environment?"
            )

        parsed["follow_up_triggered"] = follow_up_triggered
        parsed["follow_up_question"] = follow_up_question

        return parsed

    @classmethod
    def generate_final_scorecard(
        cls,
        session_id: str,
        candidate_name: str,
        target_role: str,
        experience_level: str,
        responses: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Synthesizes all question evaluations into a comprehensive candidate scorecard.
        """
        if not responses:
            return {
                "overall_score": 0.0,
                "recommendation": "Incomplete Interview",
                "summary_verdict": "Candidate did not submit answers to the interview questions.",
                "avg_accuracy": 0.0,
                "avg_depth": 0.0,
                "avg_practical": 0.0,
                "avg_clarity": 0.0,
                "key_strengths": [],
                "areas_for_growth": []
            }

        total_acc = sum(r.get("score_accuracy", 5.0) for r in responses)
        total_dep = sum(r.get("score_depth", 5.0) for r in responses)
        total_prac = sum(r.get("score_practical", 5.0) for r in responses)
        total_clar = sum(r.get("score_clarity", 5.0) for r in responses)
        total_overall = sum(r.get("score_overall", 5.0) for r in responses)
        n = len(responses)

        avg_acc = round(total_acc / n, 2)
        avg_dep = round(total_dep / n, 2)
        avg_prac = round(total_prac / n, 2)
        avg_clar = round(total_clar / n, 2)
        avg_overall = round(total_overall / n, 2)

        # Scale 1-10 to 0-100%
        scaled_overall = round(avg_overall * 10, 1)

        # Determine Recommendation
        if scaled_overall >= 85.0:
            rec = "Strong Hire"
            verdict = (
                f"{candidate_name} demonstrated exceptional mastery across {target_role} foundational theory "
                f"and applied system considerations. Responses were grounded, rigorous, and clearly communicated."
            )
        elif scaled_overall >= 70.0:
            rec = "Hire"
            verdict = (
                f"{candidate_name} exhibits solid technical competency and good problem-solving acumen for {target_role}. "
                f"Understands core concepts and practical workflows with consistent clarity."
            )
        elif scaled_overall >= 55.0:
            rec = "Borderline / Additional Round Suggested"
            verdict = (
                f"{candidate_name} shows fundamental potential but displayed gaps in deeper architectural trade-offs "
                f"and theoretical rigor on select topics."
            )
        else:
            rec = "Needs Improvement"
            verdict = (
                f"{candidate_name} struggled with technical depth and core mechanisms expected for {target_role}. "
                f"Further practical experience with scalable system design and foundational algorithms recommended."
            )

        # Collect unique strengths and areas for growth
        strengths = []
        growth = []
        for r in responses:
            for s in r.get("strengths", []):
                if s not in strengths and len(strengths) < 5:
                    strengths.append(s)
            for g in r.get("missing_aspects", []):
                if g not in growth and len(growth) < 5:
                    growth.append(g)

        return {
            "overall_score": scaled_overall,
            "recommendation": rec,
            "summary_verdict": verdict,
            "avg_accuracy": avg_acc,
            "avg_depth": avg_dep,
            "avg_practical": avg_prac,
            "avg_clarity": avg_clar,
            "key_strengths": strengths if strengths else ["Consistent communication"],
            "areas_for_growth": growth if growth else ["More edge-case analysis under extreme scale"]
        }

    @classmethod
    def _parse_json(cls, text: str) -> Optional[Dict[str, Any]]:
        """Extracts JSON object from text output."""
        try:
            cleaned = text.strip()
            if "```json" in cleaned:
                cleaned = re.search(r'```json\s*(.*?)\s*```', cleaned, re.DOTALL).group(1)
            elif "```" in cleaned:
                cleaned = re.search(r'```\s*(.*?)\s*```', cleaned, re.DOTALL).group(1)
            return json.loads(cleaned)
        except Exception:
            return None
