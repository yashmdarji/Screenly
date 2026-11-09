const API_BASE = '/api';

export async function checkBackendHealth() {
  const res = await fetch(`${API_BASE}/health`);
  return res.json();
}

export async function startInterviewSession(formData) {
  const res = await fetch(`${API_BASE}/sessions/start`, {
    method: 'POST',
    body: formData,
  });
  if (!res.ok) {
    const error = await res.json();
    throw new Error(error.detail || 'Failed to start interview.');
  }
  return res.json();
}

export async function getCurrentQuestion(sessionId) {
  const res = await fetch(`${API_BASE}/interview/${sessionId}/current-question`);
  if (!res.ok) {
    const error = await res.json();
    throw new Error(error.detail || 'Failed to fetch current question.');
  }
  return res.json();
}

export async function submitAnswer(sessionId, questionId, answerText) {
  const res = await fetch(`${API_BASE}/interview/${sessionId}/submit-answer`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question_id: questionId, answer_text: answerText }),
  });
  if (!res.ok) {
    const error = await res.json();
    throw new Error(error.detail || 'Failed to submit answer.');
  }
  return res.json();
}

export async function submitFollowUp(sessionId, questionId, followUpAnswer) {
  const res = await fetch(`${API_BASE}/interview/${sessionId}/submit-followup`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question_id: questionId, follow_up_answer: followUpAnswer }),
  });
  if (!res.ok) {
    const error = await res.json();
    throw new Error(error.detail || 'Failed to submit follow up.');
  }
  return res.json();
}

export async function getSessionScorecard(sessionId) {
  const res = await fetch(`${API_BASE}/sessions/${sessionId}/scorecard`);
  if (!res.ok) {
    const error = await res.json();
    throw new Error(error.detail || 'Failed to load scorecard.');
  }
  return res.json();
}

export async function parseResumeDirectly(formData) {
  const res = await fetch(`${API_BASE}/resume/parse`, {
    method: 'POST',
    body: formData,
  });
  if (!res.ok) {
    const error = await res.json();
    throw new Error(error.detail || 'Failed to parse resume.');
  }
  return res.json();
}
