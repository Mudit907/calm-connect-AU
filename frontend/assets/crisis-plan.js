/**
 * crisis-plan.js — saves the coping plan form to localStorage (no
 * backend, by design — this content shouldn't need to touch a server to
 * be useful) and supports printing/saving as PDF via the browser's
 * native print dialog, so a person can keep a physical or offline copy.
 */

const PLAN_FIELDS = [
  "plan-warning-signs",
  "plan-internal-coping",
  "plan-social-distraction",
  "plan-ask-help",
  "plan-professionals",
];

const PLAN_STORAGE_KEY = "calmconnect_coping_plan";

function loadPlan() {
  try {
    const raw = localStorage.getItem(PLAN_STORAGE_KEY);
    return raw ? JSON.parse(raw) : {};
  } catch {
    return {};
  }
}

function populateForm() {
  const saved = loadPlan();
  PLAN_FIELDS.forEach((id) => {
    const field = document.getElementById(id);
    if (field && saved[id]) field.value = saved[id];
  });
}

function savePlan(e) {
  e.preventDefault();
  const data = {};
  PLAN_FIELDS.forEach((id) => {
    data[id] = document.getElementById(id).value;
  });
  localStorage.setItem(PLAN_STORAGE_KEY, JSON.stringify(data));

  const status = document.getElementById("plan-status");
  status.textContent = "Saved to this browser.";
  setTimeout(() => {
    status.textContent = "";
  }, 3000);
}

document.addEventListener("DOMContentLoaded", () => {
  populateForm();
  document.getElementById("plan-form").addEventListener("submit", savePlan);
  document.getElementById("plan-print").addEventListener("click", () => window.print());
});
