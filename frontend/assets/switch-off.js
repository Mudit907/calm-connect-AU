/**
 * switch-off.js — the sound mixer for switch-off.html: multiple ambient
 * and instrumental tracks can play simultaneously with independent
 * volume control. The breathing module on this page is handled by the
 * shared assets/breathing.js, loaded separately — see switch-off.html.
 */

function initSoundMixer() {
  document.querySelectorAll(".sound-tile").forEach((tile) => {
    const soundId = tile.getAttribute("data-sound");
    const audio = document.getElementById(soundId);
    const volSlider = tile.querySelector(`[data-vol-for="${soundId}"]`);

    if (!audio) return;
    audio.volume = (volSlider ? parseInt(volSlider.value, 10) : 60) / 100;

    tile.addEventListener("click", (e) => {
      if (e.target === volSlider) return; // don't toggle play when dragging volume
      if (audio.paused) {
        audio.play().catch((err) => console.warn("Playback blocked or file missing:", err));
        tile.classList.add("is-playing");
      } else {
        audio.pause();
        tile.classList.remove("is-playing");
      }
    });

    if (volSlider) {
      volSlider.addEventListener("input", () => {
        audio.volume = parseInt(volSlider.value, 10) / 100;
      });
      // Prevent the tile's click-to-toggle from firing when interacting with the slider
      volSlider.addEventListener("click", (e) => e.stopPropagation());
    }
  });
}

function initMixerTabs() {
  document.querySelectorAll(".mixer-tab").forEach((tab) => {
    tab.addEventListener("click", () => {
      const target = tab.getAttribute("data-tab");

      document.querySelectorAll(".mixer-tab").forEach((t) => {
        t.classList.toggle("is-active", t === tab);
        t.setAttribute("aria-selected", String(t === tab));
      });

      document.querySelectorAll(".mixer-tab-panel").forEach((panel) => {
        panel.classList.toggle("is-active", panel.getAttribute("data-panel") === target);
      });
    });
  });
}

document.addEventListener("DOMContentLoaded", () => {
  const darkToggle = document.getElementById("darkToggle");
  if (darkToggle) {
    darkToggle.addEventListener("click", () => document.body.classList.toggle("dark"));
  }
  initBreathingModule(); // from assets/breathing.js, loaded before this file
  initSoundMixer();
  initMixerTabs();
});
