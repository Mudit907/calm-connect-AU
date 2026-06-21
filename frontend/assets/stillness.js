/**
 * stillness.js — two small, genuinely-finished tools:
 * 1. A daily reflection prompt, deterministic by date (same prompt all
 *    day, changes tomorrow) rather than random-on-every-reload, which
 *    would undermine the "today's reflection" framing.
 * 2. A gratitude list persisted to localStorage — no backend, by design
 *    (see frontend IA notes), but genuinely useful across visits since
 *    the entire point is being able to look back at past entries.
 */

const REFLECTION_PROMPTS = [
  "What's one thing that went better than expected recently?",
  "Who's someone you haven't thanked in a while, and why are you grateful for them?",
  "What's something you're looking forward to, even a small thing?",
  "What would you tell a friend who was going through what you're going through?",
  "What's one thing your body did for you today, without you having to think about it?",
  "What's something you used to worry about that doesn't bother you anymore?",
  "If today was easy, what made it easy? If it wasn't, what got you through it?",
  "What's a small kindness you noticed today, given or received?",
  "What's something you know now that you wish you'd known a year ago?",
  "What's one thing you're proud of that no one else noticed?",
];

const GRATITUDE_KEY = "calmconnect_gratitude_entries";

function getTodaysPrompt() {
  // Deterministic by day-of-year so the prompt is stable for the whole
  // day, not re-randomised on every page load.
  const now = new Date();
  const start = new Date(now.getFullYear(), 0, 0);
  const dayOfYear = Math.floor((now - start) / 86400000);
  return REFLECTION_PROMPTS[dayOfYear % REFLECTION_PROMPTS.length];
}

function loadGratitudeEntries() {
  try {
    const raw = localStorage.getItem(GRATITUDE_KEY);
    return raw ? JSON.parse(raw) : [];
  } catch {
    return [];
  }
}

function saveGratitudeEntries(entries) {
  localStorage.setItem(GRATITUDE_KEY, JSON.stringify(entries));
}

function formatGratitudeDate(isoString) {
  return new Date(isoString).toLocaleDateString("en-AU", { day: "numeric", month: "short" });
}

function renderGratitudeList() {
  const entries = loadGratitudeEntries();
  const list = document.getElementById("gratitude-list");

  if (entries.length === 0) {
    list.innerHTML = `<p class="gratitude-empty">Nothing here yet — add the first thing below.</p>`;
    return;
  }

  // Most recent first
  list.innerHTML = entries
    .slice()
    .reverse()
    .map(
      (entry) => `
      <div class="gratitude-entry">
        <span>${escapeHtml(entry.text)}</span>
        <span class="gratitude-entry__date">${formatGratitudeDate(entry.date)}</span>
      </div>
    `
    )
    .join("");
}

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str;
  return div.innerHTML;
}

function initGratitudeTool() {
  renderGratitudeList();

  document.getElementById("gratitude-form").addEventListener("submit", (e) => {
    e.preventDefault();
    const input = document.getElementById("gratitude-input");
    const text = input.value.trim();
    if (!text) return;

    const entries = loadGratitudeEntries();
    entries.push({ text, date: new Date().toISOString() });
    saveGratitudeEntries(entries);

    input.value = "";
    renderGratitudeList();
  });
}

document.addEventListener("DOMContentLoaded", () => {
  document.getElementById("reflection-prompt").textContent = getTodaysPrompt();
  initGratitudeTool();
});
