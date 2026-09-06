import Link from "next/link";
import { notFound } from "next/navigation";
import { Trophy } from "lucide-react";
import { api, ApiError } from "@/lib/api";
import { continentLabel } from "@/lib/format";
import type { CountryDetail } from "@/lib/types";

export const dynamic = "force-dynamic";

export default async function CountryPage({ params }: PageProps<"/countries/[id]">) {
  const { id } = await params;
  let country: CountryDetail;
  try {
    country = await api.countryDetail(Number(id));
  } catch (err) {
    if (err instanceof ApiError && err.status === 404) notFound();
    throw err;
  }

  return (
    <div className="mx-auto max-w-4xl space-y-6">
      <Link href="/competitions" className="text-sm text-text-secondary hover:text-text">
        ← Toutes les compétitions
      </Link>

      <div>
        <h1 className="text-2xl font-bold">{country.name}</h1>
        <p className="mt-1 text-sm text-text-secondary">{continentLabel(country.continent)}</p>
      </div>

      <div className="card p-4">
        <h2 className="mb-3 text-sm font-semibold text-text-secondary">Compétitions</h2>
        <ul className="space-y-1">
          {country.competitions.map((c) => (
            <li key={c.id}>
              <Link
                href={`/competitions/${c.id}`}
                className="flex items-center gap-2 rounded-lg px-2 py-2 text-sm hover:bg-surface-2"
              >
                <Trophy size={14} className="text-accent" />
                {c.name}
              </Link>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}
