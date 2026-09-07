import { FlaskConical, Radio } from "lucide-react";
import type { SystemStatus } from "@/lib/types";

export function DemoBanner({ status }: { status: SystemStatus | null }) {
  if (!status) return null;

  if (status.demo_mode) {
    return (
      <div className="flex items-center gap-2 border-b border-line bg-draw/10 px-4 py-2 text-xs text-draw sm:px-6">
        <FlaskConical size={14} />
        <span>
          <strong className="font-semibold">Mode démo</strong> — données fictives ({status.demo_matches_count} matchs)
          générées pour la démonstration. Configurez FOOTBALL_DATA_API_KEY pour passer en données réelles.
        </span>
      </div>
    );
  }

  return (
    <div className="flex items-center gap-2 border-b border-line bg-win/10 px-4 py-2 text-xs text-win sm:px-6">
      <Radio size={14} />
      <span>
        <strong className="font-semibold">Données réelles</strong> — {status.real_matches_count} matchs synchronisés
        depuis football-data.org.
      </span>
    </div>
  );
}
