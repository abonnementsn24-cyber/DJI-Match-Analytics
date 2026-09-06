import { MODEL_LABELS, pct } from "@/lib/format";
import type { Prediction } from "@/lib/types";

const ORDER = ["basic", "form", "elo", "ensemble", "ml"];

export function ModelComparisonTable({ models }: { models: Record<string, Prediction> }) {
  const names = ORDER.filter((name) => models[name]);

  return (
    <div className="overflow-x-auto">
      <table className="w-full min-w-[480px] text-sm">
        <thead>
          <tr className="text-left text-xs text-text-secondary">
            <th className="pb-2">Modèle</th>
            <th className="pb-2">Domicile</th>
            <th className="pb-2">Nul</th>
            <th className="pb-2">Extérieur</th>
            <th className="pb-2">Score probable</th>
          </tr>
        </thead>
        <tbody>
          {names.map((name) => {
            const p = models[name];
            return (
              <tr key={name} className="border-t border-line">
                <td className="py-2 font-medium">{MODEL_LABELS[name] ?? name}</td>
                <td className="py-2 text-win">{pct(p.home_win_probability)}</td>
                <td className="py-2 text-draw">{pct(p.draw_probability)}</td>
                <td className="py-2 text-loss">{pct(p.away_win_probability)}</td>
                <td className="py-2 text-text-secondary">{p.top_scores[0]?.score ?? "—"}</td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
