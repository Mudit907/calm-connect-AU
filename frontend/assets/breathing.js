/**
 * breathing.js — a guided breathing timer with two real patterns (box,
 * 4-7-8), correct phase timing, accessible text labels (not just
 * animation). Shared between switch-off.html and move-and-breathe.html
 * so there's one tested implementation, not two copies that can drift.
 *
 * Requires markup with: [data-pattern] buttons, #breath-circle,
 * #breath-label, #breath-count, #breath-toggle.
 */

const BREATH_PATTERNS = {
  box: [
    { phase: "inhale", seconds: 4, label: "Breathe in" },
    { phase: "hold", seconds: 4, label: "Hold" },
    { phase: "exhale", seconds: 4, label: "Breathe out" },
    { phase: "hold", seconds: 4, label: "Hold" },
  ],
  "478": [
    { phase: "inhale", seconds: 4, label: "Breathe in" },
    { phase: "hold", seconds: 7, label: "Hold" },
    { phase: "exhale", seconds: 8, label: "Breathe out" },
  ],
};

let currentPattern = "box";
let breathTimer = null;
let isBreathing = false;
let stepIndex = 0;
let secondsLeft = 0;
let completedCycles = 0;

function setPatternUI(name) {
  document.querySelectorAll("[data-pattern]").forEach((btn) => {
    btn.classList.toggle("is-active", btn.getAttribute("data-pattern") === name);
  });
}

function applyCircleClass(phase) {
  const circle = document.getElementById("breath-circle");
  circle.classList.remove("is-inhale", "is-hold", "is-exhale");
  if (phase === "inhale") circle.classList.add("is-inhale");
  else if (phase === "hold") circle.classList.add("is-hold");
  else if (phase === "exhale") circle.classList.add("is-exhale");
}

function runStep() {
  const pattern = BREATH_PATTERNS[currentPattern];
  const step = pattern[stepIndex % pattern.length];

  if (stepIndex > 0 && stepIndex % pattern.length === 0) completedCycles++;

  secondsLeft = step.seconds;
  document.getElementById("breath-label").textContent = step.label;
  document.getElementById("breath-count").textContent =
    `${step.seconds}s · cycle ${completedCycles + 1}`;
  applyCircleClass(step.phase);

  clearInterval(breathTimer);
  breathTimer = setInterval(() => {
    secondsLeft -= 1;
    document.getElementById("breath-count").textContent =
      `${Math.max(secondsLeft, 0)}s · cycle ${completedCycles + 1}`;
    if (secondsLeft <= 0) {
      stepIndex += 1;
      runStep();
    }
  }, 1000);
}

function startBreathing() {
  isBreathing = true;
  stepIndex = 0;
  completedCycles = 0;
  document.getElementById("breath-toggle").textContent = "Stop";
  runStep();
}

function stopBreathing() {
  isBreathing = false;
  clearInterval(breathTimer);
  document.getElementById("breath-toggle").textContent = "Start";
  document.getElementById("breath-label").textContent = "Press start";
  document.getElementById("breath-count").textContent = "";
  document.getElementById("breath-circle").classList.remove("is-inhale", "is-hold", "is-exhale");
}

function initBreathingModule() {
  document.querySelectorAll("[data-pattern]").forEach((btn) => {
    btn.addEventListener("click", () => {
      currentPattern = btn.getAttribute("data-pattern");
      setPatternUI(currentPattern);
      if (isBreathing) startBreathing(); // restart cleanly on the new pattern
    });
  });

  document.getElementById("breath-toggle").addEventListener("click", () => {
    if (isBreathing) stopBreathing();
    else startBreathing();
  });
}
