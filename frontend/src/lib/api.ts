import type {
  BacktestCompareResponse,
  CompetitionDetail,
  CountryDetail,
  MatchPredictionCompareResponse,
  MatchPredictionResponse,
  MatchSummary,
  ModelListEntry,
  ModelMetricsEntry,
  PaginatedMatches,
  StandingRow,
  SystemStatus,
  Team,
  TeamFormResponse,
  WorldTreeNode,
} from "./types";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export class ApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.status = status;
  }
}

async function apiFetch<T>(path: string, params?: Record<string, string | number | boolean | undefined>): Promise<T> {
  const url = new URL(`${API_BASE_URL}${path}`);
  if (params) {
    for (const [key, value] of Object.entries(params)) {
      if (value !== undefined && value !== null && value !== "") {
        url.searchParams.set(key, String(value));
      }
    }
  }

  let response: Response;
  try {
    response = await fetch(url.toString(), { cache: "no-store" });
  } catch {
    throw new ApiError(
      "Impossible de contacter l'API EMDJI. Vérifiez que le backend tourne et que NEXT_PUBLIC_API_BASE_URL est correct.",
      0
    );
  }

  if (!response.ok) {
    let detail = `Erreur API (${response.status})`;
    try {
      const body = await response.json();
      if (body?.detail) detail = body.detail;
    } catch {
      // ignore body parse errors, keep generic message
    }
    throw new ApiError(detail, response.status);
  }

  return response.json() as Promise<T>;
}

export const api = {
  systemStatus: () => apiFetch<SystemStatus>("/api/v1/system/status"),

  matchesToday: (params?: { model?: string; continent?: string; competition_id?: number }) =>
    apiFetch<MatchSummary[]>("/api/v1/matches/today", params),

  matchesUpcoming: (params?: { days?: number; model?: string }) =>
    apiFetch<MatchSummary[]>("/api/v1/matches/upcoming", params),

  matchesList: (params: {
    tab?: string;
    model?: string;
    continent?: string;
    country_id?: number;
    competition_id?: number;
    team_id?: number;
    page?: number;
    page_size?: number;
  }) => apiFetch<PaginatedMatches>("/api/v1/matches", params),

  matchDetail: (id: number) => apiFetch<MatchSummary>(`/api/v1/matches/${id}`),

  matchPrediction: (id: number, model?: string) =>
    apiFetch<MatchPredictionResponse>(`/api/v1/matches/${id}/prediction`, { model }),

  matchH2h: (id: number) =>
    apiFetch<{
      match_id: number;
      meetings: { home_team: string; away_team: string; home_goals: number; away_goals: number; date: string }[];
      elo: { home_rating: number; away_rating: number; difference: number };
    }>(`/api/v1/matches/${id}/h2h`),

  matchPredictionCompare: (id: number) =>
    apiFetch<MatchPredictionCompareResponse>(`/api/v1/matches/${id}/prediction`, { compare: true }),

  teamsList: (params?: { search?: string; competition_id?: number; page?: number; page_size?: number }) =>
    apiFetch<{ page: number; page_size: number; total: number; results: Team[] }>("/api/v1/teams", params),

  teamDetail: (id: number) => apiFetch<Team>(`/api/v1/teams/${id}`),

  teamForm: (id: number) => apiFetch<TeamFormResponse>(`/api/v1/teams/${id}/form`),

  competitionsTree: (continent?: string) =>
    apiFetch<WorldTreeNode[]>("/api/v1/competitions", { continent }),

  competitionDetail: (id: number) => apiFetch<CompetitionDetail>(`/api/v1/competitions/${id}`),

  competitionStandings: (id: number, seasonId?: number) =>
    apiFetch<StandingRow[]>(`/api/v1/competitions/${id}/standings`, { season_id: seasonId }),

  competitionMatches: (id: number, params?: { season_id?: number; status?: string }) =>
    apiFetch<MatchSummary[]>(`/api/v1/competitions/${id}/matches`, params),

  competitionTeams: (id: number, seasonId?: number) =>
    apiFetch<Team[]>(`/api/v1/competitions/${id}/teams`, { season_id: seasonId }),

  countryDetail: (id: number) => apiFetch<CountryDetail>(`/api/v1/countries/${id}`),

  models: () => apiFetch<ModelListEntry[]>("/api/v1/models"),

  modelsMetrics: (params?: { model?: string; competition_id?: number }) =>
    apiFetch<Record<string, ModelMetricsEntry>>("/api/v1/models/metrics", params),

  backtesting: (params?: {
    competition_id?: number;
    country_id?: number;
    continent?: string;
    season_id?: number;
    min_confidence?: string;
  }) => apiFetch<BacktestCompareResponse>("/api/v1/backtesting", params),
};

export { API_BASE_URL };
