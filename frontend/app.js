const apiBaseInput = document.getElementById("api-base");
const homeInput = document.getElementById("home-team");
const awayInput = document.getElementById("away-team");
const modelSelect = document.getElementById("model-select");
const teamList = document.getElementById("team-list");
const statusEl = document.getElementById("status");

const resultSection = document.getElementById("result");
const resultTitle = document.getElementById("result-title");
const reliableView = document.getElementById("reliable-view");
const unreliableView = document.getElementById("unreliable-view");
const unreliableReason = document.getElementById("unreliable-reason");

const compareSection = document.getElementById("compare-result");
const compareTable = document.getElementById("compare-table");

const MODEL_LABELS = {
  simple: "Poisson simple",
  form: "Poisson + forme",
  combined: "Poisson + forme + Elo + H2H",
};
const CONFIDENCE_LABELS = { faible: "faible", moyenne: "moyenne", elevee: "élevée" };

function apiBase() {
  return apiBaseInput.value.trim().replace(/\/$/, "");
}

function pct(value) {
  return `${Math.round(value * 100)} %`;
}

async function loadTeams() {
  try {
    const response = await fetch(`${apiBase()}/teams`);
    if (!response.ok) return;
    const teams = await response.json();
    teamList.innerHTML = teams.map((t) => `<option value="${t.name}"></option>`).join("");
  } catch (err) {
    // Silently ignore: the dashboard still works with manually typed names.
  }
}

async function predict() {
  const home = homeInput.value.trim();
  const away = awayInput.value.trim();
  if (!home || !away) {
    statusEl.textContent = "Renseignez les deux équipes.";
    return;
  }

  statusEl.textContent = "Calcul en cours...";
  resultSection.classList.add("hidden");
  compareSection.classList.add("hidden");

  try {
    const url = `${apiBase()}/predict?home=${encodeURIComponent(home)}&away=${encodeURIComponent(away)}&model=${modelSelect.value}`;
    const response = await fetch(url);
    if (!response.ok) {
      statusEl.textContent = `Erreur API (${response.status}).`;
      return;
    }
    const data = await response.json();
    renderResult(data);
    statusEl.textContent = "";
  } catch (err) {
    statusEl.textContent = "Impossible de contacter l'API. Vérifiez l'URL et que le serveur tourne.";
  }
}

function renderResult(data) {
  resultSection.classList.remove("hidden");
  resultTitle.textContent = `${data.home_team} — ${data.away_team}`;

  if (!data.reliable) {
    reliableView.classList.add("hidden");
    unreliableView.classList.remove("hidden");
    unreliableReason.textContent = data.reason;
    return;
  }

  unreliableView.classList.add("hidden");
  reliableView.classList.remove("hidden");

  document.getElementById("home-win").textContent = pct(data.home_win);
  document.getElementById("draw").textContent = pct(data.draw);
  document.getElementById("away-win").textContent = pct(data.away_win);
  document.getElementById("btts").textContent = pct(data.btts);
  document.getElementById("over25").textContent = pct(data.over_2_5);
  document.getElementById("xg").textContent = `${data.expected_home_goals} - ${data.expected_away_goals}`;
  document.getElementById("confidence").textContent = CONFIDENCE_LABELS[data.confidence] ?? data.confidence;

  const list = document.getElementById("top-scores");
  list.innerHTML = data.top_scores
    .map((s) => `<li>${s.score} <span style="color:var(--muted)">(${pct(s.probability)})</span></li>`)
    .join("");
}

async function compareModels() {
  const home = homeInput.value.trim();
  const away = awayInput.value.trim();
  if (!home || !away) {
    statusEl.textContent = "Renseignez les deux équipes.";
    return;
  }

  statusEl.textContent = "Comparaison en cours...";
  resultSection.classList.add("hidden");
  compareSection.classList.add("hidden");

  try {
    const url = `${apiBase()}/predict/compare?home=${encodeURIComponent(home)}&away=${encodeURIComponent(away)}`;
    const response = await fetch(url);
    if (!response.ok) {
      statusEl.textContent = `Erreur API (${response.status}).`;
      return;
    }
    const data = await response.json();
    renderCompare(data);
    statusEl.textContent = "";
  } catch (err) {
    statusEl.textContent = "Impossible de contacter l'API.";
  }
}

function renderCompare(data) {
  compareSection.classList.remove("hidden");
  const models = ["simple", "form", "combined"];

  if (!models.some((m) => data[m].reliable)) {
    compareTable.innerHTML = `<p class="warning">${data.combined.reason}</p>`;
    return;
  }

  const rows = models
    .map((m) => {
      const p = data[m];
      if (!p.reliable) return "";
      return `<tr>
        <td>${MODEL_LABELS[m]}</td>
        <td>${pct(p.home_win)}</td>
        <td>${pct(p.draw)}</td>
        <td>${pct(p.away_win)}</td>
        <td>${pct(p.btts)}</td>
        <td>${p.top_scores[0].score}</td>
      </tr>`;
    })
    .join("");

  compareTable.innerHTML = `
    <table>
      <thead>
        <tr><th>Modèle</th><th>Domicile</th><th>Nul</th><th>Extérieur</th><th>BTTS</th><th>Score le + probable</th></tr>
      </thead>
      <tbody>${rows}</tbody>
    </table>
  `;
}

async function runBacktest() {
  const output = document.getElementById("backtest-result");
  output.innerHTML = "<p>Calcul en cours...</p>";
  try {
    const response = await fetch(`${apiBase()}/backtest/compare`);
    const data = await response.json();
    renderBacktest(data, output);
  } catch (err) {
    output.innerHTML = "<p>Impossible de contacter l'API.</p>";
  }
}

function renderBacktest(data, output) {
  const rows = Object.entries(data.models)
    .map(([name, report]) => {
      const isBest = name === data.best_model;
      return `<tr${isBest ? ' class="best"' : ""}>
        <td>${MODEL_LABELS[name]}${isBest ? " ⭐" : ""}</td>
        <td>${report.matches_evaluated}</td>
        <td>${report.brier_score ?? "—"}</td>
        <td>${report.log_loss ?? "—"}</td>
        <td>${report.accuracy != null ? pct(report.accuracy) : "—"}</td>
      </tr>`;
    })
    .join("");

  output.innerHTML = `
    <table>
      <thead>
        <tr><th>Modèle</th><th>Matchs évalués</th><th>Brier score</th><th>Log loss</th><th>Précision</th></tr>
      </thead>
      <tbody>${rows}</tbody>
    </table>
    <p class="hint">⭐ = modèle le mieux calibré (Brier score le plus bas) sur l'historique stocké.</p>
  `;
}

document.getElementById("predict-btn").addEventListener("click", predict);
document.getElementById("compare-btn").addEventListener("click", compareModels);
document.getElementById("backtest-btn").addEventListener("click", runBacktest);
apiBaseInput.addEventListener("change", loadTeams);

loadTeams();
