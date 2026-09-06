export type ModelName = "basic" | "form" | "elo" | "ensemble" | "ml";

export type Confidence =
  | "VERY_LOW"
  | "LOW"
  | "MEDIUM"
  | "HIGH"
  | "VERY_HIGH"
  | "INSUFFICIENT_DATA";

export type Outcome = "HOME" | "DRAW" | "AWAY";

export interface Team {
  id: number;
  name: string;
  short_name: string | null;
  code: string | null;
  logo: string | null;
  team_type: "CLUB" | "NATIONAL_TEAM";
}

export interface Competition {
  id: number;
  name: string;
  code: string | null;
  country: string | null;
  continent: string;
  type: string;
  data_quality: "A" | "B" | "C" | "D";
  logo: string | null;
}

export interface ScoreLine {
  score: string;
  probability: number;
}

export interface Prediction {
  model_name: string;
  model_version: string;
  generated_at: string;
  locked: boolean;
  home_win_probability: number;
  draw_probability: number;
  away_win_probability: number;
  expected_home_goals: number;
  expected_away_goals: number;
  btts_probability: number;
  over_2_5_probability: number;
  top_scores: ScoreLine[];
  confidence: Confidence;
  predicted_result: Outcome;
  actual_result: Outcome | null;
  correct: boolean | null;
  brier_score: number | null;
  log_loss: number | null;
}

export interface MatchSummary {
  id: number;
  utc_date: string;
  status: string;
  matchday: number | null;
  competition: Competition | null;
  home_team: Team | null;
  away_team: Team | null;
  home_goals: number | null;
  away_goals: number | null;
  winner: string | null;
  prediction?: Prediction | null;
}

export interface PaginatedMatches {
  page: number;
  page_size: number;
  total: number;
  results: MatchSummary[];
}

export interface MatchPredictionUnreliable {
  match_id: number;
  reliable: false;
  reason: string;
  model?: string;
}

export interface MatchPredictionReliable extends Prediction {
  match_id: number;
  reliable: true;
}

export type MatchPredictionResponse = MatchPredictionUnreliable | MatchPredictionReliable;

export interface MatchPredictionCompareResponse {
  match_id: number;
  models: Record<string, Prediction>;
}

export interface WorldTreeCompetition {
  id: number;
  name: string;
  code: string | null;
  type: string;
  data_quality: string;
  logo: string | null;
}

export interface WorldTreeCountry {
  country_id: number | null;
  country: string;
  competitions: WorldTreeCompetition[];
}

export interface WorldTreeNode {
  continent: string;
  countries: WorldTreeCountry[];
}

export interface StandingRow {
  team_id: number;
  team: string;
  played: number;
  wins: number;
  draws: number;
  losses: number;
  goals_for: number;
  goals_against: number;
  points: number;
  goal_difference: number;
}

export interface TeamFormSummary {
  matches: number;
  wins: number;
  draws: number;
  losses: number;
  points: number;
  points_per_match: number;
  goals_for: number;
  goals_against: number;
  avg_goals_for: number;
  avg_goals_against: number;
  goal_difference: number;
  clean_sheets: number;
  failed_to_score: number;
}

export interface TeamFormResponse {
  team: Team;
  reliable: boolean;
  reason?: string;
  elo_rating?: number;
  matches_played?: number;
  goals_for?: number;
  goals_against?: number;
  home?: { matches: number; goals_for: number; goals_against: number };
  away?: { matches: number; goals_for: number; goals_against: number };
  form?: Record<string, TeamFormSummary | null>;
}

export interface ModelListEntry {
  name: string;
  label: string;
  variables: string[];
  matches_evaluated: number;
  accuracy: number | null;
  brier_score: number | null;
  log_loss: number | null;
  version?: string;
  trained_at?: string;
  algorithm?: string;
  test_report?: { matches: number; accuracy: number | null; brier_score: number | null; log_loss: number | null };
}

export interface ClassificationReport {
  accuracy: number;
  precision: Record<string, number>;
  recall: Record<string, number>;
  f1: Record<string, number>;
  confusion_matrix: number[][];
  labels: string[];
}

export interface CalibrationPoint {
  predicted_range: string;
  matches: number;
  mean_predicted: number;
  actual_frequency: number;
}

export interface BacktestModelReport {
  model_name: string;
  matches_evaluated: number;
  accuracy: number | null;
  brier_score: number | null;
  log_loss: number | null;
  calibration_error: number | null;
  classification: ClassificationReport | null;
  calibration_curve: CalibrationPoint[];
}

export interface BacktestCompareResponse {
  best_model: string | null;
  models: Record<string, BacktestModelReport>;
}

export interface MonthlyPoint {
  month: string;
  matches: number;
  accuracy: number | null;
  brier_score: number | null;
}

export interface CompetitionSeason {
  id: number;
  year_start: number;
  year_end: number;
  current: boolean;
}

export interface CompetitionDetail extends Competition {
  historical_depth: number;
  last_sync: string | null;
  seasons: CompetitionSeason[];
}

export interface CountryDetail {
  id: number;
  name: string;
  continent: string;
  competitions: Competition[];
}

export interface ModelMetricsEntry {
  summary: BacktestModelReport;
  monthly: MonthlyPoint[];
}

export interface SystemStatus {
  demo_mode: boolean;
  provider_configured: boolean;
  competitions_count: number;
  matches_count: number;
  demo_matches_count: number;
  real_matches_count: number;
  finished_matches_count: number;
  ml_model_available: boolean;
}
