import { pct } from "@/lib/format";

interface ProbabilityBarProps {
  home: number;
  draw: number;
  away: number;
  homeLabel?: string;
  awayLabel?: string;
}

export function ProbabilityBar({ home, draw, away, homeLabel = "1", awayLabel = "2" }: ProbabilityBarProps) {
  return (
    <div className="w-full">
      <div className="flex h-2.5 w-full overflow-hidden rounded-full bg-surface-2">
        <div style={{ width: `${home * 100}%` }} className="bg-win" title={`${homeLabel}: ${pct(home)}`} />
        <div style={{ width: `${draw * 100}%` }} className="bg-draw" title={`Nul: ${pct(draw)}`} />
        <div style={{ width: `${away * 100}%` }} className="bg-loss" title={`${awayLabel}: ${pct(away)}`} />
      </div>
      <div className="mt-1.5 flex justify-between text-xs text-text-secondary">
        <span className="text-win font-medium">{pct(home)}</span>
        <span className="text-draw font-medium">{pct(draw)}</span>
        <span className="text-loss font-medium">{pct(away)}</span>
      </div>
    </div>
  );
}
