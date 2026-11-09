/**
 * Screenly - AI Technical Candidate Screening & RAG Interview System
 * Frontend Application Controller
 */

class ScreenlyApp {
  constructor() {
    this.sessionId = null;
    this.currentQuestion = null;
    this.currentCitations = [];
    this.isRecording = false;
    this.recognition = null;
    this.uploadedFile = null;

    this.initElements();
    this.initEvents();
    this.initSpeech();
    this.checkHealth();
  }

  initElements() {
    // Views
    this.setupView = document.getElementById("setup-view");
    this.interviewView = document.getElementById("interview-view");
    this.scorecardView = document.getElementById("scorecard-view");
    this.citationDrawer = document.getElementById("citation-drawer");

    // Inputs
    this.roleSelect = document.getElementById("role-select");
    this.levelSelect = document.getElementById("level-select");
    this.resumeFileInput = document.getElementById("resume-file");
    this.resumeTextInput = document.getElementById("resume-text");
    this.dropZone = document.getElementById("drop-zone");
    this.fileNameDisplay = document.getElementById("file-name-display");
    this.answerText = document.getElementById("answer-text");
    this.charCount = document.getElementById("char-count");

    // Interview UI
    this.headerRoleText = document.getElementById("header-role-text");
    this.roleBadge = document.getElementById("role-badge");
    this.sessionCandidateName = document.getElementById("session-candidate-name");
    this.sessionCandidateRole = document.getElementById("session-candidate-role");
    this.candidateInitial = document.getElementById("candidate-initial");
    this.questionProgressLabel = document.getElementById("question-progress-label");
    this.questionProgressBar = document.getElementById("question-progress-bar");
    this.questionTopicBadge = document.getElementById("question-topic-badge");
    this.questionDifficultyBadge = document.getElementById("question-difficulty-badge");
    this.questionText = document.getElementById("question-text");
    this.questionRationale = document.getElementById("question-rationale");
    this.citationCountBadge = document.getElementById("citation-count-badge");
    this.citationsContent = document.getElementById("citations-content");

    // Evaluation Card
    this.evaluationCard = document.getElementById("evaluation-card");
    this.evalOverallScore = document.getElementById("eval-overall-score");
    this.evalAcc = document.getElementById("eval-acc");
    this.evalDep = document.getElementById("eval-dep");
    this.evalPrac = document.getElementById("eval-prac");
    this.evalClar = document.getElementById("eval-clar");
    this.evalFeedback = document.getElementById("eval-feedback");
    this.followupSection = document.getElementById("followup-section");
    this.followupQuestionText = document.getElementById("followup-question-text");
    this.followupAnswerText = document.getElementById("followup-answer-text");
    this.nextQBtn = document.getElementById("next-q-btn");
    this.nextBtnText = document.getElementById("next-btn-text");

    // Scorecard Elements
    this.cardCandidateName = document.getElementById("card-candidate-name");
    this.cardRoleDisplay = document.getElementById("card-role-display");
    this.cardOverallScore = document.getElementById("card-overall-score");
    this.cardRecommendation = document.getElementById("card-recommendation");
    this.cardVerdict = document.getElementById("card-verdict");
    this.cardAvgAcc = document.getElementById("card-avg-acc");
    this.cardAvgDep = document.getElementById("card-avg-dep");
    this.cardAvgPrac = document.getElementById("card-avg-prac");
    this.cardAvgClar = document.getElementById("card-avg-clar");
    this.cardStrengthsList = document.getElementById("card-strengths-list");
    this.cardGrowthList = document.getElementById("card-growth-list");
    this.transcriptList = document.getElementById("transcript-list");
  }

  initEvents() {
    // Drop zone events
    this.dropZone.addEventListener("click", () => this.resumeFileInput.click());
    this.dropZone.addEventListener("dragover", (e) => {
      e.preventDefault();
      this.dropZone.classList.add("border-indigo-500", "bg-indigo-950/20");
    });
    this.dropZone.addEventListener("dragleave", () => {
      this.dropZone.classList.remove("border-indigo-500", "bg-indigo-950/20");
    });
    this.dropZone.addEventListener("drop", (e) => {
      e.preventDefault();
      this.dropZone.classList.remove("border-indigo-500", "bg-indigo-950/20");
      if (e.dataTransfer.files.length > 0) {
        this.handleFileSelected(e.dataTransfer.files[0]);
      }
    });

    this.resumeFileInput.addEventListener("change", (e) => {
      if (e.target.files.length > 0) {
        this.handleFileSelected(e.target.files[0]);
      }
    });

    // Character counter for answer text
    this.answerText.addEventListener("input", () => {
      const len = this.answerText.value.length;
      this.charCount.innerText = `${len} characters`;
    });

    // Role selection change updates header badge
    this.roleSelect.addEventListener("change", () => {
      this.headerRoleText.innerText = this.roleSelect.value;
    });
  }

