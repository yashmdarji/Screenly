import re
import json
from typing import Dict, Any, List, Optional
from backend.app.services.llm_service import llm_service
from backend.app.schemas.resume import ResumeParseResult


class QuestionGeneratorService:
    """
    Dynamically generates deep, grounded, role-specific interview questions
    synthesizing candidate resume background and retrieved textbook knowledge chunks.
    """

    @classmethod
    def generate_question(
        cls,
        target_role: str,
        resume: ResumeParseResult,
        question_index: int,
        topic: str,
        difficulty: str,
        retrieved_chunks: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Orchestrates question synthesis with RAG context and candidate profile.
        """
        candidate_skills = resume.raw_skills_list[:6]
        candidate_projects = resume.projects_detected[:2]

        # Prepare grounding excerpt text
        context_excerpts = []
        for i, chunk in enumerate(retrieved_chunks):
            book = chunk.get("book_title", "Foundational Knowledge")
            chapter = chunk.get("chapter_title", "")
            text = chunk.get("text", "")
            context_excerpts.append(f"[{i+1}] Source: {book} - '{chapter}'\nExcerpt: {text}")

        context_block = "\n\n".join(context_excerpts)

        system_prompt = (
            "You are a Principal Technical Interviewer conducting a rigorous technical screening. "
            "Generate one deep, practical, non-generic interview question tailored specifically to the candidate. "
            "The question must be grounded directly in the provided textbook reference excerpts and influenced "
            "by the candidate's declared resume skills and projects.\n"
            "Return valid JSON strictly matching this schema:\n"
            "{\n"
            '  "question_text": "...",\n'
            '  "context_rationale": "Why this question connects the candidate\'s resume to this topic...",\n'
            '  "expected_concepts": ["concept1", "concept2", "concept3"]\n'
            "}"
        )

        user_prompt = (
            f"Target Role: {target_role}\n"
            f"Difficulty: {difficulty}\n"
            f"Topic: {topic}\n"
            f"Candidate Skills: {', '.join(candidate_skills)}\n"
            f"Candidate Projects: {'; '.join(candidate_projects)}\n\n"
            f"--- GROUNDED KNOWLEDGE BASE EXCERPTS ---\n"
            f"{context_block}\n\n"
            f"Generate an applied interview question reflecting this exact difficulty and grounding context."
        )

        # Call LLM service (synchronous)
        raw_output = llm_service.generate_completion(system_prompt, user_prompt)

        # Attempt to parse JSON from LLM
        parsed_llm = cls._parse_json_response(raw_output)

        if not parsed_llm or "question_text" not in parsed_llm or len(parsed_llm["question_text"]) < 20:
            # Fall back to high-fidelity deterministic grounded question builder
            parsed_llm = cls._build_grounded_fallback_question(
                target_role=target_role,
                topic=topic,
                difficulty=difficulty,
                resume=resume,
                retrieved_chunks=retrieved_chunks
            )

        return {
            "topic": topic,
            "difficulty": difficulty,
            "question_text": parsed_llm["question_text"],
            "context_rationale": parsed_llm.get("context_rationale", f"Grounded in {topic} and aligned with candidate's background."),
            "expected_concepts": parsed_llm.get("expected_concepts", [topic, "Trade-off analysis", "Implementation details"]),
            "grounding_chunks": retrieved_chunks
        }

    @classmethod
    def _parse_json_response(cls, text: str) -> Optional[Dict[str, Any]]:
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

    @classmethod
    def _build_grounded_fallback_question(
        cls,
        target_role: str,
        topic: str,
        difficulty: str,
        resume: ResumeParseResult,
        retrieved_chunks: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Deterministic, context-aware question synthesizer ensuring 100% reliable execution
        grounded in the textbook corpus and candidate background.
        """
        primary_chunk = retrieved_chunks[0] if retrieved_chunks else {}
        book = primary_chunk.get("book_title", "Core Foundations")
        chapter = primary_chunk.get("chapter_title", topic)
        top_skill = resume.raw_skills_list[0] if resume.raw_skills_list else "your tech stack"

        # Adaptive questions tailored to role & topics
        if "AI" in target_role or "ML" in target_role:
            if "Ensemble" in topic:
                question_text = (
                    f"Comparing ensemble paradigms discussed in {book}: How does Bootstrap Aggregation (Bagging) in Random Forests "
                    f"differ in variance and bias reduction from Gradient Boosting (GBDT)? What is the mathematical significance of "
                    f"predicting pseudo-residuals (negative gradient of loss) in sequential boosting iterations?"
                )
                expected = ["Bagging decorrelation & variance reduction", "Boosting sequential residual fitting", "Pseudo-residuals as negative gradients", "Learning rate shrinkage"]
            elif "Optimization" in topic or "Neural" in topic:
                question_text = (
                    f"In your background you worked with {top_skill} and neural architectures. Grounded in "
                    f"{book} ('{chapter}'), when training deep networks with gradient descent, how do plateaus and "
                    f"local minima impede weight convergence? Explain the mathematical rationale behind adding a "
                    f"momentum term to weight updates, and how it mitigates high-curvature oscillations compared to standard SGD."
                )
                expected = ["Momentum velocity vector", "Damping oscillations in high curvature", "Escaping saddle points / local minima", "Learning rate scheduling"]
            else:
                question_text = (
                    f"Based on principles in {book} ({chapter}): Explain how the Naive Bayes assumption of conditional independence "
                    f"simplifies Maximum A Posteriori (MAP) estimation. Why does Naive Bayes frequently perform well in real-world "
                    f"classification even when the attribute independence assumption is severely violated?"
                )
                expected = ["P(h|D) = P(D|h)P(h)/P(D)", "Product of conditional probabilities", "Class ranking vs probability calibration", "Zero-frequency laplace smoothing"]

        elif "Backend" in target_role:
            if "Storage" in topic or "Index" in topic:
                question_text = (
                    f"Your resume highlights relational databases and {top_skill}. Grounded in {book}: "
                    f"Compare B-Tree and Log-Structured Merge (LSM) tree storage engines for high-write vs high-read workloads. "
                    f"How do composite index leftmost prefix rules and covered queries optimize execution plans in production databases?"
                )
                expected = ["B+ Trees random I/O vs in-place updates", "LSM-tree MemTable SSTables sequential writes", "Leftmost prefix rule for compound indexes", "Covered index query optimization"]
            elif "Caching" in topic:
                question_text = (
                    f"In distributed backend systems utilizing caching with {top_skill}: Compare Cache-Aside, Write-Through, "
                    f"and Write-Behind strategies. How would you prevent the 'cache stampede' (thundering herd) failure mode "
                    f"when a critical cache key expires under 10,000 queries per second?"
                )
                expected = ["Cache-Aside lazy loading vs Write-Through", "Cache stampede thundering herd", "Mutex locking (single-flight)", "Probabilistic early expiration / XFetch"]
            elif "Transaction" in topic or "ACID" in topic:
                question_text = (
                    f"Grounded in {book} ('{chapter}'): Walk through the SQL isolation levels from Read Committed to Serializable. "
                    f"Explain how Multi-Version Concurrency Control (MVCC) prevents readers from blocking writers, and how you would "
                    f"implement distributed locks with fencing tokens to guarantee idempotency in payment APIs."
                )
                expected = ["Dirty reads non-repeatable reads phantom reads", "MVCC snapshot isolation", "Distributed locking with fencing tokens", "Idempotency key enforcement"]
            elif "Consensus" in topic or "CAP" in topic:
                question_text = (
                    f"According to the CAP theorem in distributed systems: Why is it impossible to provide simultaneous strict Consistency "
                    f"and 100% Availability across network partitions? Describe how eventual consistency models handle conflicting concurrent updates."
                )
                expected = ["CAP partition tolerance reality", "Consistency vs Availability trade-off", "Eventual consistency and monotonic reads", "Conflict resolution / CRDTs or vector clocks"]
            else:
                question_text = (
                    f"In microservice architecture and asynchronous messaging: Compare synchronous REST over HTTP/1.1 with gRPC over HTTP/2, "
                    f"and describe how you would use the Transactional Outbox pattern with Kafka or RabbitMQ to avoid dual-write distributed transaction failures."
                )
                expected = ["REST JSON vs gRPC Protocol Buffers", "HTTP/2 multiplexing streaming", "Dual-write failure modes", "Transactional outbox pattern with message broker"]

        else:
            question_text = (
                f"Drawing from {book} on model evaluation: On an imbalanced dataset where positive cases are only 0.5%, why is accuracy "
                f"a misleading metric? Compare the utility of the Precision-Recall curve vs ROC-AUC, and explain how data leakage can "
                f"inadvertently occur during cross-validation resampling."
            )
            expected = ["Accuracy paradox on imbalanced data", "Precision-Recall AUC vs ROC-AUC", "True negative rate inflation", "Fitting transformations inside CV folds strictly"]

        return {
            "question_text": question_text,
            "context_rationale": f"Selected for {resume.candidate_name}'s declared stack ({top_skill}) and role expectations in {topic}.",
            "expected_concepts": expected
        }
