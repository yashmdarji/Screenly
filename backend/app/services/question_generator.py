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
        retrieved_chunks: List[Dict[str, Any]],
        experience_level: str = "Mid-Level"
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
            f"Experience Level: {experience_level}\n"
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
                retrieved_chunks=retrieved_chunks,
                experience_level=experience_level
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
        retrieved_chunks: List[Dict[str, Any]],
        experience_level: str = "Mid-Level"
    ) -> Dict[str, Any]:
        """
        Deterministic, context-aware question synthesizer ensuring 100% reliable execution
        grounded in the textbook corpus, candidate background, and seniority tier.
        """
        primary_chunk = retrieved_chunks[0] if retrieved_chunks else {}
        book = primary_chunk.get("book_title", "Core Foundations")
        chapter = primary_chunk.get("chapter_title", topic)
        top_skill = resume.raw_skills_list[0] if resume.raw_skills_list else "your tech stack"

        exp_lower = (experience_level or "mid").lower()
        if "junior" in exp_lower or "intern" in exp_lower or "entry" in exp_lower:
            tier = "junior"
        elif "senior" in exp_lower or "staff" in exp_lower or "lead" in exp_lower:
            tier = "senior"
        else:
            tier = "mid"

        # Adaptive questions tailored to role, topics & seniority tier
        if "AI" in target_role or "ML" in target_role:
            if "Generalization" in topic or "Overfitting" in topic or "Regularization" in topic:
                if tier == "junior":
                    question_text = (
                        f"From {book} ('{chapter}'): What is the difference between underfitting and overfitting? "
                        f"How can you diagnose overfitting using training vs. validation loss curves, and how does L2 regularization help prevent it?"
                    )
                    expected = ["Underfitting vs overfitting bias variance", "Training vs validation loss divergence", "L2 weight penalty shrinks parameters", "Early stopping / cross-validation"]
                elif tier == "senior":
                    question_text = (
                        f"In production ML pipelines grounded in {book}: How do covariate shift and target leakage invalidate standard k-fold cross-validation? "
                        f"Compare ElasticNet (L1+L2) regularization against post-hoc temperature scaling calibration when deploying models under shifting class priors."
                    )
                    expected = ["Covariate shift and temporal leakage", "ElasticNet sparsity plus multicollinearity grouping", "Post-hoc temperature scaling calibration", "GroupKFold / time-series splitting"]
                else:
                    question_text = (
                        f"Regarding model validation and generalization from {book}: Explain the Bias-Variance decomposition of generalization error. "
                        f"Compare L1 (Lasso) vs L2 (Ridge) regularization mathematically and explain geometrically why L1 creates sparse feature weights while L2 smoothly shrinks them toward zero."
                    )
                    expected = ["Bias^2 + Variance + Irreducible Error", "L1 diamond L1-ball geometry", "Feature sparsity vs shrinkage", "Multicollinearity handling"]

            elif "SVM" in topic or "Statistical" in topic:
                if tier == "junior":
                    question_text = (
                        f"Based on {book} ('{chapter}'): Why does a Support Vector Machine try to maximize the margin between classes? "
                        f"What are 'support vectors', and why do decision trees sometimes overfit compared to a max-margin linear classifier?"
                    )
                    expected = ["Maximum margin widens separation boundary", "Support vectors closest points to hyperplane", "Decision tree high variance without pruning", "Generalization margin robustness"]
                elif tier == "senior":
                    question_text = (
                        f"Scaling kernel methods from {book} to web-scale workloads (10M+ samples): Why does exact RBF Kernel SVM training hit an O(N^2) to O(N^3) bottleneck? "
                        f"Compare Nyström low-rank approximations against Random Fourier Features (Rahimi & Recht) for approximating non-linear boundaries in linear time."
                    )
                    expected = ["Kernel matrix O(N^2) memory bottleneck", "Nystrom landmark sampling decomposition", "Random Fourier Features Bochner theorem", "Linear-time primal optimization SGD"]
                else:
                    question_text = (
                        f"Drawing from {book} on Support Vector Machines: Explain how the Maximum Margin Hyperplane is formulated mathematically as a constrained optimization problem. "
                        f"What is the role of support vectors, and how does the Kernel Trick (e.g. RBF kernel) enable non-linear classification without explicit high-dimensional mapping?"
                    )
                    expected = ["Margin maximization 2/||w||", "Support vectors on margin boundary", "Kernel trick phi(x) . phi(z)", "Slack variables for soft margin"]

            elif "Ensemble" in topic or "Boosting" in topic:
                if tier == "junior":
                    question_text = (
                        f"Grounded in {book} ('{chapter}'): Explain the main difference between Bagging (Random Forests) and Boosting. "
                        f"Why does averaging predictions across multiple randomized trees improve stability over a single decision tree?"
                    )
                    expected = ["Bagging parallel bootstrap sampling", "Boosting sequential error correction", "Variance reduction via averaging", "Feature subsampling decorrelation"]
                elif tier == "senior":
                    question_text = (
                        f"When scaling Gradient Boosted Trees (XGBoost/LightGBM) on sparse terabyte-scale tabular data: "
                        f"How do second-order Taylor approximations (Hessian weighting), histogram-based quantile binning, and Gradient-based One-Side Sampling (GOSS) optimize training throughput without losing accuracy?"
                    )
                    expected = ["Second-order Newton step Hessian weighting", "Histogram quantile binning O(bins) split finding", "GOSS retains large-gradient instances", "Regularized leaf weights L1/L2"]
                else:
                    question_text = (
                        f"Comparing ensemble paradigms discussed in {book}: How does Bootstrap Aggregation (Bagging) in Random Forests "
                        f"differ in variance and bias reduction from Gradient Boosting (GBDT)? What is the mathematical significance of "
                        f"predicting pseudo-residuals (negative gradient of loss) in sequential boosting iterations?"
                    )
                    expected = ["Bagging decorrelation & variance reduction", "Boosting sequential residual fitting", "Pseudo-residuals as negative gradients", "Learning rate shrinkage"]

            elif "Optimization" in topic or "Neural" in topic:
                if tier == "junior":
                    question_text = (
                        f"Working with {top_skill} and neural networks ({book}): Why do we typically train with mini-batch gradient descent instead of full-batch or single-sample updates? "
                        f"What happens if your learning rate is set too high versus too low?"
                    )
                    expected = ["Mini-batch hardware vectorization & noisy regularization", "Too high learning rate diverges / overshoots", "Too low learning rate stalls slowly", "Momentum smooths gradient steps"]
                elif tier == "senior":
                    question_text = (
                        f"In distributed multi-GPU training with {top_skill} and large batch sizes ({book}): Why does large-batch SGD suffer from sharp minima and generalization degradation? "
                        f"Explain how linear learning rate warmup, decoupled weight decay (AdamW), and gradient clipping stabilize convergence across nodes."
                    )
                    expected = ["Sharp vs flat minima generalization gap", "Linear LR scaling with warmup", "AdamW decoupled weight decay vs L2", "Gradient norm clipping against exploding updates"]
                else:
                    question_text = (
                        f"In your background you worked with {top_skill} and neural architectures. Grounded in "
                        f"{book} ('{chapter}'), when training deep networks with gradient descent, how do plateaus and "
                        f"local minima impede weight convergence? Explain the mathematical rationale behind adding a "
                        f"momentum term to weight updates, and how it mitigates high-curvature oscillations compared to standard SGD."
                    )
                    expected = ["Momentum velocity vector", "Damping oscillations in high curvature", "Escaping saddle points / local minima", "Learning rate scheduling"]

            else:
                if tier == "junior":
                    question_text = (
                        f"From {book} ({chapter}): What is Bayes' Theorem, and why is Naive Bayes called 'naive'? "
                        f"Give a practical example of how Laplace smoothing prevents zero-probability bugs when an unseen word appears during inference."
                    )
                    expected = ["Bayes rule posterior likelihood prior", "Conditional independence naive assumption", "Zero-probability multiplication collapse", "Laplace add-one smoothing"]
                elif tier == "senior":
                    question_text = (
                        f"Synthesizing statistical learning theory from {book}: Analyze how VC Dimension and Rademacher Complexity bound out-of-sample generalization error. "
                        f"In Bayesian neural networks or variational inference, why is the exact posterior intractable, and how does maximizing the ELBO objective resolve it?"
                    )
                    expected = ["VC dimension shattering capacity bound", "Rademacher complexity data-dependent bound", "Intractable partition function integral", "ELBO KL divergence + reconstruction"]
                else:
                    question_text = (
                        f"Based on principles in {book} ({chapter}): Explain how the Naive Bayes assumption of conditional independence "
                        f"simplifies Maximum A Posteriori (MAP) estimation. Why does Naive Bayes frequently perform well in real-world "
                        f"classification even when the attribute independence assumption is severely violated?"
                    )
                    expected = ["P(h|D) = P(D|h)P(h)/P(D)", "Product of conditional probabilities", "Class ranking vs probability calibration", "Zero-frequency laplace smoothing"]

        elif "Backend" in target_role:
            level_prefix = "At entry-level scale" if tier == "junior" else ("At high-throughput distributed production scale (50k+ QPS)" if tier == "senior" else "In production backend systems")
            if "Storage" in topic or "Index" in topic:
                question_text = (
                    f"{level_prefix}, utilizing databases and {top_skill} ({book}): "
                    f"Compare B-Tree and Log-Structured Merge (LSM) tree storage engines for high-write vs high-read workloads. "
                    f"How do composite index leftmost prefix rules and covered queries optimize execution plans?"
                )
                expected = ["B+ Trees random I/O vs in-place updates", "LSM-tree MemTable SSTables sequential writes", "Leftmost prefix rule for compound indexes", "Covered index query optimization"]
            elif "Caching" in topic:
                question_text = (
                    f"{level_prefix} using caching with {top_skill}: Compare Cache-Aside, Write-Through, "
                    f"and Write-Behind strategies. How would you prevent the 'cache stampede' (thundering herd) failure mode "
                    f"when a critical cache key expires under concurrent load?"
                )
                expected = ["Cache-Aside lazy loading vs Write-Through", "Cache stampede thundering herd", "Mutex locking (single-flight)", "Probabilistic early expiration / XFetch"]
            elif "Transaction" in topic or "ACID" in topic:
                question_text = (
                    f"{level_prefix} grounded in {book} ('{chapter}'): Walk through SQL isolation levels from Read Committed to Serializable. "
                    f"Explain how Multi-Version Concurrency Control (MVCC) prevents readers from blocking writers, and how you would "
                    f"implement distributed locks with fencing tokens to guarantee idempotency in payment APIs."
                )
                expected = ["Dirty reads non-repeatable reads phantom reads", "MVCC snapshot isolation", "Distributed locking with fencing tokens", "Idempotency key enforcement"]
            elif "Consensus" in topic or "CAP" in topic:
                question_text = (
                    f"{level_prefix} according to the CAP theorem: Why is it impossible to provide simultaneous strict Consistency "
                    f"and 100% Availability across network partitions? Describe how eventual consistency models handle conflicting concurrent updates."
                )
                expected = ["CAP partition tolerance reality", "Consistency vs Availability trade-off", "Eventual consistency and monotonic reads", "Conflict resolution / CRDTs or vector clocks"]
            else:
                question_text = (
                    f"{level_prefix} in microservice architecture: Compare synchronous REST over HTTP/1.1 with gRPC over HTTP/2, "
                    f"and describe how you would use the Transactional Outbox pattern with Kafka or RabbitMQ to avoid dual-write failures."
                )
                expected = ["REST JSON vs gRPC Protocol Buffers", "HTTP/2 multiplexing streaming", "Dual-write failure modes", "Transactional outbox pattern with message broker"]

        else:
            level_prefix = "Foundational evaluation" if tier == "junior" else ("Production ML systems evaluation" if tier == "senior" else "Applied model evaluation")
            question_text = (
                f"[{level_prefix}] Drawing from {book}: On an imbalanced dataset where positive cases are only 0.5%, why is accuracy "
                f"a misleading metric? Compare the utility of the Precision-Recall curve vs ROC-AUC, and explain how data leakage can "
                f"inadvertently occur during cross-validation resampling."
            )
            expected = ["Accuracy paradox on imbalanced data", "Precision-Recall AUC vs ROC-AUC", "True negative rate inflation", "Fitting transformations inside CV folds strictly"]

        return {
            "question_text": question_text,
            "context_rationale": f"Calibrated for {experience_level} ({difficulty}) — selected for {resume.candidate_name}'s declared stack ({top_skill}) in {topic}.",
            "expected_concepts": expected
        }
