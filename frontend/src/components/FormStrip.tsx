import type { TeamFormSummary } from "@/lib/types";

const RESULT_COLORS: Record<string, string> = {
  V: "bg-win text-bg",
  N: "bg-draw text-bg",
  D: "bg-loss text-bg",
};

export function FormStrip({
  form,
  results,
}: {
  form: TeamFormSummary | null | undefined;
  results?: string[];
}) {
  if (!form) {
    return <span className="text-xs text-text-secondary">Pas assez de données</span>;
  }

  return (
    <div className="flex items-center gap-3">
      {results && (
        <div className="flex gap-1">
          {results.map((r, i) => (
            <span
              key={i}
              className={`flex h-5 w-5 items-center justify-center rounded-full text-[10px] font-bold ${RESULT_COLORS[r] ?? "bg-surface-2"}`}
            >
              {r}
            </span>
          ))}
        </div>
      )}
      <span className="text-xs text-text-secondary">
        {form.goals_for}-{form.goals_against} buts · {form.points_per_match.toFixed(2)} pts/match
      </span>
    </div>
  );
}
