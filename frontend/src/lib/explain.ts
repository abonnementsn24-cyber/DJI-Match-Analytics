import type { Prediction, TeamFormResponse } from "./types";

/** Deterministic, human-readable reasons behind a prediction — never framed
 * as certainty, always as contributing factors (per product brief §12). */
export function buildExplanation(
  homeForm: TeamFormResponse | null,
  awayForm: TeamFormResponse | null,
  eloDifference: number | null,
  prediction: Prediction
): string[] {
  const reasons: string[] = [];

  const homeRecent = homeForm?.form?.["last_5"];
  const awayRecent = awayForm?.form?.["last_5"];

  if (homeRecent && awayRecent) {
    if (homeRecent.points_per_match - awayRecent.points_per_match >= 0.6) {
      reasons.push("Meilleure forme récente de l'équipe à domicile sur les 5 derniers matchs.");
    } else if (awayRecent.points_per_match - homeRecent.points_per_match >= 0.6) {
      reasons.push("Meilleure forme récente de l'équipe à l'extérieur sur les 5 derniers matchs.");
    }
  }

  if (eloDifference !== null) {
    if (eloDifference >= 60) {
      reasons.push("Rating Elo nettement supérieur pour l'équipe à domicile.");
    } else if (eloDifference <= -60) {
      reasons.push("Rating Elo nettement supérieur pour l'équipe à l'extérieur.");
    }
  }

  if (prediction.home_win_probability > 0.4 && prediction.home_win_probability > prediction.away_win_probability) {
    reasons.push("L'avantage du terrain joue en faveur de l'équipe à domicile.");
  }

  if (awayRecent && awayRecent.avg_goals_against >= 1.6) {
    reasons.push("Défense extérieure fragile récemment (buts encaissés au-dessus de la moyenne).");
  }
  if (homeRecent && homeRecent.avg_goals_against >= 1.6) {
    reasons.push("Défense à domicile fragile récemment (buts encaissés au-dessus de la moyenne).");
  }

  if (prediction.btts_probability >= 0.55) {
    reasons.push("Les deux équipes marquent fréquemment dans leurs matchs récents.");
  }

  if (reasons.length === 0) {
    reasons.push("Aucun facteur ne se détache nettement — équipes statistiquement proches.");
  }

  return reasons.slice(0, 4);
}
