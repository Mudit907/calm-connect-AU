/**
 * history.js — fetches this session's real interaction history from the
 * backend and renders it as an SVG line chart + a plain-text entry list.
 *
 * Plots escalation_probability (a real, continuous model output) over
 * time — NOT category, since categories are not an ordinal scale (see
 * backend/ml/DESIGN.md). This file does not invent any derived score.
 */

const CHART_WIDTH = 640;
const CHART_HEIGHT = 220;
const CHART_PADDING = { top: 20, right: 20, bottom: 30, left: 36 };

function formatDate(isoString) {
  const d = new Date(isoString);
  return d.toLocaleDateString("en-AU", { day: "numeric", month: "short" });
}

function buildChartSVG(points) {
  const plotWidth = CHART_WIDTH - CHART_PADDING.left - CHART_PADDING.right;
  const plotHeight = CHART_HEIGHT - CHART_PADDING.top - CHART_PADDING.bottom;

  const n = points.length;
  const xStep = n > 1 ? plotWidth / (n - 1) : 0;

  const coords = points.map((p, i) => {
    const x = CHART_PADDING.left + (n > 1 ? i * xStep : plotWidth / 2);
    const y = CHART_PADDING.top + plotHeight * (1 - p.escalation_probability);
    return { x, y, point: p };
  });

  const pathD = coords.map((c, i) => `${i === 0 ? "M" : "L"}${c.x.toFixed(1)},${c.y.toFixed(1)}`).join(" ");

  const circles = coords
    .map(
      (c) =>
        `<circle class="chart-point ${c.point.escalation_flag ? "is-elevated" : ""}" cx="${c.x.toFixed(1)}" cy="${c.y.toFixed(1)}" r="4">
          <title>${formatDate(c.point.timestamp_utc)} — probability ${c.point.escalation_probability.toFixed(2)}</title>
        </circle>`
    )
    .join("");

  const yAxisLine = `<line class="chart-axis" x1="${CHART_PADDING.left}" y1="${CHART_PADDING.top}" x2="${CHART_PADDING.left}" y2="${CHART_PADDING.top + plotHeight}" />`;
  const xAxisLine = `<line class="chart-axis" x1="${CHART_PADDING.left}" y1="${CHART_PADDING.top + plotHeight}" x2="${CHART_PADDING.left + plotWidth}" y2="${CHART_PADDING.top + plotHeight}" />`;

  const yLabelTop = `<text class="chart-axis-label" x="4" y="${CHART_PADDING.top + 4}">1.0</text>`;
  const yLabelBottom = `<text class="chart-axis-label" x="4" y="${CHART_PADDING.top + plotHeight}">0.0</text>`;

  const xLabelFirst = n > 0
    ? `<text class="chart-axis-label" x="${coords[0].x}" y="${CHART_HEIGHT - 8}" text-anchor="middle">${formatDate(points[0].timestamp_utc)}</text>`
    : "";
  const xLabelLast = n > 1
    ? `<text class="chart-axis-label" x="${coords[n - 1].x}" y="${CHART_HEIGHT - 8}" text-anchor="middle">${formatDate(points[n - 1].timestamp_utc)}</text>`
    : "";

  return `
    ${yAxisLine}${xAxisLine}
    ${yLabelTop}${yLabelBottom}${xLabelFirst}${xLabelLast}
    <path class="chart-line" d="${pathD}" />
    ${circles}
  `;
}

function renderEntryList(points) {
  const list = document.getElementById("entry-list");
  // Most recent first for the readable list, even though the chart goes
  // chronologically left-to-right.
  const reversed = [...points].reverse();
  list.innerHTML = reversed
    .map(
      (p) => `
      <div class="entry-row">
        <span class="entry-row__date">${formatDate(p.timestamp_utc)}</span>
        <span class="entry-row__rec">Recommended: ${p.top_recommendation}</span>
      </div>
    `
    )
    .join("");
}

async function initHistoryPage() {
  const loadingState = document.getElementById("loading-state");
  const emptyState = document.getElementById("empty-state");
  const dataState = document.getElementById("data-state");

  try {
    const points = await getHistory();

    loadingState.style.display = "none";

    if (!points || points.length === 0) {
      emptyState.style.display = "block";
      return;
    }

    dataState.style.display = "block";
    document.getElementById("chart-caption").textContent =
      `${points.length} check-in${points.length === 1 ? "" : "s"} recorded in this browser.`;
    document.getElementById("trend-svg").innerHTML = buildChartSVG(points);
    renderEntryList(points);
  } catch (err) {
    loadingState.innerHTML = `<p>Couldn't load your history right now. ${err.message || ""}</p>`;
    console.error(err);
  }
}

document.addEventListener("DOMContentLoaded", initHistoryPage);
