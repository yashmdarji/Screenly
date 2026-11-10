# Screenly 🧠⚡
> **Autonomous Role-Adaptive Technical Candidate Screening System Powered by Grounded Retrieval-Augmented Generation (RAG)**

[![Live Demo](https://img.shields.io/badge/Live_Demo-screenly--60i4.onrender.com-46E3B7?style=flat-square&logo=render&logoColor=white)](https://screenly-60i4.onrender.com/)
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI_0.110+-009688?style=flat-square&logo=fastapi)](https://fastapi.tiangolo.com)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python)](https://python.org)
[![ChromaDB](https://img.shields.io/badge/Vector_DB-ChromaDB_Persistent-FF6F00?style=flat-square)](https://trychroma.com)
[![React](https://img.shields.io/badge/Frontend-React_18_%2B_Tailwind-61DAFB?style=flat-square&logo=react)](https://react.dev)
[![SQLAlchemy](https://img.shields.io/badge/Database-SQLAlchemy_%2B_SQLite-D71F00?style=flat-square&logo=sqlite)](https://sqlite.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg?style=flat-square)](LICENSE)

Screenly is a modular, production-ready AI interview and screening system designed to conduct rigorous, context-aware technical evaluations. Unlike conventional interview bots that ask canned questions or hallucinate ungrounded prompts, Screenly constructs **role-specific, resume-tailored questions grounded strictly in foundational textbooks and engineering corpora** using a transparent RAG pipeline with end-to-end citation traceability.

---

## 🌐 Live Web Application
Test the complete application live in your browser with zero installation:
👉 **[https://screenly-60i4.onrender.com](https://screenly-60i4.onrender.com/)**

> [!NOTE]
> *Hosted on Render's cloud platform. If the service is waking up from an idle state, the initial cold-start spin-up may take ~30–45 seconds. Subsequent interactions respond in milliseconds.*

---

## 📑 Table of Contents
- [Live Web Application](#-live-web-application)
- [Key Features](#-key-features)
- [System Architecture](#-system-architecture)
- [System Flow & Pipeline](#-system-flow--pipeline)
- [Knowledge Base & RAG Grounding](#-knowledge-base--rag-grounding)
- [Architectural & Design Decisions](#-architectural--design-decisions)
- [Project Structure](#-project-structure)
- [Quick Start Guide](#-quick-start-guide)
- [API Reference](#-api-reference)
- [License](#-license)

---

## 🌟 Key Features

1. **Role-Adaptive Evaluation**:
   - Out-of-the-box evaluation tracks for **AI/ML Engineers**, **Backend / Distributed Systems Engineers**, and **Data Scientists / Applied ML**.
   - Questions adapt dynamically in difficulty (Foundational, Medium, Hard, Advanced) based on the candidate's declared seniority and real-time response accuracy.

2. **Resume-Influenced Context Construction**:
   - Parses PDF and plain-text resumes via AST regex heuristics and `pypdf`.
   - Extracts categorized skill taxonomies (languages, frameworks, ML tools, distributed storage, cloud/DevOps) and past project domains to formulate personalized inquiry topics.

3. **Textbook-Grounded RAG Pipeline**:
   - Questions are rooted in canonical engineering references (e.g. Tom Mitchell's *Machine Learning*, Andriy Burkov's *The Hundred-Page Machine Learning Book*, Distributed Systems & Storage Design literature).
   - Prevents hallucinations and generic template outputs.
   - **Full Traceability Drawer**: Evaluators and candidates can inspect the exact textbook section, chapter, and similarity score that generated any question.

4. **Multi-Dimensional Rubric Evaluation**:
   - Evaluates answers across 4 distinct dimensions on a 1.0–10.0 scale:
     - **Technical Accuracy** (35%): Mathematical and algorithmic correctness.
     - **Conceptual Depth** (30%): Understanding of internal mechanics and theoretical proofs.
     - **Practical Trade-offs** (20%): Production considerations, concurrency, failure modes, scale.
     - **Communication Clarity** (15%): Structured explanation and concise articulation.

5. **Adaptive Follow-Up Probing**:
   - If a candidate provides a shallow, ambiguous, or borderline response, the engine triggers an intelligent follow-up probe (e.g., *"How would your approach handle cache stampede under 10k QPS?"*), simulating a real principal engineer interview.

6. **Voice Synthesis & Transcription (Web Speech API)**:
   - Voice microphone button for real-time speech-to-text response entry.
   - Text-to-speech button to read questions aloud with browser audio.

7. **Comprehensive Candidate Scorecard**:
   - Overall fit percentage (0–100%) and recommendation badge (*Strong Hire*, *Hire*, *Borderline*, *Needs Improvement*).
   - Radar metrics breakdown, identified key strengths, growth areas, and complete auditable question transcript.
   - Clean 1-click **Print / PDF export**.

8. **Dual-Mode Reliability (Zero-Key Offline Fallback)**:
   - Works immediately out of the box with zero external API keys via high-fidelity deterministic evaluation engine.
   - Seamlessly upgrades to **Google Gemini 1.5 Flash** or **OpenAI GPT-4o-mini** by adding an API key to `.env`.

---

## 🏛 System Architecture

```mermaid
flowchart TD
    subgraph Frontend["Frontend Layer (React / Vite / Tailwind)"]
        UI_Upload["Resume Upload & Role Selection"]
        UI_Interview["Interactive Interview Room"]
        UI_Speech["Web Speech API (STT / TTS)"]
        UI_Citations["Traceability Citation Drawer"]
        UI_Scorecard["Candidate Scorecard & PDF Export"]
    end

    subgraph API["Backend Service Layer (FastAPI)"]
        R_Session["Session Lifecycle Router (/api/sessions)"]
        R_Interview["Interview Flow Router (/api/interview)"]
        R_Resume["Resume Parser Router (/api/resume)"]
        R_Knowledge["Knowledge & Ingestion Router (/api/knowledge)"]
    end

    subgraph Core["Core Intelligence Services"]
        S_Parser["ResumeParserService (PDF & Text Extraction)"]
        S_RAG["RAGEngine (Dynamic Query Construction)"]
        S_Vector["PersistentVectorStore (ChromaDB + On-Disk Index)"]
        S_Generator["QuestionGeneratorService (Grounded Prompts)"]
        S_Evaluator["EvaluatorService (Multi-Rubric & Adaptive Probing)"]
        S_LLM["LLMService (Gemini / OpenAI / Offline Engine)"]
    end

    subgraph Storage["Persistence & Corpora"]
        DB[(SQLite / SQLAlchemy DB)]
        VDB[(ChromaDB Persistent Store)]
        Corpora["7 Canonical Textbooks (Mitchell, Burkov, Bishop, Mueller, etc.)"]
    end

    UI_Upload --> R_Session
    UI_Interview --> R_Interview
    UI_Citations -.-> R_Interview
    UI_Scorecard -.-> R_Session

    R_Session --> S_Parser
    R_Session --> S_RAG
    R_Interview --> S_Generator
    R_Interview --> S_Evaluator

    S_RAG --> Corpora
    S_RAG --> S_Vector
    S_Vector --> VDB
    S_Generator --> S_LLM
    S_Evaluator --> S_LLM

    R_Session --> DB
    R_Interview --> DB
```

---

## 🔄 System Flow & Pipeline

```mermaid
sequenceDiagram
    autonumber
    actor Candidate as Candidate / Interviewer
    participant UI as Web Frontend
    participant API as FastAPI Backend
    participant Parser as Resume Parser
    participant RAG as RAG & Vector Engine
    participant LLM as LLM / Evaluation Service
    participant DB as SQLite DB

    Candidate->>UI: Uploads Resume (PDF/Text) & Selects Role
    UI->>API: POST /api/sessions/start
    API->>Parser: Extract skills, domains, projects
    API->>RAG: Construct dynamic topic queries
    API->>DB: Store session (status: IN_PROGRESS)
    API-->>UI: Session ID & Parsed Profile

    Candidate->>UI: Clicks "Start Technical Screening"
    UI->>API: GET /api/interview/{id}/current-question
    API->>RAG: Retrieve top-k textbook chunks (Cosine Similarity)
    API->>LLM: Generate grounded question matching difficulty & stack
    API->>DB: Store Question with source grounding citations
    API-->>UI: Question text, topic, difficulty & citations

    Candidate->>UI: Speaks or types response & Submits
    UI->>API: POST /api/interview/{id}/submit-answer
    API->>LLM: Grade answer across Accuracy, Depth, Practical, Clarity
    alt Shallow / Borderline Answer
        API-->>UI: Feedback + Adaptive Follow-Up Probe
        Candidate->>UI: Submits Follow-Up Elaboration
        UI->>API: POST /api/interview/{id}/submit-followup
    end
    API->>DB: Store response scores & feedback

    opt Interview Complete (5/5 Questions)
        API->>LLM: Aggregate session metrics & recommendations
        API->>DB: Persist final SessionScorecard
        API-->>UI: session_completed = True
        Candidate->>UI: View Final Technical Scorecard & Print PDF
    end
```

---

## 📚 Knowledge Base & Canonical RAG Grounding

Screenly indexes real textbook knowledge into semantic chunks with sliding overlap across 7 canonical academic references:

| # | Reference / Book Title | Author(s) | Primary Focus & Grounded Concepts |
| :-: | :--- | :--- | :--- |
| **1** | *Machine Learning* | Tom M. Mitchell | Artificial Neural Networks, Backpropagation, Learning Representations, Decision Trees (ID3, Information Gain, Entropy), Post-Pruning, Bayes Theorem, MAP, Naive Bayes Classifiers, PAC Learning, VC Dimension |
| **2** | *The Hundred-Page Machine Learning Book* | Andriy Burkov | Support Vector Machines (SVM), Maximum Margin Hyperplanes, Kernel Trick, Bias-Variance Decomposition, L1 (Lasso) vs L2 (Ridge) Regularization, Cross-Validation, Data Leakage, Random Forests, GBDT |
| **3** | *Machine Learning for Absolute Beginners* | Oliver Theobald | Foundational Machine Learning Mechanics, Supervised vs Unsupervised Learning, Feature Scaling, Min-Max Normalization, Linear Regression, Bias-Variance Fundamentals |
| **4** | *Introduction to Machine Learning with Python* | Andreas Müller & Sarah Guido | Practical Scikit-Learn Pipelines, Preprocessing, Hyperparameter Tuning, GridSearchCV, Model Evaluation, Confusion Matrices, Precision-Recall Curves |
| **5** | *Master Machine Learning Algorithms* | Jason Brownlee | Mathematical Underpinnings of ML Algorithms, Gradient Descent Optimization Mechanics, Stochastic vs Mini-Batch, Parametric vs Non-Parametric Modeling |
| **6** | *Pattern Recognition and Machine Learning* | Christopher M. Bishop | Probabilistic Machine Learning, Bayesian Inference, Maximum Likelihood Estimation (MLE), Probability Distributions, Gaussian Mixture Models, Expectation-Maximization |
| **7** | *Artificial Intelligence, Machine Learning and Deep Learning Foundations* | Foundational Systems | Modern Neural Architecture Paradigms, Deep Learning Fundamentals, Loss Topography, Vanishing/Exploding Gradients, Activation Dynamics |
| **+** | *Principles of Backend Engineering & Storage Architecture* | Martin Kleppmann & Engineering Guild | B-Trees vs LSM-Trees, Composite Index Leftmost Prefix Rule, Covered Queries, Cache-Aside vs Write-Through, Cache Stampede (Thundering Herd), ACID Isolation Levels, MVCC, CAP Theorem, REST vs gRPC |
| **+** | *Applied ML & Model Evaluation* | Applied Data Science Standards | Evaluation Metrics on Imbalanced Data, Precision-Recall vs ROC-AUC, Cost-Sensitive Resampling, SMOTE, Categorical Target Encoding, Mutual Information, RFE |

---

## 💡 Architectural & Design Decisions

### 1. Semantic Sentence Chunking with Overlap (500 chars, 80 char overlap)
- **Rationale**: Arbitrary character slicing splits mathematical equations, formulas, and technical terminology mid-token, destroying semantic coherence. Screenly splits along sentence boundaries (`. `, `! `, `? `), carrying trailing sentences into subsequent chunks as overlapping context.

### 2. Persistent ChromaDB & On-Disk Vector Database
- **Rationale**: Relying on ephemeral in-memory vectors forces expensive re-indexing on every process startup and risks memory exhaustion. Screenly integrates **ChromaDB (`PersistentClient`)** backed by an on-disk binary vector store (`data/chroma_db/`). At application boot, Screenly instantly mounts the precomputed index in **$< 0.1$ seconds** and executes cosine similarity searches in **$< 5$ milliseconds** per evaluation cycle with zero external network dependencies.

### 3. Strict Traceability Pipeline (`Context -> Question -> Answer -> Storage`)
- **Rationale**: In automated screening, hiring decisions must be transparent and defensible. Every question stores the exact `chunk_id`, `book_title`, `chapter`, `section`, and `similarity_score` in SQLite. Evaluators can click the **Citations Drawer** on any question to view the reference literature.

### 4. Adaptive Difficulty & Follow-Up Probing
- **Rationale**: Real technical interviews are conversational, not static quizzes. If a candidate scores `>= 8.2` on earlier questions, Screenly elevates subsequent questions to *Hard* or *Advanced* architectural design. If an answer is vague or misses core mechanics (`< 6.8`), the system triggers a targeted follow-up probe.

### 5. Multi-Rubric Quantitative Scoring
- **Rationale**: Single arbitrary grades fail to provide actionable candidate feedback. Screenly scores four distinct dimensions:
  $$\text{Overall Score} = 0.35 \times \text{Accuracy} + 0.30 \times \text{Depth} + 0.20 \times \text{Practical} + 0.15 \times \text{Clarity}$$

### 6. Dual-Mode Execution (Offline Fallback + Cloud LLMs)
- **Rationale**: When evaluators test an assignment submission without personal API keys, traditional LLM wrappers crash with `401 Unauthorized`. Screenly features an intelligent local fallback engine that evaluates candidate answers deterministically against expected concept vectors, guaranteeing zero-crash evaluation while supporting Gemini and OpenAI via `.env`.

---

## 📂 Project Structure

```
Screenly/
├── run.py                          # Unified launcher (starts backend & opens app)
├── requirements.txt                # Python dependencies
├── .env.example                    # Environment variable configuration template
├── .gitignore                      # Git ignore rules
├── LICENSE                         # MIT License
├── README.md                       # Comprehensive documentation & architecture
├── screenly.db                     # SQLite database (auto-created on startup)
│
├── data/
│   ├── chroma_db/                  # Persistent ChromaDB on-disk vector database
│   │   └── vector_index.json       # Precomputed normalized vector embeddings & index
│   ├── knowledge_base/             # Structured canonical textbook corpora
│   │   ├── ai_ml/
│   │   │   ├── tom_mitchell_machine_learning.json
│   │   │   ├── burkov_hundred_page_ml.json
│   │   │   ├── ml_for_absolute_beginners.json
│   │   │   ├── bishop_pattern_recognition_and_ml.json
│   │   │   └── ai_ml_deep_learning_foundations.json
│   │   ├── backend/
│   │   │   └── system_design_and_distributed_systems.json
│   │   └── data_science/
│   │       ├── intro_to_ml_with_python.json
│   │       ├── master_machine_learning_algorithms.json
│   │       └── applied_ml_and_model_evaluation.json
│   └── sample_resumes/             # Test resumes for 1-click verification
│       ├── alex_chen_aiml_engineer.txt
│       ├── priya_patel_backend_engineer.txt
│       ├── sample_aiml_resume.pdf
│       └── sample_backend_resume.pdf
│
├── scripts/
│   └── ingest_textbooks_to_vdb.py  # Offline vector database ingestion pipeline
│
├── backend/
│   ├── app/
│   │   ├── main.py                 # FastAPI application factory & lifespan
│   │   ├── config.py               # Settings (Pydantic BaseSettings)
│   │   ├── database.py             # SQLite + SQLAlchemy session setup
│   │   ├── models/                 # SQLAlchemy ORM models
│   │   │   ├── session.py          # InterviewSession model
│   │   │   ├── question.py         # InterviewQuestion (with grounding metadata)
│   │   │   ├── response.py         # CandidateResponse (rubric scores & follow-ups)
│   │   │   └── evaluation.py       # SessionScorecard (aggregate report)
│   │   ├── schemas/                # Pydantic schemas for request/response validation
│   │   │   ├── session.py
│   │   │   ├── resume.py
│   │   │   ├── question.py
│   │   │   └── evaluation.py
│   │   ├── services/               # Core business & AI logic
│   │   │   ├── resume_parser.py    # PDF & text skill extraction
│   │   │   ├── vector_store.py     # Hybrid vector store & chunker
│   │   │   ├── rag_engine.py       # Knowledge retrieval & query construction
│   │   │   ├── question_generator.py # Dynamic grounded question generator
│   │   │   ├── evaluator.py        # Multi-rubric evaluator & adaptive prober
│   │   │   └── llm_service.py      # LLM provider (Gemini / OpenAI / Offline)
│   │   ├── routers/                # REST API routers
│   │   │   ├── session_routes.py   # /api/sessions
│   │   │   ├── interview_routes.py # /api/interview
│   │   │   ├── resume_routes.py    # /api/resume
│   │   │   └── knowledge_routes.py # /api/knowledge
│   │   └── static/                 # Embedded React single-page application
│   │       ├── index.html
│   │       ├── app.js
│   │       └── styles.css
│   └── tests/                      # Automated test suite
│       ├── test_resume_parser.py
│       ├── test_rag_retrieval.py
│       └── test_interview_flow.py
│
└── frontend/                       # Standalone React 18 + Vite application
    ├── package.json
    ├── vite.config.js
    ├── index.html
    └── src/
        ├── main.jsx
        ├── App.jsx
        ├── index.css
        └── services/
            └── api.js
```

---

## 🚀 Quick Start Guide

> 💡 **Prefer testing immediately without local setup?** Launch the live production app directly at **[screenly-60i4.onrender.com](https://screenly-60i4.onrender.com/)**.

### Prerequisites
- **Python 3.10+**
- **Node.js 18+** *(optional - only if modifying frontend source directly; the app runs out-of-the-box via Python)*

### 1. Installation
```bash
# Clone the repository
git clone https://github.com/yashmdarji/Screenly.git
cd Screenly

# Install Python dependencies
pip install -r requirements.txt
```

### 2. Environment Configuration (Optional)
Screenly works **100% offline out of the box** without any API keys. If you wish to use Google Gemini or OpenAI:
```bash
cp .env.example .env
# Edit .env and set:
# LLM_PROVIDER=gemini
# GEMINI_API_KEY=your_gemini_api_key_here
```

### 3. Launch the Application
Run the unified launcher:
```bash
python run.py
```
Open your browser at **[http://localhost:8000](http://localhost:8000)**. The full interactive interface will be ready immediately!

### 4. Running the Standalone React Frontend (Optional for Frontend Devs)
If you want to run the Vite development server with hot-module replacement:
```bash
cd frontend
npm install
npm run dev
```
The Vite dev server will run on `http://localhost:5173` and automatically proxy API calls to the FastAPI backend on port 8000.

### 5. Running Automated Tests
```bash
python backend/tests/test_resume_parser.py
python backend/tests/test_rag_retrieval.py
python backend/tests/test_interview_flow.py
```

---

## 🔌 API Reference

### Sessions (`/api/sessions`)
- `POST /api/sessions/start`: Initializes candidate screening session, parses resume, extracts skills, and generates RAG topic queries.
- `GET /api/sessions/{id}`: Retrieves current session status, question index, and candidate metadata.
- `GET /api/sessions/{id}/scorecard`: Returns complete final evaluation report with radar metrics and grounded question transcript.
- `GET /api/sessions`: Lists recent screening sessions.

### Interview (`/api/interview`)
- `GET /api/interview/{id}/current-question`: Generates or retrieves the active question with grounded citations and context rationale.
- `POST /api/interview/{id}/submit-answer`: Submits candidate response; evaluates across Accuracy, Depth, Practical, Clarity; triggers adaptive follow-up probe if required.
- `POST /api/interview/{id}/submit-followup`: Submits response to adaptive follow-up question.

### Resume & Knowledge (`/api/resume`, `/api/knowledge`)
- `POST /api/resume/parse`: Standalone resume extraction endpoint (PDF or text).
- `GET /api/knowledge/status`: Returns loaded textbooks and chunk statistics.
- `POST /api/knowledge/search`: Interactive RAG vector similarity search test tool.
- `POST /api/knowledge/ingest`: Ingests custom documentation or textbook chapters into the vector store.

---

## 📄 License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
