export function EloCompare({
  homeRating,
  awayRating,
  homeName,
  awayName,
}: {
  homeRating: number;
  awayRating: number;
  homeName: string;
  awayName: string;
}) {
  const total = homeRating + awayRating;
  const homeShare = total > 0 ? (homeRating / total) * 100 : 50;

  return (
    <div>
      <div className="flex justify-between text-sm font-medium">
        <span>{homeName}: {homeRating.toFixed(0)}</span>
        <span>{awayName}: {awayRating.toFixed(0)}</span>
      </div>
      <div className="mt-2 flex h-2 overflow-hidden rounded-full bg-surface-2">
        <div style={{ width: `${homeShare}%` }} className="bg-accent" />
        <div style={{ width: `${100 - homeShare}%` }} className="bg-accent-strong opacity-50" />
      </div>
      <div className="mt-1 text-center text-xs text-text-secondary">
        Écart: {Math.abs(homeRating - awayRating).toFixed(0)} points
      </div>
    </div>
  );
}
