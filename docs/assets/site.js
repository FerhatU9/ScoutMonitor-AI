"use strict";

const $ = (selector) => document.querySelector(selector);
const escapeHTML = (value) => String(value).replace(/[&<>"']/g, (character) => ({
  "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
})[character]);

const state = { players: [], shortlist: new Set(), first: "SYN006", second: "SYN020" };
const number = (value) => value === null || !Number.isFinite(value) ? "—" : Number(value).toLocaleString("en-US", { maximumFractionDigits: 2 });
const decimal = (value, digits = 2) => value === null || !Number.isFinite(value) ? "—" : Number(value).toFixed(digits);
const delta = (a, b, digits = 2) => a === null || b === null ? "Unavailable" : `${b - a > 0 ? "+" : ""}${decimal(b - a, digits)}`;
const compact = (name) => name.replace("Fictional Defender ", "Defender ");

function parseCSV(text) {
  const lines = text.trim().replace(/^\uFEFF/, "").split(/\r?\n/);
  const columns = lines.shift().split(",");
  const required = ["player_id", "player_name", "age", "position", "preferred_foot", "league", "minutes", "progressive_passes_per90", "defensive_duel_win_pct", "is_synthetic", "source"];
  if (required.some((column) => !columns.includes(column))) throw new Error("Player data format is not supported");
  return lines.filter(Boolean).map((line) => {
    // The repository's synthetic dataset has no quoted commas.
    const values = line.split(",");
    if (values.length !== columns.length) throw new Error("Invalid player record");
    const record = Object.fromEntries(columns.map((column, i) => [column, values[i]]));
    if (record.is_synthetic !== "true" || record.source !== "synthetic_v1") throw new Error("Only fictional demonstration records may appear on this website");
    const nullableMetric = (value) => value === "" ? null : Number(value);
    return {
      ...record,
      age: Number(record.age),
      minutes: Number(record.minutes),
      progressive_passes_per90: nullableMetric(record.progressive_passes_per90),
      defensive_duel_win_pct: nullableMetric(record.defensive_duel_win_pct)
    };
  });
}

function filteredPlayers() {
  const query = $("#search").value.trim().toLowerCase();
  const league = $("#league").value;
  const foot = $("#foot").value;
  const sort = $("#sort").value;
  const records = state.players.filter((p) =>
    (!query || p.player_name.toLowerCase().includes(query) || p.player_id.toLowerCase().includes(query)) &&
    (!league || p.league === league) && (!foot || p.preferred_foot === foot)
  );
  records.sort((a, b) => {
    if (sort === "player_id") return a.player_id.localeCompare(b.player_id);
    const av = a[sort], bv = b[sort];
    if (av === null) return bv === null ? a.player_id.localeCompare(b.player_id) : 1;
    if (bv === null) return -1;
    return bv - av || a.player_id.localeCompare(b.player_id);
  });
  return records;
}

function renderPlayers() {
  const filtered = filteredPlayers();
  $("#result-count").textContent = `${filtered.length} / ${state.players.length} PLAYERS`;
  $("#grid-status").textContent = `DATA SOURCE / SYNTHETIC_V1 · ${state.shortlist.size} SHORTLISTED IN THIS SESSION`;
  if (!filtered.length) {
    $("#player-grid").innerHTML = '<p class="placeholder-msg">No players match these filters. Try resetting your search.</p>';
    return;
  }
  $("#player-grid").innerHTML = filtered.map((p) => {
    const selected = state.shortlist.has(p.player_id);
    const initials = p.player_id.slice(-2);
    return `
      <article class="player-card">
        <div class="card-top"><span class="card-id">${escapeHTML(p.player_id)}</span><span class="mini-tag">CB</span></div>
        <div class="player-avatar" aria-hidden="true">${escapeHTML(initials)}</div>
        <h3>${escapeHTML(compact(p.player_name))}</h3>
        <p class="player-sub">${escapeHTML(p.league)} · ${escapeHTML(p.preferred_foot)} foot · age ${p.age}</p>
        <div class="player-metrics">
          <div><span>Passes / 90</span><strong>${decimal(p.progressive_passes_per90)}</strong></div>
          <div><span>Duel win %</span><strong>${decimal(p.defensive_duel_win_pct, 1)}<small>${p.defensive_duel_win_pct === null ? "" : "%"}</small></strong></div>
        </div>
        <div class="player-actions">
          <button type="button" data-compare="${escapeHTML(p.player_id)}" aria-label="Compare ${escapeHTML(p.player_name)}">Compare ↗</button>
          <button type="button" data-shortlist="${escapeHTML(p.player_id)}" aria-pressed="${selected}" class="${selected ? "saved" : ""}">${selected ? "✓ Shortlisted" : "+ Shortlist"}</button>
        </div>
        <p class="player-footnote">${number(p.minutes)} minutes · fictional data</p>
      </article>`;
  }).join("");
}

