import Link from "next/link";
import { notFound } from "next/navigation";
import { api, ApiError } from "@/lib/api";
import { continentLabel } from "@/lib/format";

export const dynamic = "force-dynamic";

const TABS = [
  { key: "standings", label: "Classement" },
  { key: "matches", label: "Calendrier & résultats" },
  { key: "teams", label: "Équipes" },
] as const;

export default async function CompetitionDetailPage({
  params,
  searchParams,
}: PageProps<"/competitions/[id]">) {
  const { id } = await params;
  const search = await searchParams;
  const tab = typeof search.tab === "string" ? search.tab : "standings";
  const competitionId = Number(id);

  let competition;
  try {
    competition = await api.competitionDetail(competitionId);
  } catch (err) {
    if (err instanceof ApiError && err.status === 404) notFound();
    throw err;
  }

  const [standings, matches, teams] = await Promise.all([
    api.competitionStandings(competitionId).catch(() => []),
    api.competitionMatches(competitionId).catch(() => []),
    api.competitionTeams(competitionId).catch(() => []),
  ]);

  const finishedMatches = matches.filter((m) => m.status === "FINISHED").slice(-15).reverse();
  const upcomingMatches = matches.filter((m) => m.status !== "FINISHED").slice(0, 15);

  return (
    <div className="mx-auto max-w-5xl space-y-6">
      <Link href="/competitions" className="text-sm text-text-secondary hover:text-text">
        ← Toutes les compétitions
      </Link>

      <div>
        <h1 className="text-2xl font-bold">{competition.name}</h1>
        <p className="mt-1 text-sm text-text-secondary">
          {competition.country} · {continentLabel(competition.continent)} · Qualité des données:{" "}
          {competition.data_quality}
        </p>
      </div>

      <div className="flex flex-wrap gap-1 rounded-lg border border-line bg-surface p-1 text-sm">
        {TABS.map((t) => (
          <Link
            key={t.key}
            href={`/competitions/${competitionId}?tab=${t.key}`}
            className={`rounded-md px-3 py-1.5 ${
              tab === t.key ? "bg-surface-2 text-text" : "text-text-secondary hover:text-text"
            }`}
          >
            {t.label}
          </Link>
        ))}
      </div>

      {tab === "standings" && (
        <div className="card overflow-x-auto p-4">
          <table className="w-full min-w-[480px] text-sm">
            <thead>
              <tr className="text-left text-xs text-text-secondary">
                <th className="pb-2">#</th>
                <th className="pb-2">Équipe</th>
                <th className="pb-2 text-center">J</th>
                <th className="pb-2 text-center">V</th>
                <th className="pb-2 text-center">N</th>
                <th className="pb-2 text-center">D</th>
                <th className="pb-2 text-center">BP</th>
                <th className="pb-2 text-center">BC</th>
                <th className="pb-2 text-center">Diff</th>
                <th className="pb-2 text-center">Pts</th>
              </tr>
            </thead>
            <tbody>
              {standings.map((row, i) => (
                <tr key={row.team_id} className="border-t border-line">
                  <td className="py-2 text-text-secondary">{i + 1}</td>
                  <td className="py-2 font-medium">
                    <Link href={`/teams/${row.team_id}`} className="hover:text-accent">
                      {row.team}
                    </Link>
                  </td>
                  <td className="py-2 text-center">{row.played}</td>
                  <td className="py-2 text-center">{row.wins}</td>
                  <td className="py-2 text-center">{row.draws}</td>
                  <td className="py-2 text-center">{row.losses}</td>
                  <td className="py-2 text-center">{row.goals_for}</td>
                  <td className="py-2 text-center">{row.goals_against}</td>
                  <td className="py-2 text-center">{row.goal_difference}</td>
                  <td className="py-2 text-center font-bold">{row.points}</td>
                </tr>
              ))}
            </tbody>
          </table>
          {standings.length === 0 && (
            <p className="py-6 text-center text-sm text-text-secondary">Aucun match terminé pour établir un classement.</p>
          )}
        </div>
      )}

      {tab === "matches" && (
        <div className="space-y-6">
          <div className="card p-4">
            <h2 className="mb-2 text-sm font-semibold text-text-secondary">À venir</h2>
            <ul className="divide-y divide-line">
              {upcomingMatches.map((m) => (
                <li key={m.id}>
                  <Link href={`/matches/${m.id}`} className="flex items-center justify-between px-1 py-2 text-sm hover:text-accent">
                    <span>
                      {m.home_team?.name} vs {m.away_team?.name}
                    </span>
                    <span className="text-text-secondary">{new Date(m.utc_date).toLocaleDateString("fr-FR")}</span>
                  </Link>
                </li>
              ))}
              {upcomingMatches.length === 0 && <li className="py-3 text-sm text-text-secondary">Aucun match à venir.</li>}
            </ul>
          </div>
          <div className="card p-4">
            <h2 className="mb-2 text-sm font-semibold text-text-secondary">Résultats récents</h2>
            <ul className="divide-y divide-line">
              {finishedMatches.map((m) => (
                <li key={m.id}>
                  <Link href={`/matches/${m.id}`} className="flex items-center justify-between px-1 py-2 text-sm hover:text-accent">
                    <span>
                      {m.home_team?.name} {m.home_goals} - {m.away_goals} {m.away_team?.name}
                    </span>
                    <span className="text-text-secondary">{new Date(m.utc_date).toLocaleDateString("fr-FR")}</span>
                  </Link>
                </li>
              ))}
              {finishedMatches.length === 0 && <li className="py-3 text-sm text-text-secondary">Aucun résultat.</li>}
            </ul>
          </div>
        </div>
      )}

      {tab === "teams" && (
        <div className="card p-4">
          <div className="grid grid-cols-2 gap-2 sm:grid-cols-3">
            {teams.map((t) => (
              <Link
                key={t.id}
                href={`/teams/${t.id}`}
                className="rounded-lg px-3 py-2 text-sm hover:bg-surface-2"
              >
                {t.name}
              </Link>
            ))}
          </div>
          {teams.length === 0 && <p className="text-sm text-text-secondary">Aucune équipe synchronisée.</p>}
        </div>
      )}
    </div>
  );
}
