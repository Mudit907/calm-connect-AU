/**
 * cbt-reframe.js — a 5-step wizard implementing a standard CBT thought
 * record: situation -> automatic thought -> evidence for -> evidence
 * against -> balanced thought. Deliberately not persisted anywhere (see
 * different-perspective.html's own disclaimer) — this is a single-session
 * tool, not a journal.
 */

const CBT_STEP_IDS = ["cbt-situation", "cbt-thought", "cbt-for", "cbt-against", "cbt-balanced"];
let cbtStepIndex = 0;

function renderCbtProgress() {
  const progress = document.getElementById("cbt-progress");
  progress.innerHTML = CBT_STEP_IDS.map((_, i) => {
    const cls = i === cbtStepIndex ? "is-active" : i < cbtStepIndex ? "is-done" : "";
    return `<span class="${cls}"></span>`;
  }).join("");
}

function showCbtStep(index) {
  document.querySelectorAll(".cbt-step").forEach((step) => {
    step.classList.toggle("is-active", parseInt(step.getAttribute("data-step"), 10) === index);
  });
  document.getElementById("cbt-back").style.visibility = index === 0 ? "hidden" : "visible";
  document.getElementById("cbt-next").textContent = index === CBT_STEP_IDS.length - 1 ? "See summary" : "Next";
  renderCbtProgress();
}

function showCbtSummary() {
  document.getElementById("cbt-form").style.display = "none";
  document.getElementById("cbt-summary").classList.add("is-active");

  const fieldToSummary = {
    "cbt-situation": "summary-situation",
    "cbt-thought": "summary-thought",
    "cbt-for": "summary-for",
    "cbt-against": "summary-against",
    "cbt-balanced": "summary-balanced",
  };

  for (const [fieldId, summaryId] of Object.entries(fieldToSummary)) {
    const value = document.getElementById(fieldId).value.trim();
    document.getElementById(summaryId).textContent = value || "(left blank)";
  }
}

function resetCbtTool() {
  CBT_STEP_IDS.forEach((id) => {
    document.getElementById(id).value = "";
  });
  cbtStepIndex = 0;
  document.getElementById("cbt-summary").classList.remove("is-active");
  document.getElementById("cbt-form").style.display = "block";
  showCbtStep(0);
}

function initCbtTool() {
  document.getElementById("cbt-next").addEventListener("click", () => {
    if (cbtStepIndex < CBT_STEP_IDS.length - 1) {
      cbtStepIndex += 1;
      showCbtStep(cbtStepIndex);
    } else {
      showCbtSummary();
    }
  });

  document.getElementById("cbt-back").addEventListener("click", () => {
    if (cbtStepIndex > 0) {
      cbtStepIndex -= 1;
      showCbtStep(cbtStepIndex);
    }
  });

  document.getElementById("cbt-restart").addEventListener("click", resetCbtTool);

  showCbtStep(0);
}

document.addEventListener("DOMContentLoaded", initCbtTool);
