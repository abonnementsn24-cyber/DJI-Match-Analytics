import Link from "next/link";
import { BarChart3, CalendarClock, Database, Target, TrendingUp, Trophy } from "lucide-react";
import { api, ApiError } from "@/lib/api";
import { StatTile } from "@/components/StatTile";
import { MatchCard } from "@/components/MatchCard";
import { MODEL_LABELS, pct } from "@/lib/format";
import type { MatchSummary } from "@/lib/types";

export const dynamic = "force-dynamic";

const SORTS = [
  { key: "time", label: "Heure" },
  { key: "competition", label: "Compétition" },
  { key: "confidence", label: "Confiance" },
  { key: "probability", label: "Probabilité dominante" },
] as const;

function sortMatches(matches: MatchSummary[], sort: string): MatchSummary[] {
  const copy = [...matches];
  switch (sort) {
    case "competition":
      return copy.sort((a, b) => (a.competition?.name ?? "").localeCompare(b.competition?.name ?? ""));
    case "confidence": {
      const order = ["VERY_HIGH", "HIGH", "MEDIUM", "LOW", "VERY_LOW", "INSUFFICIENT_DATA"];
      return copy.sort(
        (a, b) =>
          order.indexOf(a.prediction?.confidence ?? "INSUFFICIENT_DATA") -
          order.indexOf(b.prediction?.confidence ?? "INSUFFICIENT_DATA")
      );
    }
    case "probability":
      return copy.sort((a, b) => {
        const maxA = a.prediction
          ? Math.max(a.prediction.home_win_probability, a.prediction.draw_probability, a.prediction.away_win_probability)
          : 0;
        const maxB = b.prediction
          ? Math.max(b.prediction.home_win_probability, b.prediction.draw_probability, b.prediction.away_win_probability)
          : 0;
        return maxB - maxA;
      });
    default:
      return copy.sort((a, b) => a.utc_date.localeCompare(b.utc_date));
  }
}

export default async function DashboardPage({
  searchParams,
}: PageProps<"/dashboard">) {
  const params = await searchParams;
  const sort = typeof params.sort === "string" ? params.sort : "time";

  let error: string | null = null;
  let todayMatches: MatchSummary[] = [];
  let upcomingCount = 0;
  let bestModel: string | null = null;
  let bestAccuracy: number | null = null;
  let bestBrier: number | null = null;
  let totalHistorical = 0;

  try {
    const [today, upcoming, backtest, status] = await Promise.all([
      api.matchesToday(),
      api.matchesUpcoming({ days: 7 }),
      api.backtesting(),
      api.systemStatus(),
    ]);
    todayMatches = today;
    upcomingCount = upcoming.length;
    bestModel = backtest.best_model;
    if (bestModel) {
      bestAccuracy = backtest.models[bestModel]?.accuracy ?? null;
      bestBrier = backtest.models[bestModel]?.brier_score ?? null;
    }
    totalHistorical = status.finished_matches_count;
  } catch (err) {
    error = err instanceof ApiError ? err.message : "Erreur inconnue lors du chargement du dashboard.";
  }

  const sorted = sortMatches(todayMatches, sort);
  const analyzedToday = todayMatches.filter((m) => m.prediction).length;

  return (
    <div className="mx-auto max-w-7xl space-y-8">
      <div>
        <h1 className="text-2xl font-bold">Dashboard</h1>
        <p className="mt-1 text-sm text-text-secondary">
          Vue d&apos;ensemble de l&apos;analyse statistique des matchs — probabilités, confiance et performance des modèles.
        </p>
      </div>

      {error && (
        <div className="card border-loss/40 bg-loss/10 p-4 text-sm text-loss">{error}</div>
      )}

      <div className="grid grid-cols-2 gap-4 md:grid-cols-3 xl:grid-cols-6">
        <StatTile label="Matchs analysés aujourd'hui" value={String(analyzedToday)} icon={BarChart3} />
        <StatTile label="Matchs à venir (7j)" value={String(upcomingCount)} icon={CalendarClock} />
        <StatTile
          label="Précision meilleur modèle"
          value={bestAccuracy !== null ? pct(bestAccuracy) : "—"}
          icon={Target}
        />
        <StatTile label="Brier Score" value={bestBrier !== null ? bestBrier.toFixed(3) : "—"} icon={TrendingUp} />
        <StatTile
          label="Modèle recommandé"
          value={bestModel ? MODEL_LABELS[bestModel] ?? bestModel : "—"}
          icon={Trophy}
        />
        <StatTile label="Matchs historiques" value={String(totalHistorical)} icon={Database} />
      </div>

      <div>
        <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
          <h2 className="text-lg font-semibold">Matchs du jour</h2>
          <div className="flex flex-wrap gap-1 rounded-lg border border-line bg-surface p-1 text-xs">
            {SORTS.map((s) => (
              <Link
                key={s.key}
                href={`/dashboard?sort=${s.key}`}
                className={`rounded-md px-2.5 py-1.5 ${
                  sort === s.key ? "bg-surface-2 text-text" : "text-text-secondary hover:text-text"
                }`}
              >
                {s.label}
              </Link>
            ))}
          </div>
        </div>

        {sorted.length === 0 ? (
          <div className="card p-8 text-center text-sm text-text-secondary">
            Aucun match aujourd&apos;hui dans les compétitions actuellement synchronisées.
          </div>
        ) : (
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {sorted.map((match) => (
              <MatchCard key={match.id} match={match} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
