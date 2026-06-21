/**
 * session.js — get-or-create a persistent, anonymous session ID.
 *
 * This is NOT an account system. There is no sign-up, no password, no
 * server-side identity. It is a random token stored in this browser's
 * localStorage, used only so the backend can group a person's own
 * check-ins together for the trend view (see history.html).
 *
 * Deliberate consequence, stated plainly rather than hidden: clearing
 * browser storage (or using a different browser/device) loses the link
 * to past history. There is no recovery mechanism, by design — adding
 * one would mean adding real accounts, which this project intentionally
 * does not do. See backend/README.md for the privacy rationale.
 */

const CC_SESSION_KEY = "calmconnect_session_id";

function getOrCreateSessionId() {
  let id = localStorage.getItem(CC_SESSION_KEY);
  if (!id) {
    id = (crypto.randomUUID ? crypto.randomUUID() : _fallbackUUID());
    localStorage.setItem(CC_SESSION_KEY, id);
  }
  return id;
}

function _fallbackUUID() {
  // crypto.randomUUID() requires a secure context (https or localhost).
  // This fallback covers older browsers / plain-http local testing.
  return "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx".replace(/[xy]/g, (c) => {
    const r = (Math.random() * 16) | 0;
    const v = c === "x" ? r : (r & 0x3) | 0x8;
    return v.toString(16);
  });
}

function clearSession() {
  localStorage.removeItem(CC_SESSION_KEY);
}
