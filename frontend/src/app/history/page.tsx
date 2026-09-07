import Link from "next/link";
import { api, ApiError } from "@/lib/api";
import { MODEL_LABELS, pct } from "@/lib/format";

export const dynamic = "force-dynamic";

const MODEL_TABS = ["ensemble", "basic", "form", "elo", "ml"];

export default async function HistoryPage({ searchParams }: PageProps<"/history">) {
  const params = await searchParams;
  const model = typeof params.model === "string" ? params.model : "ensemble";
  const page = typeof params.page === "string" ? Number(params.page) : 1;
  const pageSize = 20;

  let error: string | null = null;
  let results: Awaited<ReturnType<typeof api.matchesList>>["results"] = [];
  let total = 0;

  try {
    const response = await api.matchesList({ tab: "finished", model, page, page_size: pageSize });
    results = response.results;
    total = response.total;
  } catch (err) {
    error = err instanceof ApiError ? err.message : "Erreur lors du chargement de l'historique.";
  }

  const totalPages = Math.max(1, Math.ceil(total / pageSize));
  const correctCount = results.filter((m) => m.prediction?.correct).length;

  return (
    <div className="mx-auto max-w-5xl space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Historique des prédictions</h1>
        <p className="mt-1 text-sm text-text-secondary">
          Chaque prédiction est enregistrée avant le coup d&apos;envoi et n&apos;est jamais modifiée après coup — seul
          le résultat réel est ajouté une fois le match terminé.
        </p>
      </div>

      <div className="flex flex-wrap gap-1 rounded-lg border border-line bg-surface p-1 text-sm">
        {MODEL_TABS.map((m) => (
          <Link
            key={m}
            href={`/history?model=${m}`}
            className={`rounded-md px-3 py-1.5 ${model === m ? "bg-surface-2 text-text" : "text-text-secondary hover:text-text"}`}
          >
            {MODEL_LABELS[m]}
          </Link>
        ))}
      </div>

      {error && <div className="card border-loss/40 bg-loss/10 p-4 text-sm text-loss">{error}</div>}

      <div className="card overflow-x-auto p-4">
        <div className="mb-3 text-xs text-text-secondary">
          {results.length} prédictions affichées · {correctCount} correctes sur cette page
        </div>
        <table className="w-full min-w-[720px] text-sm">
          <thead>
            <tr className="text-left text-xs text-text-secondary">
              <th className="p-2">Date</th>
              <th className="p-2">Match</th>
              <th className="p-2">Généré le</th>
              <th className="p-2">1 / N / 2</th>
              <th className="p-2">Résultat</th>
              <th className="p-2 text-center">Correct</th>
            </tr>
          </thead>
          <tbody>
            {results.map((m) => (
              <tr key={m.id} className="border-t border-line">
                <td className="p-2 text-text-secondary">{new Date(m.utc_date).toLocaleDateString("fr-FR")}</td>
                <td className="p-2">
                  <Link href={`/matches/${m.id}`} className="hover:text-accent">
                    {m.home_team?.name} vs {m.away_team?.name}
                  </Link>
                </td>
                <td className="p-2 text-text-secondary">
                  {m.prediction ? new Date(m.prediction.generated_at).toLocaleDateString("fr-FR") : "—"}
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
        {results.length === 0 && <p className="py-6 text-center text-sm text-text-secondary">Aucune prédiction évaluée.</p>}
      </div>

      {totalPages > 1 && (
        <div className="flex items-center justify-center gap-2 text-sm">
          <Link
            href={`/history?model=${model}&page=${Math.max(1, page - 1)}`}
            className="rounded-lg border border-line px-3 py-1.5 text-text-secondary hover:text-text"
          >
            Précédent
          </Link>
          <span className="text-text-secondary">
            Page {page} / {totalPages}
          </span>
          <Link
            href={`/history?model=${model}&page=${Math.min(totalPages, page + 1)}`}
            className="rounded-lg border border-line px-3 py-1.5 text-text-secondary hover:text-text"
          >
            Suivant
          </Link>
        </div>
      )}
    </div>
  );
}
