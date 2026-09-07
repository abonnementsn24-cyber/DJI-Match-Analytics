import type { ClassificationReport } from "@/lib/types";

export function ConfusionMatrix({ report }: { report: ClassificationReport }) {
  const labelsFr: Record<string, string> = { HOME: "Domicile", DRAW: "Nul", AWAY: "Extérieur" };

  return (
    <div className="overflow-x-auto">
      <table className="w-full min-w-[360px] text-center text-sm">
        <thead>
          <tr>
            <th className="p-2 text-xs text-text-secondary">Réel \ Prédit</th>
            {report.labels.map((l) => (
              <th key={l} className="p-2 text-xs text-text-secondary">
                {labelsFr[l]}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {report.confusion_matrix.map((row, i) => (
            <tr key={i} className="border-t border-line">
              <td className="p-2 text-xs font-medium text-text-secondary">{labelsFr[report.labels[i]]}</td>
              {row.map((cell, j) => (
                <td
                  key={j}
                  className="p-2 font-semibold"
                  style={{ background: i === j ? "rgba(52,199,123,0.12)" : undefined }}
                >
                  {cell}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
