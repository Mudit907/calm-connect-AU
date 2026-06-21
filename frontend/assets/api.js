/**
 * api.js — single place that knows the backend URL. Change API_BASE_URL
 * once you have your Render/Railway deployment URL; nothing else needs
 * to change.
 *
 * Depends on session.js being loaded first (for getOrCreateSessionId).
 */

const API_BASE_URL = "https://calm-connect-au.onrender.com";

async function getRecommendation(age, text) {
  const sessionId = getOrCreateSessionId();

  const res = await fetch(`${API_BASE_URL}/recommend`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id: sessionId, age, text }),
  });

  if (!res.ok) {
    const detail = await res.json().catch(() => ({}));
    throw new Error(detail.detail || `Request failed (${res.status})`);
  }

  return res.json();
}

async function getHistory() {
  const sessionId = getOrCreateSessionId();

  const res = await fetch(`${API_BASE_URL}/history/${sessionId}`, { method: "GET" });

  if (!res.ok) {
    const detail = await res.json().catch(() => ({}));
    throw new Error(detail.detail || `Request failed (${res.status})`);
  }

  return res.json();
}

async function checkApiHealth() {
  try {
    const res = await fetch(`${API_BASE_URL}/health`, { method: "GET" });
    return res.ok;
  } catch {
    return false;
  }
}
