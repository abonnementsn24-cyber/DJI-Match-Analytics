"use client";

import { useRouter, usePathname, useSearchParams } from "next/navigation";

const CONFIDENCE_OPTIONS = [
  { value: "", label: "Toutes confiances" },
  { value: "VERY_HIGH", label: "Très élevée" },
  { value: "HIGH", label: "Élevée" },
  { value: "MEDIUM", label: "Moyenne" },
  { value: "LOW", label: "Faible" },
  { value: "VERY_LOW", label: "Très faible" },
];

export function BacktestFilters({ competitions }: { competitions: { id: number; name: string }[] }) {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();

  function setParam(key: string, value: string) {
    const params = new URLSearchParams(searchParams.toString());
    if (value) params.set(key, value);
    else params.delete(key);
    router.push(`${pathname}?${params.toString()}`);
  }

  return (
    <div className="flex flex-wrap gap-2">
      <select
        value={searchParams.get("competition_id") ?? ""}
        onChange={(e) => setParam("competition_id", e.target.value)}
        className="min-w-[200px] rounded-lg border border-line bg-surface-2 px-3 py-2 text-sm text-text"
      >
        <option value="">Toutes les compétitions</option>
        {competitions.map((c) => (
          <option key={c.id} value={c.id}>
            {c.name}
          </option>
        ))}
      </select>

      <select
        value={searchParams.get("min_confidence") ?? ""}
        onChange={(e) => setParam("min_confidence", e.target.value)}
        className="rounded-lg border border-line bg-surface-2 px-3 py-2 text-sm text-text"
      >
        {CONFIDENCE_OPTIONS.map((o) => (
          <option key={o.value} value={o.value}>
            {o.label}
          </option>
        ))}
      </select>
    </div>
  );
}
