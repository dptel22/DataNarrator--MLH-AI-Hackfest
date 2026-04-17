/**
 * DataNarrator — frontend logic
 *
 * Sends SQL + question to the /narrate endpoint, renders the narrative text,
 * builds a data-preview table, and wires up the audio player.
 */

const API_BASE = (window.API_BASE || "http://localhost:8000").replace(/\/$/, "");

// ── DOM references ─────────────────────────────────────────────────────────────
const narrateBtn   = document.getElementById("narrate-btn");
const btnLabel     = document.getElementById("btn-label");
const btnSpinner   = document.getElementById("btn-spinner");
const errorMsg     = document.getElementById("error-msg");
const resultsSection = document.getElementById("results-section");
const narrativeText  = document.getElementById("narrative-text");
const tableHead    = document.getElementById("table-head");
const tableBody    = document.getElementById("table-body");
const audioEl      = document.getElementById("audio-element");
const playBtn      = document.getElementById("play-btn");
const pauseBtn     = document.getElementById("pause-btn");

// ── helpers ────────────────────────────────────────────────────────────────────

function setLoading(loading) {
  narrateBtn.disabled = loading;
  btnLabel.classList.toggle("hidden", loading);
  btnSpinner.classList.toggle("hidden", !loading);
}

function showError(msg) {
  errorMsg.textContent = msg;
  errorMsg.classList.remove("hidden");
}

function clearError() {
  errorMsg.textContent = "";
  errorMsg.classList.add("hidden");
}

function buildTable(records) {
  if (!records || records.length === 0) {
    tableHead.innerHTML = "";
    tableBody.innerHTML = '<tr><td colspan="1" style="color:var(--clr-muted)">No data returned.</td></tr>';
    return;
  }
  const cols = Object.keys(records[0]);

  // header
  tableHead.innerHTML =
    "<tr>" + cols.map(c => `<th>${escapeHtml(c)}</th>`).join("") + "</tr>";

  // rows
  tableBody.innerHTML = records
    .map(row =>
      "<tr>" +
      cols.map(c => `<td>${escapeHtml(String(row[c] ?? ""))}</td>`).join("") +
      "</tr>"
    )
    .join("");
}

function escapeHtml(str) {
  return str
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function loadAudio(base64Mp3) {
  const blob = base64ToBlob(base64Mp3, "audio/mpeg");
  const url  = URL.createObjectURL(blob);
  audioEl.src = url;
  playBtn.classList.remove("hidden");
  pauseBtn.classList.add("hidden");
}

function base64ToBlob(base64, mimeType) {
  const bytes = atob(base64);
  const arr   = new Uint8Array(bytes.length);
  for (let i = 0; i < bytes.length; i++) arr[i] = bytes.charCodeAt(i);
  return new Blob([arr], { type: mimeType });
}

// ── audio controls ─────────────────────────────────────────────────────────────
playBtn.addEventListener("click", () => {
  audioEl.play();
  playBtn.classList.add("hidden");
  pauseBtn.classList.remove("hidden");
});

pauseBtn.addEventListener("click", () => {
  audioEl.pause();
  pauseBtn.classList.add("hidden");
  playBtn.classList.remove("hidden");
});

audioEl.addEventListener("ended", () => {
  pauseBtn.classList.add("hidden");
  playBtn.classList.remove("hidden");
});

// ── narrate handler ────────────────────────────────────────────────────────────
narrateBtn.addEventListener("click", async () => {
  const question = document.getElementById("question-input").value.trim();
  const sql      = document.getElementById("sql-input").value.trim();

  clearError();

  if (!question) { showError("Please enter a question."); return; }
  if (!sql)      { showError("Please enter a SQL query."); return; }

  setLoading(true);
  resultsSection.classList.add("hidden");

  try {
    const response = await fetch(`${API_BASE}/narrate`, {
      method:  "POST",
      headers: { "Content-Type": "application/json" },
      body:    JSON.stringify({ sql, question }),
    });

    if (!response.ok) {
      const err = await response.json().catch(() => ({}));
      throw new Error(err.detail || `HTTP ${response.status}`);
    }

    const data = await response.json();

    narrativeText.textContent = data.narrative;
    buildTable(data.records);
    loadAudio(data.audio_base64);

    resultsSection.classList.remove("hidden");
  } catch (err) {
    showError(`Error: ${err.message}`);
  } finally {
    setLoading(false);
  }
});
