import Link from "next/link";
import { api, ApiError } from "@/lib/api";
import { MODEL_LABELS, pct } from "@/lib/format";
import { BacktestFilters } from "@/components/BacktestFilters";

export const dynamic = "force-dynamic";

export default async function BacktestingPage({ searchParams }: PageProps<"/backtesting">) {
  const params = await searchParams;
  const competitionId = typeof params.competition_id === "string" ? Number(params.competition_id) : undefined;
  const minConfidence = typeof params.min_confidence === "string" ? params.min_confidence : undefined;

  let error: string | null = null;
  let report: Awaited<ReturnType<typeof api.backtesting>> | null = null;
  let competitionOptions: { id: number; name: string }[] = [];
  let historicalMatches: Awaited<ReturnType<typeof api.matchesList>>["results"] = [];

  try {
    const [backtest, tree, matches] = await Promise.all([
      api.backtesting({ competition_id: competitionId, min_confidence: minConfidence }),
      api.competitionsTree(),
      api.matchesList({ tab: "finished", competition_id: competitionId, page_size: 15 }),
    ]);
    report = backtest;
    competitionOptions = tree.flatMap((n) => n.countries.flatMap((c) => c.competitions.map((comp) => ({ id: comp.id, name: comp.name }))));
    historicalMatches = matches.results;
  } catch (err) {
    error = err instanceof ApiError ? err.message : "Erreur lors du chargement du backtesting.";
  }

  return (
    <div className="mx-auto max-w-6xl space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Backtesting</h1>
        <p className="mt-1 text-sm text-text-secondary">
          Rejoue l&apos;historique en chronologique (sans anticipation) pour mesurer objectivement la fiabilité de
          chaque modèle.
        </p>
      </div>

      <BacktestFilters competitions={competitionOptions} />

      {error && <div className="card border-loss/40 bg-loss/10 p-4 text-sm text-loss">{error}</div>}

      {report && (
        <>
          {report.best_model && (
            <div className="card border-accent/40 bg-accent/10 p-4 text-sm text-accent">
              Modèle le mieux calibré sur ces critères : <strong>{MODEL_LABELS[report.best_model]}</strong>
            </div>
          )}

          <div className="card overflow-x-auto p-4">
            <table className="w-full min-w-[640px] text-sm">
              <thead>
                <tr className="text-left text-xs text-text-secondary">
                  <th className="p-2">Modèle</th>
                  <th className="p-2 text-center">Matchs</th>
                  <th className="p-2 text-center">Accuracy</th>
                  <th className="p-2 text-center">Brier</th>
                  <th className="p-2 text-center">Log Loss</th>
                  <th className="p-2 text-center">Erreur de calibration</th>
                </tr>
              </thead>
              <tbody>
                {Object.entries(report.models).map(([name, m]) => (
                  <tr key={name} className={`border-t border-line ${name === report.best_model ? "bg-win/5" : ""}`}>
                    <td className="p-2 font-medium">{MODEL_LABELS[name] ?? name}</td>
                    <td className="p-2 text-center">{m.matches_evaluated}</td>
                    <td className="p-2 text-center">{m.accuracy !== null ? pct(m.accuracy) : "—"}</td>
                    <td className="p-2 text-center">{m.brier_score ?? "—"}</td>
                    <td className="p-2 text-center">{m.log_loss ?? "—"}</td>
                    <td className="p-2 text-center">{m.calibration_error ?? "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}

      <div className="card overflow-x-auto p-4">
        <h2 className="mb-3 text-lg font-semibold">Matchs historiques (Ensemble)</h2>
        <table className="w-full min-w-[640px] text-sm">
          <thead>
            <tr className="text-left text-xs text-text-secondary">
              <th className="p-2">Date</th>
              <th className="p-2">Match</th>
              <th className="p-2">Prédiction</th>
              <th className="p-2">Résultat</th>
              <th className="p-2 text-center">Correct</th>
            </tr>
          </thead>
          <tbody>
            {historicalMatches.map((m) => (
              <tr key={m.id} className="border-t border-line">
                <td className="p-2 text-text-secondary">{new Date(m.utc_date).toLocaleDateString("fr-FR")}</td>
                <td className="p-2">
                  <Link href={`/matches/${m.id}`} className="hover:text-accent">
                    {m.home_team?.name} vs {m.away_team?.name}
                  </Link>
                </td>
                <td className="p-2 text-text-secondary">
                  {m.prediction
                    ? `${pct(m.prediction.home_win_probability)} / ${pct(m.prediction.draw_probability)} / ${pct(m.prediction.away_win_probability)}`
                    : "—"}
                </td>
                <td className="p-2">
                  {m.home_goals} - {m.away_goals}
                </td>
                <td className="p-2 text-center">
                  {m.prediction?.correct === true && <span className="text-win">✓</span>}
                  {m.prediction?.correct === false && <span className="text-loss">✗</span>}
                  {m.prediction?.correct == null && "—"}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {historicalMatches.length === 0 && (
          <p className="py-4 text-center text-sm text-text-secondary">Aucun match terminé pour ces critères.</p>
        )}
      </div>
    </div>
  );
}