function renderSelects() {
  const options = state.players.map((p) => `<option value="${escapeHTML(p.player_id)}">${escapeHTML(p.player_id)} · ${escapeHTML(compact(p.player_name))}</option>`).join("");
  $("#compare-a").innerHTML = options;
  $("#compare-b").innerHTML = options;
  $("#compare-a").value = state.first;
  $("#compare-b").value = state.second;
}

function metric(name, firstValue, secondValue, max, digits = 2, suffix = "") {
  const validA = firstValue !== null && Number.isFinite(firstValue);
  const validB = secondValue !== null && Number.isFinite(secondValue);
  const left = validA ? Math.min(100, (firstValue / max) * 100) : 0;
  const right = validB ? Math.min(100, (secondValue / max) * 100) : 0;
  const label = validA && validB ? delta(firstValue, secondValue, digits) + (suffix ? " " + suffix : "") : "MISSING DATA";
  return `
    <div class="metric-row">
      <div class="metric-header"><span>${escapeHTML(name)}</span><strong>${escapeHTML(label)}</strong></div>
      <div class="metric-bars">
        <div><i style="width:${left.toFixed(2)}%"></i></div>
        <div><i style="width:${right.toFixed(2)}%"></i></div>
      </div>
      <div class="metric-values"><span>${validA ? decimal(firstValue, digits) + suffix : "Not reported"}</span><span>${validB ? decimal(secondValue, digits) + suffix : "Not reported"}</span></div>
    </div>`;
}

function renderComparison() {
  state.first = $("#compare-a").value;
  state.second = $("#compare-b").value;
  const a = state.players.find((p) => p.player_id === state.first);
  const b = state.players.find((p) => p.player_id === state.second);
  if (!a || !b) return;
  if (a.player_id === b.player_id) {
    $("#comparison-output").innerHTML = '<p class="placeholder-msg" style="padding:35px">Choose two different fictional players to compare.</p>';
    return;
  }
  const maxMinutes = Math.max(1, ...state.players.map((p) => p.minutes));
  const maxPasses = Math.max(1, ...state.players.map((p) => p.progressive_passes_per90 || 0));
  $("#comparison-output").innerHTML = `
    <div class="comparison-inner">
      <div class="comparison-profile">
        <span class="compare-id">PLAYER A / ${escapeHTML(a.player_id)}</span>
        <div class="monogram" aria-hidden="true">${escapeHTML(a.player_id.slice(-2))}</div>
        <h3>${escapeHTML(compact(a.player_name))}</h3>
        <p>${escapeHTML(a.league)}</p><p>${escapeHTML(a.preferred_foot)} foot · ${a.age} years</p>
      </div>
      <div class="comparison-table">
        ${metric("Playing minutes", a.minutes, b.minutes, maxMinutes, 0)}
        ${metric("Progressive passes / 90", a.progressive_passes_per90, b.progressive_passes_per90, maxPasses)}
        ${metric("Defensive duel win %", a.defensive_duel_win_pct, b.defensive_duel_win_pct, 100, 1, "pp")}
      </div>
      <div class="comparison-profile">
        <span class="compare-id">PLAYER B / ${escapeHTML(b.player_id)}</span>
        <div class="monogram" aria-hidden="true">${escapeHTML(b.player_id.slice(-2))}</div>
        <h3>${escapeHTML(compact(b.player_name))}</h3>
        <p>${escapeHTML(b.league)}</p><p>${escapeHTML(b.preferred_foot)} foot · ${b.age} years</p>
      </div>
    </div>
    <div class="compare-note">All values come from fictional demonstration data. The difference is Player B minus Player A; <strong>pp</strong> means percentage points. A missing metric is displayed as “Not reported” and cannot be compared. Comparisons are descriptive, not player rankings or predictions.</div>`;
}

