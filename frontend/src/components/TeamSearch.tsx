"use client";

import { useRouter, usePathname, useSearchParams } from "next/navigation";
import { Search } from "lucide-react";

export function TeamSearch() {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();

  return (
    <div className="relative">
      <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-text-secondary" />
      <input
        defaultValue={searchParams.get("search") ?? ""}
        onChange={(e) => {
          const params = new URLSearchParams(searchParams.toString());
          if (e.target.value) params.set("search", e.target.value);
          else params.delete("search");
          params.delete("page");
          router.push(`${pathname}?${params.toString()}`);
        }}
        placeholder="Rechercher une équipe..."
        className="w-full rounded-lg border border-line bg-surface-2 py-2 pl-9 pr-3 text-sm text-text placeholder:text-text-secondary sm:w-72"
      />
    </div>
  );
}
