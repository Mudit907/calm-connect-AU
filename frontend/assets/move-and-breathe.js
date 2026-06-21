/**
 * move-and-breathe.js — meditation timer (carried over from the original
 * the original (now-retired) yoga page, fixed to not double-fire on
 * repeated clicks) and a real,
 * guided progressive muscle relaxation (PMR) sequence: tense each muscle
 * group for a few seconds, then release, moving through the body.
 *
 * The breathing module on this page is handled by the shared
 * assets/breathing.js, loaded separately — see move-and-breathe.html.
 */

const PMR_SEQUENCE = [
  { group: "Hands and forearms", instruction: "Clench both fists tightly.", tense: 5, release: 8 },
  { group: "Upper arms", instruction: "Bend your elbows, tense your biceps.", tense: 5, release: 8 },
  { group: "Shoulders", instruction: "Raise your shoulders up toward your ears.", tense: 5, release: 8 },
  { group: "Face", instruction: "Scrunch your face — eyes, jaw, forehead.", tense: 5, release: 8 },
  { group: "Chest and back", instruction: "Take a deep breath, hold it, tense your chest.", tense: 5, release: 8 },
  { group: "Stomach", instruction: "Tighten your stomach muscles.", tense: 5, release: 8 },
  { group: "Legs and feet", instruction: "Point your toes, tense your calves and thighs.", tense: 5, release: 8 },
];

let pmrIndex = 0;
let pmrTimer = null;

function initMeditationTimer() {
  let timerInterval = null;
  const startBtn = document.getElementById("start-timer");
  if (!startBtn) return;

  startBtn.addEventListener("click", () => {
    const select = document.getElementById("timer");
    let timeRemaining = parseInt(select.value, 10);

    clearInterval(timerInterval); // prevent stacking multiple intervals on repeated clicks

    timerInterval = setInterval(() => {
      const minutes = Math.floor(timeRemaining / 60);
      const seconds = timeRemaining % 60;
      document.getElementById("timer-display").textContent =
        `${minutes < 10 ? "0" : ""}${minutes}:${seconds < 10 ? "0" : ""}${seconds}`;

      if (timeRemaining <= 0) {
        clearInterval(timerInterval);
        document.getElementById("timer-display").textContent = "Done";
      } else {
        timeRemaining--;
      }
    }, 1000);
  });
}

function renderPmrStep() {
  const container = document.getElementById("pmr-steps");
  const step = PMR_SEQUENCE[pmrIndex];

  container.innerHTML = `
    <div class="pmr-step is-active">
      <p class="pmr-progress">Step ${pmrIndex + 1} of ${PMR_SEQUENCE.length}</p>
      <div class="pmr-timer-ring" id="pmr-ring">${step.tense}s</div>
      <h3>${step.group}</h3>
      <p style="color: var(--mid-eucalyptus);" id="pmr-instruction">${step.instruction}</p>
    </div>
  `;

  runPmrPhase("tense", step);
}

function runPmrPhase(phase, step) {
  const ring = document.getElementById("pmr-ring");
  const instruction = document.getElementById("pmr-instruction");
  let secondsLeft = phase === "tense" ? step.tense : step.release;

  if (phase === "release") {
    instruction.textContent = "Now let go completely. Notice the difference.";
  }

  clearInterval(pmrTimer);
  ring.textContent = `${secondsLeft}s`;
  pmrTimer = setInterval(() => {
    secondsLeft -= 1;
    ring.textContent = `${Math.max(secondsLeft, 0)}s`;
    if (secondsLeft <= 0) {
      clearInterval(pmrTimer);
      if (phase === "tense") {
        runPmrPhase("release", step);
      } else {
        advancePmr();
      }
    }
  }, 1000);
}

function advancePmr() {
  pmrIndex += 1;
  if (pmrIndex >= PMR_SEQUENCE.length) {
    document.getElementById("pmr-steps").innerHTML = "";
    document.getElementById("pmr-complete").classList.add("is-active");
  } else {
    renderPmrStep();
  }
}

function initPmr() {
  const startBtn = document.getElementById("pmr-start");
  const restartBtn = document.getElementById("pmr-restart");

  startBtn.addEventListener("click", () => {
    document.getElementById("pmr-intro").style.display = "none";
    pmrIndex = 0;
    renderPmrStep();
  });

  restartBtn.addEventListener("click", () => {
    document.getElementById("pmr-complete").classList.remove("is-active");
    document.getElementById("pmr-intro").style.display = "block";
  });
}

document.addEventListener("DOMContentLoaded", () => {
  initBreathingModule(); // from assets/breathing.js, loaded before this file
  initMeditationTimer();
  initPmr();
});