  handleFileSelected(file) {
    this.uploadedFile = file;
    this.fileNameDisplay.innerText = `Selected: ${file.name} (${Math.round(file.size / 1024)} KB)`;
    this.fileNameDisplay.classList.remove("hidden");
  }

  async checkHealth() {
    try {
      const res = await fetch("/api/health");
      if (res.ok) {
        const data = await res.json();
        document.getElementById("knowledge-status-text").innerText = `RAG Active (${data.llm_provider})`;
      }
    } catch (e) {
      console.warn("Backend health check failed:", e);
    }
    if (window.lucide) window.lucide.createIcons();
  }

  // Load sample resumes for 1-click testing
  loadSampleResume(type) {
    if (type === "aiml") {
      this.roleSelect.value = "AI/ML Engineer";
      this.headerRoleText.innerText = "AI/ML Engineer";
      this.resumeTextInput.value = `Alex Chen | alex.chen@example.com | San Francisco, CA
Target: AI/ML Engineer
SKILLS: Python, PyTorch, HuggingFace, Scikit-Learn, Docker, FastAPI, RAG, SQL, Backpropagation, Gradient Descent, Vector Embeddings.
PROJECTS:
1. RAG-Based Document Intelligence Engine: Built an end-to-end question answering pipeline over 10k research papers with semantic vector search and hybrid BM25 retrieval.
2. Neural Image Segmentation: Implemented U-Net and DeepLabV3+ in PyTorch, tuning focal loss and learning rate schedules.
EXPERIENCE: ML Intern at NeuroTech Systems - optimized feature selection and hyperparameter pipelines.`;
    } else {
      this.roleSelect.value = "Backend Engineer";
      this.headerRoleText.innerText = "Backend Engineer";
      this.resumeTextInput.value = `Priya Patel | priya.patel@example.com | Seattle, WA
Target: Backend Engineer
SKILLS: Python, Go, FastAPI, PostgreSQL, Redis, Docker, Kafka, RabbitMQ, Microservices, B-Trees, Distributed Locks, ACID, Concurrency.
PROJECTS:
1. Distributed Idempotent Payment Gateway: Designed ACID-compliant transaction service enforcing idempotency keys with Redis distributed locks.
2. Real-Time Collaboration Gateway: Built WebSocket server in Go handling 15k concurrent connections with CRDT convergence.
EXPERIENCE: Backend Intern at ScaleGrid - architected multi-tier caching with Redis using cache-aside pattern, reducing query latency by 60%.`;
    }
    this.fileNameDisplay.innerText = `Loaded Sample: ${type.toUpperCase()}`;
    this.fileNameDisplay.classList.remove("hidden");
  }

