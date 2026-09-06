import Link from "next/link";
import { api, ApiError } from "@/lib/api";
import { MatchCard } from "@/components/MatchCard";
import { MatchFilters } from "@/components/MatchFilters";

export const dynamic = "force-dynamic";

const TABS = [
  { key: "today", label: "Aujourd'hui" },
  { key: "tomorrow", label: "Demain" },
  { key: "week", label: "Cette semaine" },
  { key: "finished", label: "Terminés" },
] as const;

export default async function MatchesPage({ searchParams }: PageProps<"/matches">) {
  const params = await searchParams;
  const tab = typeof params.tab === "string" ? params.tab : "today";
  const continent = typeof params.continent === "string" ? params.continent : undefined;
  const competitionId = typeof params.competition_id === "string" ? Number(params.competition_id) : undefined;
  const page = typeof params.page === "string" ? Number(params.page) : 1;

  let error: string | null = null;
  let results: Awaited<ReturnType<typeof api.matchesList>>["results"] = [];
  let total = 0;
  const pageSize = 12;
  let competitionOptions: { id: number; name: string; continent: string }[] = [];

  try {
    const [matches, tree] = await Promise.all([
      api.matchesList({ tab, continent, competition_id: competitionId, page, page_size: pageSize }),
      api.competitionsTree(),
    ]);
    results = matches.results;
    total = matches.total;
    competitionOptions = tree.flatMap((node) =>
      node.countries.flatMap((country) =>
        country.competitions.map((c) => ({ id: c.id, name: c.name, continent: node.continent }))
      )
    );
  } catch (err) {
    error = err instanceof ApiError ? err.message : "Erreur lors du chargement des matchs.";
  }

  const totalPages = Math.max(1, Math.ceil(total / pageSize));
  const queryFor = (overrides: Record<string, string | number | undefined>) => {
    const p = new URLSearchParams();
    if (tab) p.set("tab", tab);
    if (continent) p.set("continent", continent);
    if (competitionId) p.set("competition_id", String(competitionId));
    Object.entries(overrides).forEach(([k, v]) => {
      if (v === undefined) p.delete(k);
      else p.set(k, String(v));
    });
    return `?${p.toString()}`;
  };

  return (
    <div className="mx-auto max-w-7xl space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Match Center</h1>
        <p className="mt-1 text-sm text-text-secondary">
          Tous les matchs des compétitions synchronisées, filtrables par continent, pays, compétition ou équipe.
        </p>
      </div>

      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex flex-wrap gap-1 rounded-lg border border-line bg-surface p-1 text-sm">
          {TABS.map((t) => (
            <Link
              key={t.key}
              href={queryFor({ tab: t.key, page: undefined })}
              className={`rounded-md px-3 py-1.5 ${
                tab === t.key ? "bg-surface-2 text-text" : "text-text-secondary hover:text-text"
              }`}
            >
              {t.label}
            </Link>
          ))}
        </div>
        <MatchFilters competitions={competitionOptions} />
      </div>

      {error && <div className="card border-loss/40 bg-loss/10 p-4 text-sm text-loss">{error}</div>}

      {!error && results.length === 0 && (
        <div className="card p-8 text-center text-sm text-text-secondary">Aucun match pour ces critères.</div>
      )}

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {results.map((match) => (
          <MatchCard key={match.id} match={match} />
        ))}
      </div>

      {totalPages > 1 && (
        <div className="flex items-center justify-center gap-2 text-sm">
          <Link
            href={queryFor({ page: Math.max(1, page - 1) })}
            className="rounded-lg border border-line px-3 py-1.5 text-text-secondary hover:text-text"
          >
            Précédent
          </Link>
          <span className="text-text-secondary">
            Page {page} / {totalPages}
          </span>
          <Link
            href={queryFor({ page: Math.min(totalPages, page + 1) })}
            className="rounded-lg border border-line px-3 py-1.5 text-text-secondary hover:text-text"
          >
            Suivant
          </Link>
        </div>
      )}
    </div>
  );
}
