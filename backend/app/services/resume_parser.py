import io
import re
from typing import Dict, List, Any, Optional
from pypdf import PdfReader
from backend.app.schemas.resume import ResumeParseResult, SkillTaxonomy

# Skill taxonomy database
SKILL_TAXONOMY = {
    "languages": [
        "python", "go", "golang", "java", "c++", "c#", "rust", "javascript", 
        "typescript", "scala", "r", "sql", "bash", "shell"
    ],
    "frameworks": [
        "fastapi", "flask", "django", "express", "react", "next.js", "vue", 
        "node.js", "spring", "spring boot", "gin", "nest.js"
    ],
    "ml_ai_tools": [
        "pytorch", "tensorflow", "keras", "scikit-learn", "huggingface", 
        "transformers", "langchain", "llamaindex", "chromadb", "faiss", 
        "qdrant", "opencv", "numpy", "pandas", "xgboost", "lightgbm", 
        "spacy", "nltk", "jax", "tensorrt", "rag"
    ],
    "databases": [
        "postgresql", "postgres", "mysql", "sqlite", "mongodb", "redis", 
        "cassandra", "dynamodb", "elasticsearch", "neo4j", "mariadb"
    ],
    "cloud_devops": [
        "docker", "kubernetes", "aws", "gcp", "azure", "ci/cd", "github actions", 
        "terraform", "kafka", "rabbitmq", "celery", "nginx", "prometheus", "grafana"
    ],
    "core_concepts": [
        "distributed systems", "concurrency", "microservices", "b-tree", "caching", 
        "acid", "rest api", "grpc", "sharding", "deep learning", "neural networks", 
        "backpropagation", "gradient descent", "svm", "random forest", 
        "bias-variance", "regularization", "overfitting", "cross-validation"
    ]
}

ROLE_KEYWORDS = {
    "AI/ML Engineer": [
        "pytorch", "tensorflow", "scikit-learn", "deep learning", "neural networks", 
        "rag", "transformers", "huggingface", "llm", "embeddings", "backpropagation", 
        "gradient descent", "computer vision", "nlp", "mlops", "docker"
    ],
    "Backend Engineer": [
        "fastapi", "django", "postgresql", "redis", "docker", "microservices", 
        "concurrency", "distributed systems", "kafka", "rest api", "grpc", "sql", 
        "caching", "acid", "rabbitmq", "kubernetes"
    ],
    "Data Scientist": [
        "python", "pandas", "numpy", "scikit-learn", "statistics", "data analysis", 
        "visualization", "xgboost", "sql", "feature engineering", "cross-validation", 
        "hypothesis testing", "metrics"
    ]
}


class ResumeParserService:
    """Extracts structured candidate profile from PDF or raw text resumes."""

    @staticmethod
    def extract_text_from_pdf_bytes(pdf_bytes: bytes) -> str:
        """Reads plain text content from PDF binary stream."""
        try:
            reader = PdfReader(io.BytesIO(pdf_bytes))
            text_parts = []
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
            return "\n".join(text_parts).strip()
        except Exception as e:
            raise ValueError(f"Failed to parse PDF document: {str(e)}")

    @classmethod
    def parse_resume(cls, text: str, target_role: str = "AI/ML Engineer") -> ResumeParseResult:
        """Analyzes resume text and extracts candidate name, contact, skills, and projects."""
        cleaned_text = re.sub(r'\r\n', '\n', text)
        lines = [line.strip() for line in cleaned_text.split('\n') if line.strip()]

        # 1. Candidate Name (heuristic: first non-empty line without email/phone/url)
        candidate_name = "Candidate"
        for line in lines[:5]:
            if "@" not in line and not re.search(r'\d{3}', line) and len(line) < 40 and not line.lower().startswith("resume"):
                candidate_name = line
                break

        # 2. Extract Contact Info
        email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', cleaned_text)
        candidate_email = email_match.group(0) if email_match else None

        phone_match = re.search(r'(\+?\d{1,3}[-.\s]?)?(\(?\d{3}\)?[-.\s]?)?\d{3}[-.\s]?\d{4}', cleaned_text)
        candidate_phone = phone_match.group(0) if phone_match else None

        # 3. Categorized Skill Extraction
        lower_text = cleaned_text.lower()
        extracted_taxonomy = SkillTaxonomy()
        all_skills = set()

        for category, keywords in SKILL_TAXONOMY.items():
            matched_in_category = []
            for kw in keywords:
                # Use word boundary search
                pattern = r'(?<![a-zA-Z0-9])' + re.escape(kw) + r'(?![a-zA-Z0-9])'
                if re.search(pattern, lower_text):
                    matched_in_category.append(kw)
                    all_skills.add(kw)
            setattr(extracted_taxonomy, category, sorted(list(set(matched_in_category))))

        # 4. Domain & Project Exposure Detection
        domains_detected = []
        domain_keywords = {
            "Retrieval-Augmented Generation (RAG)": ["rag", "vector search", "retrieval-augmented", "embeddings", "chromadb", "faiss"],
            "Natural Language Processing (NLP)": ["nlp", "transformers", "bert", "gpt", "huggingface", "llm", "tokenization"],
            "Computer Vision (CV)": ["opencv", "yolo", "segmentation", "detection", "cnn", "image processing"],
            "High-Throughput Microservices": ["microservices", "grpc", "kafka", "event-driven", "latency", "concurrency"],
            "Database Optimization & Caching": ["indexing", "b-tree", "redis", "cache-aside", "explain analyze", "sharding"],
            "Cloud Infrastructure & MLOps": ["docker", "kubernetes", "ci/cd", "terraform", "mlops", "aws", "gcp"]
        }

        for domain, d_keywords in domain_keywords.items():
            if any(re.search(r'(?<![a-zA-Z0-9])' + re.escape(dkw) + r'(?![a-zA-Z0-9])', lower_text) for dkw in d_keywords):
                domains_detected.append(domain)

        # 5. Extract Project Mentions
        projects_detected = []
        project_patterns = [
            r'(?:project[s]?:?\s*)(.*?)(?=\n\s*(?:experience|education|skills|certifications|$))',
            r'(?:projects\b[\s\S]*?)(?=(?:experience|education|skills|$))'
        ]
        for p in project_patterns:
            match = re.search(p, lower_text, re.IGNORECASE)
            if match:
                proj_lines = [l.strip() for l in match.group(0).split('\n') if len(l.strip()) > 15]
                projects_detected = proj_lines[:4]
                break

        # 6. Experience Level Inference
        experience_level = "Junior / Mid"
        if re.search(r'\b(senior|lead|principal|architect|5\+\s*years|6\+\s*years)\b', lower_text):
            experience_level = "Senior"
        elif re.search(r'\b(intern|student|freshman|graduate|junior|entry-level|0-1\s*year)\b', lower_text):
            experience_level = "Junior / Intern"

        # 7. Alignment score with target role
        target_kw = ROLE_KEYWORDS.get(target_role, ROLE_KEYWORDS["AI/ML Engineer"])
        matched_role_kw = [k for k in target_kw if k in lower_text]
        alignment = len(matched_role_kw) / max(len(target_kw), 1)

        return ResumeParseResult(
            candidate_name=candidate_name,
            email=candidate_email,
            phone=candidate_phone,
            skills=extracted_taxonomy,
            raw_skills_list=sorted(list(all_skills)),
            domains_detected=domains_detected,
            projects_detected=projects_detected,
            experience_level_inferred=experience_level,
            total_characters_parsed=len(cleaned_text),
            matched_role_alignment=round(min(alignment * 1.5, 1.0), 2)
        )