  initSpeech() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (SpeechRecognition) {
      this.recognition = new SpeechRecognition();
      this.recognition.continuous = true;
      this.recognition.interimResults = true;
      this.recognition.lang = "en-US";

      this.recognition.onresult = (event) => {
        let transcript = "";
        for (let i = event.resultIndex; i < event.results.length; i++) {
          transcript += event.results[i][0].transcript;
        }
        this.answerText.value += " " + transcript;
        this.charCount.innerText = `${this.answerText.value.length} characters`;
      };

      this.recognition.onerror = (e) => {
        console.error("Speech recognition error:", e);
        this.stopSpeechRecognition();
      };
    }
  }

  toggleSpeechRecognition() {
    if (!this.recognition) {
      alert("Speech recognition is not supported in this browser. Please use Chrome/Edge or type your response.");
      return;
    }
    if (this.isRecording) {
      this.stopSpeechRecognition();
    } else {
      this.startSpeechRecognition();
    }
  }

  startSpeechRecognition() {
    try {
      this.recognition.start();
      this.isRecording = true;
      const micBtn = document.getElementById("mic-btn");
      micBtn.classList.add("bg-red-500/20", "border-red-500", "text-red-400");
      document.getElementById("mic-label").innerText = "Listening...";
    } catch (e) {
      console.error(e);
    }
  }

  stopSpeechRecognition() {
    if (this.recognition && this.isRecording) {
      this.recognition.stop();
      this.isRecording = false;
      const micBtn = document.getElementById("mic-btn");
      micBtn.classList.remove("bg-red-500/20", "border-red-500", "text-red-400");
      document.getElementById("mic-label").innerText = "Voice Input";
    }
  }

  speakQuestion() {
    if (!window.speechSynthesis || !this.currentQuestion) return;
    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(this.currentQuestion.question_text);
    utterance.rate = 1.0;
    utterance.pitch = 1.0;
    window.speechSynthesis.speak(utterance);
  }

  toggleCitations() {
    this.citationDrawer.classList.toggle("hidden");
    if (window.lucide) window.lucide.createIcons();
  }

  // --- INTERVIEW FLOW ---

  async startInterview() {
    const startBtn = document.getElementById("start-btn");
    startBtn.disabled = true;
    startBtn.innerHTML = `<span>Parsing Profile & Loading Knowledge...</span><div class="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>`;

    const formData = new FormData();
    formData.append("target_role", this.roleSelect.value);
    formData.append("experience_level", this.levelSelect.value);

    if (this.uploadedFile) {
      formData.append("resume_file", this.uploadedFile);
    } else if (this.resumeTextInput.value.trim()) {
      formData.append("resume_text", this.resumeTextInput.value.trim());
    } else {
      this.loadSampleResume("aiml");
      formData.append("resume_text", this.resumeTextInput.value.trim());
    }

    try {
      const res = await fetch("/api/sessions/start", {
        method: "POST",
        body: formData
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Failed to start interview session.");
      }

      const session = await res.json();
      this.sessionId = session.id;

      // Update candidate details in UI
      this.sessionCandidateName.innerText = session.candidate_name;
      this.sessionCandidateRole.innerText = `${session.target_role} (${session.experience_level})`;
      this.candidateInitial.innerText = session.candidate_name.charAt(0).toUpperCase();
      this.roleBadge.classList.remove("hidden");
      this.headerRoleText.innerText = session.target_role;

      // Transition Views
      this.setupView.classList.add("hidden");
      this.interviewView.classList.remove("hidden");

      // Fetch first question
      await this.fetchCurrentQuestion();

    } catch (e) {
      alert("Error starting interview: " + e.message);
      startBtn.disabled = false;
      startBtn.innerHTML = `<span>Parse Profile & Start Technical Screening</span><i data-lucide="arrow-right" class="w-4 h-4"></i>`;
      if (window.lucide) window.lucide.createIcons();
    }
  }

  async fetchCurrentQuestion() {
    // Reset inputs & hide evaluation card
    this.answerText.value = "";
    this.charCount.innerText = "0 characters";
    this.evaluationCard.classList.add("hidden");
    this.followupSection.classList.add("hidden");
    document.getElementById("submit-answer-btn").disabled = false;
    document.getElementById("submit-answer-btn").innerHTML = `<span>Submit Answer for Evaluation</span><i data-lucide="send" class="w-4 h-4"></i>`;

    this.questionText.innerText = "Generating context-aware question from knowledge base...";

    try {
      const res = await fetch(`/api/interview/${this.sessionId}/current-question`);
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Failed to load question.");
      }

      const q = await res.json();
      this.currentQuestion = q;
      this.currentCitations = q.grounding_chunks || [];

      // Update progress
      const current = q.question_index + 1;
      const total = q.total_questions;
      this.questionProgressLabel.innerText = `Question ${current} of ${total}`;
      this.questionProgressBar.style.width = `${(current / total) * 100}%`;

      // Update Card
      this.questionTopicBadge.innerText = `Topic: ${q.topic}`;
      this.questionDifficultyBadge.innerText = q.difficulty;
      this.questionText.innerText = q.question_text;
      this.questionRationale.innerText = q.context_rationale || "Synthesized from your declared technical background.";
      this.citationCountBadge.innerText = this.currentCitations.length;

      // Render citations in drawer
      this.renderCitations(this.currentCitations);

      if (window.lucide) window.lucide.createIcons();
    } catch (e) {
      console.error(e);
      alert("Error loading question: " + e.message);
    }
  }

  renderCitations(citations) {
    if (!citations || citations.length === 0) {
      this.citationsContent.innerHTML = `<div class="p-4 rounded-xl bg-slate-950 border border-slate-800 text-xs text-slate-400">Foundational domain concepts referenced.</div>`;
      return;
    }

    this.citationsContent.innerHTML = citations.map((c, i) => `
      <div class="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-2">
        <div class="flex items-center justify-between">
          <span class="text-xs font-bold text-indigo-400 font-mono">[${i+1}] ${c.book_title}</span>
          <span class="text-[10px] font-mono px-2 py-0.5 rounded bg-indigo-500/10 text-indigo-300">Score: ${c.similarity_score}</span>
        </div>
        ${c.chapter_title ? `<p class="text-xs text-slate-300 font-medium">Chapter: ${c.chapter_title}</p>` : ''}
        <p class="text-xs text-slate-400 leading-relaxed italic bg-slate-900/80 p-2.5 rounded-lg border border-slate-800/80">
          "${c.text}"
        </p>
      </div>
    `).join("");
  }

  async submitAnswer() {
    const answer = this.answerText.value.trim();
    if (!answer) {
      alert("Please enter a response before submitting.");
      return;
    }

    this.stopSpeechRecognition();

    const submitBtn = document.getElementById("submit-answer-btn");
    submitBtn.disabled = true;
    submitBtn.innerHTML = `<span>Evaluating Against Multi-Rubric...</span><div class="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>`;

    try {
      const res = await fetch(`/api/interview/${this.sessionId}/submit-answer`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          question_id: this.currentQuestion.id,
          answer_text: answer
        })
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Failed to submit answer.");
      }

      const evalData = await res.json();
      this.displayEvaluation(evalData);

    } catch (e) {
      alert("Submission error: " + e.message);
      submitBtn.disabled = false;
      submitBtn.innerHTML = `<span>Submit Answer for Evaluation</span><i data-lucide="send" class="w-4 h-4"></i>`;
      if (window.lucide) window.lucide.createIcons();
    }
  }

  displayEvaluation(data) {
    this.evalOverallScore.innerText = `${data.score_overall}/10`;
    this.evalAcc.innerText = `${data.score_accuracy}/10`;
    this.evalDep.innerText = `${data.score_depth}/10`;
    this.evalPrac.innerText = `${data.score_practical}/10`;
    this.evalClar.innerText = `${data.score_clarity}/10`;
    this.evalFeedback.innerText = data.feedback;

    this.evaluationCard.classList.remove("hidden");

    if (data.follow_up_triggered && data.follow_up_question) {
      this.followupSection.classList.remove("hidden");
      this.followupQuestionText.innerText = data.follow_up_question;
      this.followupAnswerText.value = "";
      this.nextQBtn.classList.add("hidden");
    } else {
      this.followupSection.classList.add("hidden");
      this.nextQBtn.classList.remove("hidden");

      if (data.session_completed) {
        this.nextBtnText.innerText = "View Final Technical Scorecard";
      } else {
        this.nextBtnText.innerText = "Proceed to Next Question";
      }
    }

    if (window.lucide) window.lucide.createIcons();
    this.evaluationCard.scrollIntoView({ behavior: "smooth" });
  }

  async submitFollowUp() {
    const followupAnswer = this.followupAnswerText.value.trim();
    if (!followupAnswer) {
      alert("Please provide a short elaboration or approach.");
      return;
    }

    try {
      const res = await fetch(`/api/interview/${this.sessionId}/submit-followup`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          question_id: this.currentQuestion.id,
          follow_up_answer: followupAnswer
        })
      });

      if (!res.ok) throw new Error("Failed to submit follow-up response.");
      const updatedData = await res.json();

      this.followupSection.classList.add("hidden");
      this.nextQBtn.classList.remove("hidden");
      this.evalOverallScore.innerText = `${updatedData.score_overall}/10`;
      this.evalFeedback.innerText = updatedData.feedback;

      if (updatedData.session_completed) {
        this.nextBtnText.innerText = "View Final Technical Scorecard";
      } else {
        this.nextBtnText.innerText = "Proceed to Next Question";
      }
    } catch (e) {
      alert("Error submitting follow-up: " + e.message);
    }
  }

  async loadNextQuestion() {
    if (this.nextBtnText.innerText.includes("Scorecard")) {
      await this.loadScorecard();
    } else {
      await this.fetchCurrentQuestion();
    }
  }

  async loadScorecard() {
    try {
      const res = await fetch(`/api/sessions/${this.sessionId}/scorecard`);
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Failed to load scorecard.");
      }

      const report = await res.json();
      this.renderScorecard(report);

      this.interviewView.classList.add("hidden");
      this.scorecardView.classList.remove("hidden");
      window.scrollTo({ top: 0, behavior: "smooth" });

    } catch (e) {
      alert("Scorecard loading error: " + e.message);
    }
  }

  renderScorecard(data) {
    this.cardCandidateName.innerText = data.candidate_name;
    this.cardRoleDisplay.innerText = `Target: ${data.target_role} (${data.experience_level})`;
    this.cardOverallScore.innerText = `${data.overall_score}%`;
    this.cardRecommendation.innerText = data.recommendation;

    // Recommendation badge color
    if (data.overall_score >= 80) {
      this.cardRecommendation.className = "text-sm font-bold text-emerald-400 px-3 py-1 rounded-full bg-emerald-500/20 mt-1 inline-block";
    } else if (data.overall_score >= 65) {
      this.cardRecommendation.className = "text-sm font-bold text-indigo-400 px-3 py-1 rounded-full bg-indigo-500/20 mt-1 inline-block";
    } else {
      this.cardRecommendation.className = "text-sm font-bold text-amber-400 px-3 py-1 rounded-full bg-amber-500/20 mt-1 inline-block";
    }

    this.cardVerdict.innerText = data.summary_verdict;
    this.cardAvgAcc.innerText = `${data.avg_accuracy}/10`;
    this.cardAvgDep.innerText = `${data.avg_depth}/10`;
    this.cardAvgPrac.innerText = `${data.avg_practical}/10`;
    this.cardAvgClar.innerText = `${data.avg_clarity}/10`;

    // Strengths
    this.cardStrengthsList.innerHTML = (data.key_strengths || []).map(s => `
      <li class="flex items-center space-x-2">
        <i data-lucide="check" class="w-3.5 h-3.5 text-emerald-400 flex-shrink-0"></i>
        <span>${s}</span>
      </li>
    `).join("");

    // Growth
    this.cardGrowthList.innerHTML = (data.areas_for_growth || []).map(g => `
      <li class="flex items-center space-x-2">
        <i data-lucide="arrow-up-right" class="w-3.5 h-3.5 text-amber-400 flex-shrink-0"></i>
        <span>${g}</span>
      </li>
    `).join("");

    // Question audit trail
    this.transcriptList.innerHTML = (data.interview_transcript || []).map((t, idx) => `
      <div class="border border-slate-800 rounded-xl p-5 bg-slate-950/70 space-y-3">
        <div class="flex flex-wrap items-center justify-between gap-2">
          <div class="flex items-center space-x-2">
            <span class="px-2 py-0.5 rounded bg-slate-800 text-xs font-mono font-bold text-slate-300">Q${idx + 1}</span>
            <span class="text-xs font-semibold text-indigo-300">${t.topic}</span>
            <span class="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-400">${t.difficulty}</span>
          </div>
          <span class="text-xs font-mono font-bold text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded">Score: ${t.score_overall}/10</span>
        </div>

        <p class="text-xs font-medium text-slate-200">${t.question_text}</p>

        <div class="p-3 rounded-lg bg-slate-900 border border-slate-800/80 text-xs text-slate-300 space-y-1">
          <span class="text-[11px] font-bold text-slate-400 uppercase">Candidate Answer:</span>
          <p class="italic text-slate-300">"${t.candidate_answer}"</p>
        </div>

        ${t.grounding_citations && t.grounding_citations.length > 0 ? `
          <div class="text-[11px] text-slate-400 flex items-center space-x-2">
            <i data-lucide="book" class="w-3.5 h-3.5 text-indigo-400"></i>
            <span><strong>Grounding Textbook:</strong> ${t.grounding_citations[0].book_title} (${t.grounding_citations[0].chapter_title || 'Core'})</span>
          </div>
        ` : ''}

        <p class="text-[11px] text-slate-400"><strong>Feedback:</strong> ${t.feedback}</p>
      </div>
    `).join("");

    if (window.lucide) window.lucide.createIcons();
  }

  resetToSetup() {
    this.sessionId = null;
    this.currentQuestion = null;
    this.currentCitations = [];
    this.scorecardView.classList.add("hidden");
    this.interviewView.classList.add("hidden");
    this.setupView.classList.remove("hidden");
    window.scrollTo({ top: 0, behavior: "smooth" });
  }
}

// Instantiate on load
window.addEventListener("DOMContentLoaded", () => {
  window.app = new ScreenlyApp();
  if (window.lucide) window.lucide.createIcons();
});
