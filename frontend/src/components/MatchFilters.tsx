"use client";

import { useRouter, useSearchParams, usePathname } from "next/navigation";
import { continentLabel } from "@/lib/format";

interface CompetitionOption {
  id: number;
  name: string;
  continent: string;
}

const CONTINENTS = ["AFRICA", "EUROPE", "SOUTH_AMERICA", "NORTH_AMERICA", "ASIA", "OCEANIA", "INTERNATIONAL"];

export function MatchFilters({ competitions }: { competitions: CompetitionOption[] }) {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();

  function setParam(key: string, value: string) {
    const params = new URLSearchParams(searchParams.toString());
    if (value) {
      params.set(key, value);
    } else {
      params.delete(key);
    }
    params.delete("page");
    router.push(`${pathname}?${params.toString()}`);
  }

  const continent = searchParams.get("continent") ?? "";
  const competitionId = searchParams.get("competition_id") ?? "";
  const filteredCompetitions = continent
    ? competitions.filter((c) => c.continent === continent)
    : competitions;

  return (
    <div className="flex flex-wrap gap-2">
      <select
        value={continent}
        onChange={(e) => setParam("continent", e.target.value)}
        className="rounded-lg border border-line bg-surface-2 px-3 py-2 text-sm text-text"
      >
        <option value="">Tous les continents</option>
        {CONTINENTS.map((c) => (
          <option key={c} value={c}>
            {continentLabel(c)}
          </option>
        ))}
      </select>

      <select
        value={competitionId}
        onChange={(e) => setParam("competition_id", e.target.value)}
        className="min-w-[180px] rounded-lg border border-line bg-surface-2 px-3 py-2 text-sm text-text"
      >
        <option value="">Toutes les compétitions</option>
        {filteredCompetitions.map((c) => (
          <option key={c.id} value={c.id}>
            {c.name}
          </option>
        ))}
      </select>
    </div>
  );
}