function activateNavigation() {
  const links = [...document.querySelectorAll("[data-nav]")];
  const sections = links.map((link) => document.getElementById(link.dataset.nav)).filter(Boolean);
  if (!("IntersectionObserver" in window)) return;
  const observer = new IntersectionObserver((entries) => {
    const visible = entries.filter((entry) => entry.isIntersecting).sort((a, b) => b.intersectionRatio - a.intersectionRatio);
    if (!visible.length) return;
    links.forEach((link) => {
      const active = link.dataset.nav === visible[0].target.id;
      link.classList.toggle("active", active);
      if (active) link.setAttribute("aria-current", "location");
      else link.removeAttribute("aria-current");
    });
  }, { rootMargin: "-15% 0px -55% 0px", threshold: [0, .2, .5] });
  sections.forEach((section) => observer.observe(section));
}

async function initialize() {
  activateNavigation();
  try {
    const response = await fetch("./assets/players.csv", { cache: "no-store" });
    if (!response.ok) throw new Error("Could not download fictional player records");
    state.players = parseCSV(await response.text());
    if (!state.players.length) throw new Error("No demonstration records");
    $("#hero-count").textContent = state.players.length;
    if (!state.players.some((p) => p.player_id === state.first)) state.first = state.players[0].player_id;
    if (!state.players.some((p) => p.player_id === state.second)) state.second = state.players.at(-1).player_id;
    renderSelects();
    renderPlayers();
    renderComparison();
    ["search", "league", "foot", "sort"].forEach((id) => {
      $("#" + id).addEventListener(id === "search" ? "input" : "change", renderPlayers);
    });
    ["compare-a", "compare-b"].forEach((id) => $("#" + id).addEventListener("change", renderComparison));
    $("#reset-filters").addEventListener("click", () => {
      $("#search").value = ""; $("#league").value = ""; $("#foot").value = ""; $("#sort").value = "player_id";
      renderPlayers();
    });
    $("#swap").addEventListener("click", () => {
      const a = $("#compare-a"), b = $("#compare-b");
      [a.value, b.value] = [b.value, a.value];
      renderComparison();
    });
    $("#player-grid").addEventListener("click", (event) => {
      const compare = event.target.closest("[data-compare]");
      const shortlist = event.target.closest("[data-shortlist]");
      if (compare) {
        const id = compare.dataset.compare;
        const a = $("#compare-a"), b = $("#compare-b");
        if (a.value === id) b.value = state.first === id ? state.second : state.first;
        else a.value = id;
        if (a.value === b.value) {
          const other = state.players.find((p) => p.player_id !== id);
          if (other) b.value = other.player_id;
        }
        renderComparison();
        document.getElementById("comparison").scrollIntoView({ behavior: "smooth" });
      }
      if (shortlist) {
        const id = shortlist.dataset.shortlist;
        if (state.shortlist.has(id)) state.shortlist.delete(id);
        else state.shortlist.add(id);
        renderPlayers();
      }
    });
  } catch (error) {
    $("#player-grid").innerHTML = '<p class="placeholder-msg">Demonstration records could not be loaded. Please refresh the page or explore the source repository.</p>';
    $("#comparison-output").innerHTML = '<p class="placeholder-msg">Comparison is unavailable while player data cannot be loaded.</p>';
    $("#grid-status").textContent = "DEMO DATA UNAVAILABLE";
    console.error("ScoutMonitor AI demo load error:", error.message);
  }
}
document.addEventListener("DOMContentLoaded", initialize);
