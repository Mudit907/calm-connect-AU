/**
 * shared.js — injects consistent nav/footer/crisis-banner markup on every
 * page, so the need-state pages + index don't each hand-roll their own
 * header. Each page just needs: <div id="cc-nav-root"></div> and
 * <div id="cc-footer-root"></div> plus a body[data-page="..."] attribute
 * to highlight the active nav link.
 */

const CC_PAGES = [
  { id: "index", label: "Home", href: "index.html" },
  { id: "switch-off", label: "Switch off", href: "switch-off.html" },
  { id: "move-and-breathe", label: "Move & breathe", href: "move-and-breathe.html" },
  { id: "different-perspective", label: "A different view", href: "different-perspective.html" },
  { id: "lighten-up", label: "Lighten up", href: "lighten-up.html" },
  { id: "stillness", label: "Stillness", href: "stillness.html" },
  { id: "history", label: "Your history", href: "history.html" },
  { id: "crisis-plan", label: "Coping plan", href: "crisis-plan.html" },
];

function renderNav() {
  const root = document.getElementById("cc-nav-root");
  if (!root) return;
  const currentPage = document.body.dataset.page || "";

  const links = CC_PAGES.map(
    (p) =>
      `<li><a href="${p.href}" ${p.id === currentPage ? 'aria-current="page"' : ""}>${p.label}</a></li>`
  ).join("");

  root.innerHTML = `
    <nav class="cc-nav">
      <a class="cc-nav__brand" href="index.html">
        <span class="cc-nav__brand-mark" aria-hidden="true"></span>
        CalmConnect
      </a>
      <button class="cc-nav__toggle" id="cc-nav-toggle" aria-label="Toggle navigation" aria-expanded="false">&#9776;</button>
      <ul class="cc-nav__links" id="cc-nav-links">${links}</ul>
    </nav>
  `;

  const toggle = document.getElementById("cc-nav-toggle");
  const linksEl = document.getElementById("cc-nav-links");
  toggle.addEventListener("click", () => {
    const isOpen = linksEl.classList.toggle("cc-nav__links--open");
    toggle.setAttribute("aria-expanded", String(isOpen));
  });
}

function renderFooter() {
  const root = document.getElementById("cc-footer-root");
  if (!root) return;
  root.innerHTML = `
    <footer class="cc-footer">
      <div class="cc-footer__grid">
        <div>
          <h4>CalmConnect</h4>
          <p style="color: var(--sage); font-size: 0.85rem;">A calm space to find the support that fits how you're feeling right now.</p>
        </div>
        <div>
          <h4>Find what helps</h4>
          <a href="switch-off.html">Can't switch off</a>
          <a href="move-and-breathe.html">Need to move, need to breathe</a>
          <a href="different-perspective.html">Want a different perspective</a>
          <a href="lighten-up.html">Need a laugh</a>
          <a href="stillness.html">Want some stillness</a>
        </div>
        <div>
          <h4>Support (Australia)</h4>
          <a href="crisis-plan.html">Your coping plan</a>
          <a href="tel:131114">Lifeline — 13 11 14</a>
          <a href="tel:1300224636">Beyond Blue — 1300 22 4636</a>
          <a href="tel:1800551800">Kids Helpline — 1800 55 1800</a>
        </div>
      </div>
      <p class="cc-footer__meta">CalmConnect is a portfolio project, not a clinical service. If you're in immediate danger, call 000.</p>
    </footer>
  `;
}

/**
 * Crisis banner: shown when the recommender API's escalation trigger
 * fires (escalation_flag in the /recommend response). Inserted once,
 * toggled visible/hidden — never removed from the DOM so it can't be
 * "dismissed away" by accident mid-session.
 */
function renderCrisisBanner() {
  const root = document.getElementById("cc-crisis-root");
  if (!root) return;
  root.innerHTML = `
    <div class="crisis-banner" id="cc-crisis-banner" role="status">
      <span class="crisis-banner__text">It sounds like things feel heavy right now. Support is available, day or night.</span>
      <span class="crisis-banner__links">
        <a href="tel:131114">Lifeline 13 11 14</a>
        <a href="tel:1300224636">Beyond Blue 1300 22 4636</a>
        <a href="crisis-plan.html">Your coping plan</a>
      </span>
    </div>
  `;
}

function showCrisisBanner() {
  const el = document.getElementById("cc-crisis-banner");
  if (el) el.classList.add("crisis-banner--visible");
}

document.addEventListener("DOMContentLoaded", () => {
  renderNav();
  renderFooter();
  renderCrisisBanner();
});
