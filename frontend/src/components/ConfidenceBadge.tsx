import { CONFIDENCE_COLORS, CONFIDENCE_LABELS } from "@/lib/format";
import type { Confidence } from "@/lib/types";
import { Gauge } from "lucide-react";

export function ConfidenceBadge({ confidence }: { confidence: Confidence }) {
  return (
    <span
      className={`inline-flex items-center gap-1 rounded-full border border-line bg-surface-2 px-2.5 py-1 text-xs font-medium ${CONFIDENCE_COLORS[confidence]}`}
    >
      <Gauge size={12} />
      {CONFIDENCE_LABELS[confidence]}
    </span>
  );
}
