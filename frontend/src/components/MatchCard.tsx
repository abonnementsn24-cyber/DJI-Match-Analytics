import Link from "next/link";
import { ProbabilityBar } from "./ProbabilityBar";
import { ConfidenceBadge } from "./ConfidenceBadge";
import { formatTime, continentLabel } from "@/lib/format";
import type { MatchSummary } from "@/lib/types";

function TeamCrest({ logo, name }: { logo: string | null; name: string }) {
  if (logo) {
    // eslint-disable-next-line @next/next/no-img-element
    return <img src={logo} alt={name} className="h-6 w-6 object-contain" />;
  }
  return (
    <div className="flex h-6 w-6 items-center justify-center rounded-full bg-surface-2 text-[10px] font-semibold text-text-secondary">
      {name.slice(0, 2).toUpperCase()}
    </div>
  );
}

export function MatchCard({ match }: { match: MatchSummary }) {
  const prediction = match.prediction;
  const isFinished = match.status === "FINISHED";

  return (
    <Link
      href={`/matches/${match.id}`}
      className="card card-hover flex flex-col gap-3 p-4"
    >
      <div className="flex items-center justify-between text-xs text-text-secondary">
        <span className="truncate">
          {match.competition?.name ?? "Compétition inconnue"}
          {match.competition && <span className="ml-1 opacity-70">· {continentLabel(match.competition.continent)}</span>}
        </span>
        <span>{formatTime(match.utc_date)}</span>
      </div>

      <div className="flex items-center justify-between gap-2">
        <div className="flex min-w-0 flex-1 items-center gap-2">
          <TeamCrest logo={match.home_team?.logo ?? null} name={match.home_team?.name ?? "?"} />
          <span className="truncate text-sm font-medium">{match.home_team?.name ?? "?"}</span>
        </div>
        {isFinished ? (
          <span className="shrink-0 text-sm font-bold">
            {match.home_goals} - {match.away_goals}
          </span>
        ) : (
          <span className="shrink-0 text-xs text-text-secondary">vs</span>
        )}
        <div className="flex min-w-0 flex-1 items-center justify-end gap-2 text-right">
          <span className="truncate text-sm font-medium">{match.away_team?.name ?? "?"}</span>
          <TeamCrest logo={match.away_team?.logo ?? null} name={match.away_team?.name ?? "?"} />
        </div>
      </div>

      {prediction ? (
        <>
          <ProbabilityBar
            home={prediction.home_win_probability}
            draw={prediction.draw_probability}
            away={prediction.away_win_probability}
          />
          <div className="flex items-center justify-between">
            <ConfidenceBadge confidence={prediction.confidence} />
            <span className="text-xs text-text-secondary">
              BTTS {(prediction.btts_probability * 100).toFixed(0)} %
            </span>
          </div>
        </>
      ) : (
        <div className="rounded-lg border border-line bg-surface-2 px-3 py-2 text-xs text-text-secondary">
          Données insuffisantes pour une estimation fiable.
        </div>
      )}
    </Link>
  );
}
