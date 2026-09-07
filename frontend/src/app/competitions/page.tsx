import Link from "next/link";
import { AlertTriangle, RefreshCw, Trophy } from "lucide-react";
import { api, ApiError } from "@/lib/api";
import { continentLabel } from "@/lib/format";

export const dynamic = "force-dynamic";

const QUALITY_LABELS: Record<string, string> = {
  A: "Historique riche",
  B: "Historique correct",
  C: "Peu de données",
  D: "Données insuffisantes",
};

export default async function CompetitionsPage() {
  let tree: Awaited<ReturnType<typeof api.competitionsTree>> = [];
  let popular: Awaited<ReturnType<typeof api.popularLeagues>> | null = null;
  let error: string | null = null;

  try {
    [tree, popular] = await Promise.all([api.competitionsTree(), api.popularLeagues()]);
  } catch (err) {
    error = err instanceof ApiError ? err.message : "Erreur lors du chargement des compétitions.";
  }

  const totalCompetitions = tree.reduce(
    (sum, node) => sum + node.countries.reduce((s, c) => s + c.competitions.length, 0),
    0
  );

  return (
    <div className="mx-auto max-w-6xl space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Compétitions du monde</h1>
        <p className="mt-1 text-sm text-text-secondary">
          {totalCompetitions} compétitions découvertes automatiquement auprès des fournisseurs de données configurés —
          aucune liste manuelle. Une nouvelle compétition apparaît ici dès qu&apos;elle est publiée par le fournisseur.
        </p>
      </div>

      {error && <div className="card border-loss/40 bg-loss/10 p-4 text-sm text-loss">{error}</div>}

      {popular && (
        <div className="card p-4">
          <div className="mb-3 flex items-center gap-2">
            <RefreshCw size={16} className="text-accent" />
            <h2 className="text-lg font-semibold">Championnats populaires</h2>
            <span className="text-xs text-text-secondary">— synchronisation automatique en priorité</span>
          </div>
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {popular.leagues.map((league) => {
              const content = (
                <>
                  <div>
                    <div className="text-sm font-medium">{league.label}</div>
                    <div className="text-xs text-text-secondary">{league.country}</div>
                  </div>
                  <span
                    className={`shrink-0 rounded-full px-2 py-0.5 text-[10px] ${
                      league.synced ? "bg-win/15 text-win" : "bg-surface-2 text-text-secondary"
                    }`}
                  >
                    {league.synced ? "Synchronisé" : "Non synchronisé"}
                  </span>
                </>
              );
              return league.competition_id ? (
                <Link
                  key={league.code}
                  href={`/competitions/${league.competition_id}`}
                  className="flex items-center justify-between rounded-lg border border-line px-3 py-2 hover:bg-surface-2"
                >
                  {content}
                </Link>
              ) : (
                <div
                  key={league.code}
                  className="flex items-center justify-between rounded-lg border border-line px-3 py-2 opacity-70"
                >
                  {content}
                </div>
              );
            })}
          </div>

          {popular.unavailable.length > 0 && (
            <div className="mt-4 flex items-start gap-2 rounded-lg border border-draw/30 bg-draw/10 px-3 py-2 text-xs text-draw">
              <AlertTriangle size={14} className="mt-0.5 shrink-0" />
              <ul className="space-y-0.5">
                {popular.unavailable.map((u) => (
                  <li key={u.requested}>
                    <strong>{u.requested}</strong> : {u.reason}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      <div className="space-y-6">
        {tree.map((node) => (
          <div key={node.continent}>
            <h2 className="mb-3 text-lg font-semibold">{continentLabel(node.continent)}</h2>
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {node.countries.map((country) => (
                <div key={country.country} className="card p-4">
                  <div className="mb-2 text-sm font-semibold text-text-secondary">
                    {country.country_id ? (
                      <Link href={`/countries/${country.country_id}`} className="hover:text-text">
                        {country.country}
                      </Link>
                    ) : (
                      country.country
                    )}
                  </div>
                  <ul className="space-y-2">
                    {country.competitions.map((c) => (
                      <li key={c.id}>
                        <Link
                          href={`/competitions/${c.id}`}
                          className="flex items-center justify-between rounded-lg px-2 py-1.5 text-sm hover:bg-surface-2"
                        >
                          <span className="flex items-center gap-2 truncate">
                            <Trophy size={14} className="shrink-0 text-accent" />
                            <span className="truncate">{c.name}</span>
                          </span>
                          <span
                            className="ml-2 shrink-0 rounded-full border border-line px-2 py-0.5 text-[10px] text-text-secondary"
                            title={QUALITY_LABELS[c.data_quality]}
                          >
                            {c.data_quality}
                          </span>
                        </Link>
                      </li>
                    ))}
                  </ul>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
