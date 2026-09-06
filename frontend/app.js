const apiBaseInput = document.getElementById("api-base");
const homeInput = document.getElementById("home-team");
const awayInput = document.getElementById("away-team");
const teamList = document.getElementById("team-list");
const statusEl = document.getElementById("status");

const resultSection = document.getElementById("result");
const resultTitle = document.getElementById("result-title");
const reliableView = document.getElementById("reliable-view");
const unreliableView = document.getElementById("unreliable-view");
const unreliableReason = document.getElementById("unreliable-reason");

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

  try {
    const url = `${apiBase()}/predict?home=${encodeURIComponent(home)}&away=${encodeURIComponent(away)}`;
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

async function runBacktest() {
  const output = document.getElementById("backtest-result");
  output.textContent = "Calcul en cours...";
  try {
    const response = await fetch(`${apiBase()}/backtest`);
    const data = await response.json();
    output.textContent = JSON.stringify(data, null, 2);
  } catch (err) {
    output.textContent = "Impossible de contacter l'API.";
  }
}

document.getElementById("predict-btn").addEventListener("click", predict);
document.getElementById("backtest-btn").addEventListener("click", runBacktest);
apiBaseInput.addEventListener("change", loadTeams);

loadTeams();
