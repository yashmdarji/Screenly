import re
import json
import math
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
        Uses nuanced semantic scoring with dynamic variance and topic-specific feedback.
        """
        answer_len = len(candidate_answer.strip())

        # If answer is empty or trivial
        if answer_len < 15:
            return {
                "score_accuracy": 1.5,
                "score_depth": 1.0,
                "score_practical": 1.0,
                "score_clarity": 2.0,
                "score_overall": 1.35,
                "feedback": f"No substantive technical explanation provided for {topic}. Please elaborate on the underlying mechanisms and trade-offs.",
                "strengths": [],
                "missing_aspects": expected_concepts,
                "follow_up_triggered": True,
                "follow_up_question": f"Could you provide an initial attempt on {topic}, specifically addressing how you would approach it?"
            }

        # 1. Concept matching & lexical overlap
        lower_ans = candidate_answer.lower()
        matched_concepts = []
        missing_concepts = []

        for concept in expected_concepts:
            concept_tokens = [t.lower() for t in re.findall(r'\b[a-zA-Z0-9_\-\+\#]{3,}\b', concept)]
            # Match if any significant token is present or full phrase is in text
            if concept.lower() in lower_ans or (concept_tokens and sum(1 for t in concept_tokens if t in lower_ans) >= max(1, len(concept_tokens) // 2)):
                matched_concepts.append(concept)
            else:
                missing_concepts.append(concept)

        coverage_ratio = len(matched_concepts) / max(len(expected_concepts), 1)

        # 2. Semantic alignment with grounded chunk excerpts
        chunk_text_combined = " ".join([c.get("text", "") for c in grounding_chunks]).lower()
        chunk_words = set(re.findall(r'\b[a-z]{4,}\b', chunk_text_combined))
        ans_words = set(re.findall(r'\b[a-z]{4,}\b', lower_ans))
        jaccard_overlap = len(ans_words & chunk_words) / max(len(chunk_words), 1) if chunk_words else 0.5

        # 3. Nuanced Dimension Scoring
        # Accuracy: depends on concept coverage and precision
        acc_base = 5.0 + (coverage_ratio * 4.2) + min(jaccard_overlap * 2.0, 0.8)
        score_acc = round(min(max(acc_base, 2.0), 9.9), 1)

        # Depth: rewards equations, formulas, asymptotic notation, and derivations
        math_markers = len(re.findall(r'(\=|\*|\/|\^|\\nabla|\\sum|\\prod|\\sigma|\\alpha|\\beta|\\gamma|\\lambda|o\(|argmin|argmax)', lower_ans))
        depth_bonus = min(math_markers * 0.25, 1.4)
        score_dep = round(min(max((score_acc * 0.90) + depth_bonus + (0.5 if answer_len > 400 else -0.5), 2.0), 9.8), 1)

        # Practical: rewards mentions of scale, production, latency, trade-offs, edge cases
        practical_keywords = [
            "production", "latency", "scale", "concurrency", "qps", "memory", "cache", 
            "bottleneck", "edge case", "failure", "trade-off", "tradeoff", "overhead", 
            "throughput", "variance", "regularization", "overfitting", "noise", "sharding"
        ]
        prac_count = sum(1 for kw in practical_keywords if kw in lower_ans)
        prac_factor = min(prac_count * 0.35, 1.8)
        score_prac = round(min(max((score_acc * 0.82) + prac_factor, 2.0), 9.6), 1)

        # Clarity: rewards structured formatting (numbered lists, paragraphs, bullet points)
        has_structure = 1.0 if bool(re.search(r'(\d+\.|\-|\:|\n\n)', candidate_answer)) else 0.0
        score_clar = round(min(max(7.2 + (has_structure * 1.5) + (0.5 if 200 < answer_len < 1800 else 0.0), 3.0), 9.8), 1)

        # Calculate weighted overall score
        overall = (score_acc * 0.35) + (score_dep * 0.30) + (score_prac * 0.20) + (score_clar * 0.15)
        score_overall = round(overall, 2)

        # 4. Dynamic qualitative feedback synthesis
        strengths = [f"Thoroughly articulated {c}" for c in matched_concepts]
        if math_markers > 2:
            strengths.append("Strong mathematical formalization with explicit parameter notation")
        if prac_count >= 2:
            strengths.append("Evaluated concrete systems and algorithmic trade-offs")

        missing = missing_concepts if missing_concepts else ["Extended empirical validation across disparate distributions"]

        # Build highly customized feedback sentence
        if coverage_ratio >= 0.9:
            feedback = (
                f"Outstanding technical explanation on {topic}. "
                f"Masterfully covered all {len(matched_concepts)} core theoretical tenets with sharp precision. "
                f"Clear mathematical formulation and sound applied reasoning."
            )
        elif coverage_ratio >= 0.7:
            missing_mention = missing[0] if missing else "edge-case asymptotic bounds"
            feedback = (
                f"Strong response on {topic}, addressing {len(matched_concepts)}/{len(expected_concepts)} target concepts. "
                f"Demonstrated solid conceptual intuition; could further explore {missing_mention} to achieve peak depth."
            )
        else:
            missing_str = ", ".join(missing[:2]) if missing else "core mechanisms"
            feedback = (
                f"Good foundational attempt on {topic}. "
                f"Captures high-level terminology, but misses deeper mechanistic analysis regarding {missing_str}."
            )

        # Adaptive follow-up probe trigger
        follow_up_triggered = False
        follow_up_question = None

        if enable_adaptive_probing and (score_overall < 6.8 or answer_len < 90 or len(matched_concepts) < 2):
            follow_up_triggered = True
            missing_item = missing[0] if missing else "underlying trade-offs"
            follow_up_question = (
                f"To probe a bit deeper into your answer on {topic}: "
                f"How would your approach specifically account for {missing_item} in a high-concurrency production environment?"
            )

        return {
            "score_accuracy": score_acc,
            "score_depth": score_dep,
            "score_practical": score_prac,
            "score_clarity": score_clar,
            "score_overall": score_overall,
            "feedback": feedback,
            "strengths": strengths[:4],
            "missing_aspects": missing[:3],
            "follow_up_triggered": follow_up_triggered,
            "follow_up_question": follow_up_question
        }

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
                if s not in strengths and len(strengths) < 6:
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
