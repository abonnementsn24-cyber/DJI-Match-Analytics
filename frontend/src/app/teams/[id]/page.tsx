import Link from "next/link";
import { notFound } from "next/navigation";
import { api, ApiError } from "@/lib/api";
import { FormStrip } from "@/components/FormStrip";
import { MatchCard } from "@/components/MatchCard";

export const dynamic = "force-dynamic";

export default async function TeamDetailPage({ params }: PageProps<"/teams/[id]">) {
  const { id } = await params;
  const teamId = Number(id);

  let team;
  try {
    team = await api.teamDetail(teamId);
  } catch (err) {
    if (err instanceof ApiError && err.status === 404) notFound();
    throw err;
  }

  const [form, recentMatches] = await Promise.all([
    api.teamForm(teamId).catch(() => null),
    api.matchesList({ tab: "finished", team_id: teamId, page_size: 6 }).catch(() => null),
  ]);

  return (
    <div className="mx-auto max-w-4xl space-y-6">
      <Link href="/teams" className="text-sm text-text-secondary hover:text-text">
        ← Toutes les équipes
      </Link>

      <div>
        <h1 className="text-2xl font-bold">{team.name}</h1>
        {form?.reliable && <p className="mt-1 text-sm text-text-secondary">Elo actuel: {form.elo_rating}</p>}
      </div>

      {!form?.reliable ? (
        <div className="card p-6 text-sm text-text-secondary">
          {form?.reason ?? "Données insuffisantes pour cette équipe."}
        </div>
      ) : (
        <>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div className="card p-4">
              <h2 className="mb-2 text-sm font-semibold text-text-secondary">Domicile</h2>
              <p className="text-sm">
                {form.home?.matches} matchs · {form.home?.goals_for} buts marqués · {form.home?.goals_against} encaissés
              </p>
            </div>
            <div className="card p-4">
              <h2 className="mb-2 text-sm font-semibold text-text-secondary">Extérieur</h2>
              <p className="text-sm">
                {form.away?.matches} matchs · {form.away?.goals_for} buts marqués · {form.away?.goals_against} encaissés
              </p>
            </div>
          </div>

          <div className="card p-4">
            <h2 className="mb-3 text-sm font-semibold text-text-secondary">Forme récente</h2>
            <div className="space-y-2 text-sm">
              <div>
                <span className="mr-2 text-text-secondary">5 derniers:</span>
                <FormStrip form={form.form?.["last_5"]} />
              </div>
              <div>
                <span className="mr-2 text-text-secondary">10 derniers:</span>
                <FormStrip form={form.form?.["last_10"]} />
              </div>
            </div>
          </div>
        </>
      )}

      <div>
        <h2 className="mb-3 text-lg font-semibold">Derniers résultats</h2>
        {recentMatches && recentMatches.results.length > 0 ? (
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            {recentMatches.results.map((m) => (
              <MatchCard key={m.id} match={m} />
            ))}
          </div>
        ) : (
          <p className="text-sm text-text-secondary">Aucun match terminé enregistré.</p>
        )}
      </div>
    </div>
  );
}
