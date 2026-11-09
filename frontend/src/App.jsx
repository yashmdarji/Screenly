import React, { useState, useEffect } from 'react';
import {
  BrainCircuit,
  Briefcase,
  UploadCloud,
  ArrowRight,
  BookOpen,
  Mic,
  Send,
  Volume2,
  CheckCircle,
  AlertCircle,
  Award,
  Printer,
  RotateCcw,
  Sparkles,
  X
} from 'lucide-react';
import * as api from './services/api';

export default function App() {
  const [stage, setStage] = useState('setup'); // 'setup', 'interview', 'scorecard'
  const [role, setRole] = useState('AI/ML Engineer');
  const [level, setLevel] = useState('Mid-Level');
  const [resumeText, setResumeText] = useState('');
  const [resumeFile, setResumeFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [healthStatus, setHealthStatus] = useState('Checking...');

  // Interview state
  const [session, setSession] = useState(null);
  const [currentQuestion, setCurrentQuestion] = useState(null);
  const [answer, setAnswer] = useState('');
  const [evalResult, setEvalResult] = useState(null);
  const [followUpAnswer, setFollowUpAnswer] = useState('');
  const [isRecording, setIsRecording] = useState(false);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [scorecard, setScorecard] = useState(null);
  const [ttsStatus, setTtsStatus] = useState('idle'); // 'idle', 'speaking', 'paused'

  useEffect(() => {
    api.checkBackendHealth()
      .then(d => setHealthStatus(`RAG Active (${d.llm_provider})`))
      .catch(() => setHealthStatus('Offline Mode'));
  }, []);

  const loadSample = (type) => {
    if (type === 'aiml') {
      setRole('AI/ML Engineer');
      setResumeText(`Alex Chen | alex.chen@example.com
Target: AI/ML Engineer
SKILLS: Python, PyTorch, HuggingFace, Scikit-Learn, Docker, FastAPI, RAG, SQL, Backpropagation, Gradient Descent.
PROJECTS:
1. RAG-Based Document Intelligence Engine: Question answering over 10k research papers with semantic vector search.
2. Neural Image Segmentation: PyTorch U-Net with focal loss and cosine annealing schedule.`);
    } else {
      setRole('Backend Engineer');
      setResumeText(`Priya Patel | priya.patel@example.com
Target: Backend Engineer
SKILLS: Python, Go, FastAPI, PostgreSQL, Redis, Docker, Kafka, RabbitMQ, Microservices, B-Trees, Distributed Locks, ACID.
PROJECTS:
1. Distributed Idempotent Payment Gateway: ACID transactions with Redis distributed locks.
2. High-throughput WebSocket Gateway: Go goroutines handling 15k concurrent connections.`);
    }
  };

  const handleStart = async () => {
    setLoading(true);
    try {
      const fd = new FormData();
      fd.append('target_role', role);
      fd.append('experience_level', level);
      if (resumeFile) {
        fd.append('resume_file', resumeFile);
      } else if (resumeText.trim()) {
        fd.append('resume_text', resumeText.trim());
      } else {
        loadSample('aiml');
        fd.append('resume_text', 'Alex Chen\nSkills: Python, PyTorch, Docker, Machine Learning');
      }

      const s = await api.startInterviewSession(fd);
      setSession(s);
      setStage('interview');
      await fetchQuestion(s.id);
    } catch (e) {
      alert('Error starting session: ' + e.message);
    } finally {
      setLoading(false);
    }
  };

  const fetchQuestion = async (sid) => {
    setAnswer('');
    setEvalResult(null);
    setFollowUpAnswer('');
    try {
      const q = await api.getCurrentQuestion(sid);
      setCurrentQuestion(q);
    } catch (e) {
      alert('Error fetching question: ' + e.message);
    }
  };

  const handleSubmitAnswer = async () => {
    if (!answer.trim()) {
      alert('Please enter an answer.');
      return;
    }
    setLoading(true);
    try {
      const res = await api.submitAnswer(session.id, currentQuestion.id, answer);
      setEvalResult(res);
    } catch (e) {
      alert('Submission error: ' + e.message);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmitFollowUp = async () => {
    if (!followUpAnswer.trim()) {
      alert('Please provide an elaboration.');
      return;
    }
    setLoading(true);
    try {
      const res = await api.submitFollowUp(session.id, currentQuestion.id, followUpAnswer);
      setEvalResult(res);
    } catch (e) {
      alert('Follow-up error: ' + e.message);
    } finally {
      setLoading(false);
    }
  };

  const handleNextStep = async () => {
    if (evalResult?.session_completed) {
      setLoading(true);
      try {
        const sc = await api.getSessionScorecard(session.id);
        setScorecard(sc);
        setStage('scorecard');
      } catch (e) {
        alert('Scorecard error: ' + e.message);
      } finally {
        setLoading(false);
      }
    } else {
      await fetchQuestion(session.id);
    }
  };

  const handlePlayTTS = () => {
    if (!window.speechSynthesis || !currentQuestion) return;
    window.speechSynthesis.cancel();
    const u = new SpeechSynthesisUtterance(currentQuestion.question_text);
    u.onstart = () => setTtsStatus('speaking');
    u.onpause = () => setTtsStatus('paused');
    u.onresume = () => setTtsStatus('speaking');
    u.onend = () => setTtsStatus('idle');
    u.onerror = () => setTtsStatus('idle');
    window.speechSynthesis.speak(u);
  };

  const handlePauseResumeTTS = () => {
    if (!window.speechSynthesis) return;
    if (window.speechSynthesis.speaking) {
      if (window.speechSynthesis.paused) {
        window.speechSynthesis.resume();
        setTtsStatus('speaking');
      } else {
        window.speechSynthesis.pause();
        setTtsStatus('paused');
      }
    } else {
      handlePlayTTS();
    }
  };

  const handleStopTTS = () => {
    if (!window.speechSynthesis) return;
    window.speechSynthesis.cancel();
    setTtsStatus('idle');
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-['Plus_Jakarta_Sans',sans-serif]">
      {/* Header */}
      <header className="border-b border-slate-800/80 bg-slate-900/60 backdrop-blur-md sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-4 h-16 flex items-center justify-between">
          <div className="flex items-center space-x-3 cursor-pointer" onClick={() => setStage('setup')}>
            <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-indigo-500 to-purple-500 flex items-center justify-center shadow-lg shadow-indigo-500/20">
              <BrainCircuit className="w-5 h-5 text-white" />
            </div>
            <div>
              <span className="text-xl font-extrabold tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-white via-slate-200 to-slate-400">Screenly</span>
              <span className="text-xs ml-1.5 px-2 py-0.5 rounded-full bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 font-mono">RAG Grounded</span>
            </div>
          </div>
          <div className="flex items-center space-x-3 text-xs font-mono text-slate-400 bg-slate-900 px-3 py-1.5 rounded-lg border border-slate-800">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
            <span>{healthStatus}</span>
          </div>
        </div>
      </header>

      {/* Main Body */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 py-8">
        
        {/* SETUP STAGE */}
        {stage === 'setup' && (
          <div className="space-y-8 max-w-4xl mx-auto">
            <div className="text-center space-y-2">
              <h1 className="text-3xl sm:text-4xl font-extrabold text-white">Role-Adaptive Technical Screening</h1>
              <p className="text-slate-400 text-sm">Grounded technical interviews dynamically synthesized from textbook knowledge bases and candidate resumes.</p>
            </div>

            <div className="bg-slate-900/50 border border-slate-800 rounded-2xl p-6 sm:p-8 space-y-6">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-400 mb-2 uppercase">Target Job Role</label>
                  <select value={role} onChange={(e) => setRole(e.target.value)} className="w-full bg-slate-950 border border-slate-700 rounded-xl px-4 py-3 text-sm text-white focus:outline-none focus:border-indigo-500">
                    <option value="AI/ML Engineer">AI / Machine Learning Engineer</option>
                    <option value="Backend Engineer">Backend / Distributed Systems</option>
                    <option value="Data Scientist">Data Science / Applied ML</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-400 mb-2 uppercase">Experience Level</label>
                  <select value={level} onChange={(e) => setLevel(e.target.value)} className="w-full bg-slate-950 border border-slate-700 rounded-xl px-4 py-3 text-sm text-white focus:outline-none focus:border-indigo-500">
                    <option value="Junior / Intern">Junior / Intern</option>
                    <option value="Mid-Level">Mid-Level</option>
                    <option value="Senior">Senior</option>
                  </select>
                </div>
              </div>

              <div>
                <div className="flex items-center justify-between mb-2">
                  <label className="text-xs font-semibold text-slate-400 uppercase">Candidate Resume</label>
                  <div className="flex space-x-2 text-xs text-indigo-400">
                    <button type="button" onClick={() => loadSample('aiml')} className="hover:underline">Sample AI/ML</button>
                    <span>|</span>
                    <button type="button" onClick={() => loadSample('backend')} className="hover:underline">Sample Backend</button>
                  </div>
                </div>

                <textarea
                  value={resumeText}
                  onChange={(e) => setResumeText(e.target.value)}
                  rows={5}
                  placeholder="Paste resume text or click sample above..."
                  className="w-full bg-slate-950 border border-slate-700 rounded-xl p-3 text-xs font-mono text-slate-200 focus:outline-none focus:border-indigo-500"
                />
              </div>

              <button
                disabled={loading}
                onClick={handleStart}
                className="w-full py-4 rounded-xl bg-gradient-to-r from-indigo-500 to-purple-600 hover:from-indigo-600 hover:to-purple-700 text-white font-bold text-sm flex items-center justify-center space-x-2 shadow-lg shadow-indigo-500/25"
              >
                <span>{loading ? 'Processing Resume & Grounding Context...' : 'Start Technical Screening'}</span>
                <ArrowRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        )}

        {/* INTERVIEW STAGE */}
        {stage === 'interview' && currentQuestion && (
          <div className="max-w-4xl mx-auto space-y-6">
            <div className="flex items-center justify-between bg-slate-900/60 border border-slate-800 p-4 rounded-2xl">
              <div>
                <h3 className="text-sm font-bold text-white">{session?.candidate_name}</h3>
                <p className="text-xs text-slate-400">{session?.target_role}</p>
              </div>
              <div className="text-right">
                <span className="text-xs font-mono text-slate-300 font-semibold">Question {currentQuestion.question_index + 1} of {currentQuestion.total_questions}</span>
                <div className="w-32 bg-slate-800 h-2 rounded-full overflow-hidden mt-1">
                  <div className="bg-indigo-500 h-full" style={{ width: `${((currentQuestion.question_index + 1) / currentQuestion.total_questions) * 100}%` }}></div>
                </div>
              </div>
            </div>

            <div className="bg-slate-900/70 border border-slate-800 rounded-2xl p-6 sm:p-8 space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex space-x-2">
                  <span className="px-3 py-1 rounded-full text-xs font-semibold bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">{currentQuestion.topic}</span>
                  <span className="px-2.5 py-1 rounded-full text-xs font-mono bg-amber-500/10 text-amber-400 border border-amber-500/20">{currentQuestion.difficulty}</span>
                </div>
                <button onClick={() => setDrawerOpen(true)} className="flex items-center space-x-1.5 text-xs text-indigo-300 bg-slate-800 px-3 py-1.5 rounded-lg border border-slate-700">
                  <BookOpen className="w-3.5 h-3.5" />
                  <span>Citations ({currentQuestion.grounding_chunks?.length || 0})</span>
                </button>
              </div>

              <h2 className="text-lg font-semibold text-slate-100 leading-relaxed">{currentQuestion.question_text}</h2>

              {/* TTS Audio Controls */}
              <div className="flex items-center justify-between pt-3 border-t border-slate-800/80 bg-slate-950/40 p-2.5 rounded-xl border border-slate-800/60">
                <div className="flex items-center space-x-2">
                  <span className="text-xs font-semibold text-slate-400 flex items-center space-x-1.5">
                    <Volume2 className="w-4 h-4 text-indigo-400" />
                    <span>AI Voice:</span>
                  </span>
                  <span className={`text-[11px] font-mono px-2 py-0.5 rounded ${ttsStatus === 'speaking' ? 'bg-indigo-500/20 text-indigo-300 border border-indigo-500/40 animate-pulse' : ttsStatus === 'paused' ? 'bg-amber-500/20 text-amber-300 border border-amber-500/40' : 'bg-slate-900 text-slate-400 border border-slate-800'}`}>
                    {ttsStatus === 'speaking' ? 'Speaking...' : ttsStatus === 'paused' ? 'Paused' : 'Idle'}
                  </span>
                </div>
                <div className="flex items-center space-x-1.5">
                  <button onClick={handlePlayTTS} className="px-2.5 py-1 rounded-lg bg-indigo-600/30 hover:bg-indigo-600/50 text-indigo-200 border border-indigo-500/40 text-xs">
                    Play
                  </button>
                  <button onClick={handlePauseResumeTTS} className="px-2.5 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 text-xs">
                    {ttsStatus === 'paused' ? 'Resume' : 'Pause'}
                  </button>
                  <button onClick={handleStopTTS} className="px-2.5 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 text-xs">
                    Reset
                  </button>
                </div>
              </div>
            </div>

            {/* Answer Input */}
            <div className="bg-slate-900/50 border border-slate-800 rounded-2xl p-6 space-y-4">
              <label className="text-sm font-bold text-white">Your Technical Response</label>
              <textarea
                value={answer}
                onChange={(e) => setAnswer(e.target.value)}
                rows={6}
                placeholder="Explain the theoretical foundations, implementation mechanisms, and practical trade-offs..."
                className="w-full bg-slate-950 border border-slate-700 rounded-xl p-4 text-sm text-slate-200 focus:outline-none focus:border-indigo-500"
              />
              <button
                disabled={loading}
                onClick={handleSubmitAnswer}
                className="w-full py-3.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-sm flex items-center justify-center space-x-2"
              >
                <span>{loading ? 'Evaluating Response...' : 'Submit Answer'}</span>
                <Send className="w-4 h-4" />
              </button>
            </div>

            {/* Live Evaluation Card */}
            {evalResult && (
              <div className="bg-slate-900 border border-indigo-500/30 rounded-2xl p-6 space-y-4">
                <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                  <span className="font-bold text-white">Evaluation Score</span>
                  <span className="text-emerald-400 font-mono font-bold text-lg">{evalResult.score_overall}/10</span>
                </div>
                <div className="grid grid-cols-4 gap-2 text-center text-xs">
                  <div className="p-2 bg-slate-950 rounded-lg">Accuracy: <span className="font-bold text-indigo-400">{evalResult.score_accuracy}</span></div>
                  <div className="p-2 bg-slate-950 rounded-lg">Depth: <span className="font-bold text-purple-400">{evalResult.score_depth}</span></div>
                  <div className="p-2 bg-slate-950 rounded-lg">Practical: <span className="font-bold text-emerald-400">{evalResult.score_practical}</span></div>
                  <div className="p-2 bg-slate-950 rounded-lg">Clarity: <span className="font-bold text-amber-400">{evalResult.score_clarity}</span></div>
                </div>
                <p className="text-xs text-slate-300 leading-relaxed bg-slate-950 p-3 rounded-xl">{evalResult.feedback}</p>

                {/* Adaptive follow up probe */}
                {evalResult.follow_up_triggered && evalResult.follow_up_question && (
                  <div className="p-4 bg-amber-500/10 border border-amber-500/30 rounded-xl space-y-2">
                    <span className="text-xs font-bold text-amber-400 uppercase">Adaptive Follow-up Probe</span>
                    <p className="text-xs text-amber-100">{evalResult.follow_up_question}</p>
                    <textarea
                      value={followUpAnswer}
                      onChange={(e) => setFollowUpAnswer(e.target.value)}
                      rows={2}
                      placeholder="Elaborate on this specific mechanism..."
                      className="w-full bg-slate-950 border border-amber-500/30 rounded-xl p-2 text-xs text-slate-200"
                    />
                    <button onClick={handleSubmitFollowUp} className="px-3 py-1.5 rounded-lg bg-amber-500 text-slate-950 font-bold text-xs">
                      Submit Follow-up
                    </button>
                  </div>
                )}

                {(!evalResult.follow_up_triggered || !evalResult.follow_up_question) && (
                  <button onClick={handleNextStep} className="w-full py-3 rounded-xl bg-slate-800 hover:bg-slate-700 text-white font-bold text-xs flex items-center justify-center space-x-2">
                    <span>{evalResult.session_completed ? 'View Technical Scorecard' : 'Next Question'}</span>
                    <ArrowRight className="w-4 h-4" />
                  </button>
                )}
              </div>
            )}
          </div>
        )}

        {/* SCORECARD STAGE */}
        {stage === 'scorecard' && scorecard && (
          <div className="max-w-4xl mx-auto space-y-6">
            <div className="bg-gradient-to-br from-indigo-950/80 to-purple-950/80 border border-indigo-500/30 rounded-3xl p-8 space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <h1 className="text-2xl font-extrabold text-white">{scorecard.candidate_name}</h1>
                  <p className="text-xs text-slate-400">{scorecard.target_role} ({scorecard.experience_level})</p>
                </div>
                <div className="text-right">
                  <span className="text-3xl font-black font-mono text-emerald-400">{scorecard.overall_score}%</span>
                  <span className="block text-xs font-bold text-indigo-300 mt-1">{scorecard.recommendation}</span>
                </div>
              </div>
              <p className="text-xs text-slate-200 border-t border-slate-800/80 pt-3">{scorecard.summary_verdict}</p>
            </div>

            <div className="grid grid-cols-4 gap-3 text-center text-xs">
              <div className="p-4 bg-slate-900 border border-slate-800 rounded-xl">Accuracy: <p className="text-lg font-bold text-indigo-400 mt-1">{scorecard.avg_accuracy}/10</p></div>
              <div className="p-4 bg-slate-900 border border-slate-800 rounded-xl">Depth: <p className="text-lg font-bold text-purple-400 mt-1">{scorecard.avg_depth}/10</p></div>
              <div className="p-4 bg-slate-900 border border-slate-800 rounded-xl">Applied: <p className="text-lg font-bold text-emerald-400 mt-1">{scorecard.avg_practical}/10</p></div>
              <div className="p-4 bg-slate-900 border border-slate-800 rounded-xl">Clarity: <p className="text-lg font-bold text-amber-400 mt-1">{scorecard.avg_clarity}/10</p></div>
            </div>

            <div className="space-y-3">
              <h3 className="text-sm font-bold text-white">Full Interview Transcript & Grounding</h3>
              {scorecard.interview_transcript?.map((t, idx) => (
                <div key={idx} className="p-4 bg-slate-900/60 border border-slate-800 rounded-xl space-y-2 text-xs">
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-indigo-300">Q{idx + 1}: {t.topic}</span>
                    <span className="font-mono text-emerald-400 font-bold">{t.score_overall}/10</span>
                  </div>
                  <p className="text-slate-200">{t.question_text}</p>
                  <p className="italic text-slate-400 bg-slate-950 p-2 rounded">"{t.candidate_answer}"</p>
                  <p className="text-slate-400"><strong>Feedback:</strong> {t.feedback}</p>
                </div>
              ))}
            </div>

            <div className="flex justify-between pt-4 border-t border-slate-800">
              <button onClick={() => window.print()} className="px-4 py-2 bg-slate-800 text-xs rounded-xl flex items-center space-x-2">
                <Printer className="w-4 h-4" />
                <span>Print PDF</span>
              </button>
              <button onClick={() => setStage('setup')} className="px-5 py-2 bg-indigo-600 font-bold text-xs rounded-xl flex items-center space-x-2">
                <RotateCcw className="w-4 h-4" />
                <span>Start New Screening</span>
              </button>
            </div>
          </div>
        )}

      </main>

      {/* Citations Drawer */}
      {drawerOpen && (
        <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-sm flex justify-end">
          <div className="w-full max-w-lg bg-slate-900 border-l border-slate-800 h-full p-6 overflow-y-auto space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h3 className="font-bold text-white text-sm">Grounded Textbook Citations</h3>
              <button onClick={() => setDrawerOpen(false)}><X className="w-5 h-5 text-slate-400" /></button>
            </div>
            {currentQuestion?.grounding_chunks?.map((c, i) => (
              <div key={i} className="p-3 bg-slate-950 border border-slate-800 rounded-xl text-xs space-y-1">
                <span className="font-bold text-indigo-400 font-mono">[{i+1}] {c.book_title}</span>
                <p className="text-slate-300 font-semibold">{c.chapter_title}</p>
                <p className="text-slate-400 italic">"{c.text}"</p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
