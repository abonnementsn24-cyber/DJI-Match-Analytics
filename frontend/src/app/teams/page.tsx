import Link from "next/link";
import { Users } from "lucide-react";
import { api, ApiError } from "@/lib/api";
import { TeamSearch } from "@/components/TeamSearch";

export const dynamic = "force-dynamic";

export default async function TeamsPage({ searchParams }: PageProps<"/teams">) {
  const params = await searchParams;
  const search = typeof params.search === "string" ? params.search : undefined;
  const page = typeof params.page === "string" ? Number(params.page) : 1;
  const pageSize = 24;

  let error: string | null = null;
  let teams: Awaited<ReturnType<typeof api.teamsList>>["results"] = [];
  let total = 0;

  try {
    const response = await api.teamsList({ search, page, page_size: pageSize });
    teams = response.results;
    total = response.total;
  } catch (err) {
    error = err instanceof ApiError ? err.message : "Erreur lors du chargement des équipes.";
  }

  return (
    <div className="mx-auto max-w-5xl space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold">Équipes</h1>
          <p className="mt-1 text-sm text-text-secondary">{total} équipes connues.</p>
        </div>
        <TeamSearch />
      </div>

      {error && <div className="card border-loss/40 bg-loss/10 p-4 text-sm text-loss">{error}</div>}

      <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 md:grid-cols-4">
        {teams.map((team) => (
          <Link key={team.id} href={`/teams/${team.id}`} className="card card-hover flex items-center gap-2 p-3 text-sm">
            <Users size={16} className="shrink-0 text-accent" />
            <span className="truncate">{team.name}</span>
          </Link>
        ))}
      </div>

      {!error && teams.length === 0 && (
        <div className="card p-8 text-center text-sm text-text-secondary">Aucune équipe ne correspond à cette recherche.</div>
      )}
    </div>
  );
}
