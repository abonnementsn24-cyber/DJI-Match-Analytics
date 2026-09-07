import Link from "next/link";
import { notFound } from "next/navigation";
import { AlertTriangle, Lightbulb } from "lucide-react";
import { api, ApiError } from "@/lib/api";
import { ProbabilityBar } from "@/components/ProbabilityBar";
import { ConfidenceBadge } from "@/components/ConfidenceBadge";
import { FormStrip } from "@/components/FormStrip";
import { EloCompare } from "@/components/EloCompare";
import { ModelComparisonTable } from "@/components/ModelComparisonTable";
import { formatDateTime, continentLabel, pct } from "@/lib/format";
import { buildExplanation } from "@/lib/explain";
import type { MatchPredictionCompareResponse, TeamFormResponse } from "@/lib/types";

export const dynamic = "force-dynamic";

export default async function MatchDetailPage({ params }: PageProps<"/matches/[id]">) {
  const { id } = await params;
  const matchId = Number(id);
  if (!Number.isFinite(matchId)) notFound();

  let match;
  try {
    match = await api.matchDetail(matchId);
  } catch (err) {
    if (err instanceof ApiError && err.status === 404) notFound();
    throw err;
  }

  const [compareResult, h2h, homeForm, awayForm] = await Promise.allSettled([
    api.matchPredictionCompare(matchId),
    api.matchH2h(matchId),
    match.home_team ? api.teamForm(match.home_team.id) : Promise.reject(new Error("no team")),
    match.away_team ? api.teamForm(match.away_team.id) : Promise.reject(new Error("no team")),
  ]);

  const compare: MatchPredictionCompareResponse | null =
    compareResult.status === "fulfilled" ? compareResult.value : null;
  const ensemble = compare?.models?.ensemble;
  const homeFormData: TeamFormResponse | null = homeForm.status === "fulfilled" ? homeForm.value : null;
  const awayFormData: TeamFormResponse | null = awayForm.status === "fulfilled" ? awayForm.value : null;
  const h2hData = h2h.status === "fulfilled" ? h2h.value : null;

  const homeName = match.home_team?.name ?? "?";
  const awayName = match.away_team?.name ?? "?";

  return (
    <div className="mx-auto max-w-5xl space-y-6">
      <Link href="/matches" className="text-sm text-text-secondary hover:text-text">
        ← Retour aux matchs
      </Link>

      <div className="card p-6">
        <div className="text-center text-xs text-text-secondary">
          {match.competition?.name} {match.competition && `· ${continentLabel(match.competition.continent)}`}
          {match.competition?.country && ` · ${match.competition.country}`}
        </div>
        <div className="mt-3 flex items-center justify-center gap-6 text-center">
          <div className="flex-1">
            <div className="text-lg font-bold">{homeName}</div>
          </div>
          <div className="shrink-0 text-2xl font-bold text-text-secondary">
            {match.status === "FINISHED" ? `${match.home_goals} - ${match.away_goals}` : "vs"}
          </div>
          <div className="flex-1">
            <div className="text-lg font-bold">{awayName}</div>
          </div>
        </div>
        <div className="mt-2 text-center text-xs text-text-secondary">{formatDateTime(match.utc_date)}</div>
      </div>

      {!ensemble ? (
        <div className="card flex items-start gap-3 p-6 text-sm text-text-secondary">
          <AlertTriangle size={18} className="mt-0.5 shrink-0 text-draw" />
          <p>
            Données insuffisantes pour produire une estimation fiable sur ce match (historique trop court pour l&apos;une
            des deux équipes).
          </p>
        </div>
      ) : (
        <>
          <div className="card space-y-4 p-6">
            <h2 className="text-lg font-semibold">Probabilités principales</h2>
            <ProbabilityBar
              home={ensemble.home_win_probability}
              draw={ensemble.draw_probability}
              away={ensemble.away_win_probability}
              homeLabel={homeName}
              awayLabel={awayName}
            />
            <div className="flex items-center justify-between">
              <ConfidenceBadge confidence={ensemble.confidence} />
              <span className="text-xs text-text-secondary">Modèle: Ensemble</span>
            </div>
          </div>

          <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
            <div className="card p-6">
              <h2 className="text-lg font-semibold">Buts attendus par le modèle</h2>
              <div className="mt-4 flex justify-around text-center">
                <div>
                  <div className="text-3xl font-bold text-accent">{ensemble.expected_home_goals}</div>
                  <div className="text-xs text-text-secondary">{homeName}</div>
                </div>
                <div>
                  <div className="text-3xl font-bold text-accent">{ensemble.expected_away_goals}</div>
                  <div className="text-xs text-text-secondary">{awayName}</div>
                </div>
              </div>
              <div className="mt-4 flex justify-around text-xs text-text-secondary">
                <span>BTTS: {pct(ensemble.btts_probability)}</span>
                <span>+2,5 buts: {pct(ensemble.over_2_5_probability)}</span>
              </div>
            </div>

            <div className="card p-6">
              <h2 className="text-lg font-semibold">Scores statistiquement les plus probables</h2>
              <ul className="mt-4 space-y-2">
                {ensemble.top_scores.map((s) => (
                  <li key={s.score} className="flex items-center justify-between text-sm">
                    <span className="font-medium">{s.score}</span>
                    <span className="text-text-secondary">{pct(s.probability, 1)}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>

          <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
            <div className="card p-6">
              <h2 className="text-lg font-semibold">Forme (5 derniers matchs)</h2>
              <div className="mt-4 space-y-3">
                <div>
                  <div className="mb-1 text-sm font-medium">{homeName}</div>
                  <FormStrip form={homeFormData?.form?.["last_5"]} />
                </div>
                <div>
                  <div className="mb-1 text-sm font-medium">{awayName}</div>
                  <FormStrip form={awayFormData?.form?.["last_5"]} />
                </div>
              </div>
            </div>

            <div className="card p-6">
              <h2 className="text-lg font-semibold">Elo</h2>
              <div className="mt-4">
                {h2hData ? (
                  <EloCompare
                    homeRating={h2hData.elo.home_rating}
                    awayRating={h2hData.elo.away_rating}
                    homeName={homeName}
                    awayName={awayName}
                  />
                ) : (
                  <span className="text-xs text-text-secondary">Indisponible</span>
                )}
              </div>
            </div>
          </div>

          <div className="card p-6">
            <h2 className="text-lg font-semibold">Confrontations directes (H2H)</h2>
            {h2hData && h2hData.meetings.length > 0 ? (
              <ul className="mt-4 space-y-2 text-sm">
                {h2hData.meetings.map((m, i) => (
                  <li key={i} className="flex items-center justify-between border-t border-line pt-2 first:border-t-0 first:pt-0">
                    <span>
                      {m.home_team} {m.home_goals} - {m.away_goals} {m.away_team}
                    </span>
                    <span className="text-text-secondary">{new Date(m.date).toLocaleDateString("fr-FR")}</span>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="mt-4 text-sm text-text-secondary">Aucune confrontation directe connue.</p>
            )}
          </div>

          {compare && (
            <div className="card p-6">
              <h2 className="mb-4 text-lg font-semibold">Comparaison des modèles</h2>
              <ModelComparisonTable models={compare.models} />
            </div>
          )}

          <div className="card p-6">
            <h2 className="flex items-center gap-2 text-lg font-semibold">
              <Lightbulb size={18} className="text-accent" />
              Pourquoi le modèle donne cette estimation ?
            </h2>
            <ul className="mt-4 list-disc space-y-1.5 pl-5 text-sm text-text-secondary">
              {buildExplanation(homeFormData, awayFormData, h2hData?.elo.difference ?? null, ensemble).map(
                (reason, i) => (
                  <li key={i}>{reason}</li>
                )
              )}
            </ul>
            <p className="mt-4 text-xs italic text-text-secondary">
              Ces facteurs expliquent la tendance statistique — ils ne garantissent aucun résultat.
            </p>
          </div>
        </>
      )}
    </div>
  );
}
