"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { NAV_LINKS } from "./nav-links";

export function MobileNav() {
  const pathname = usePathname();

  return (
    <nav className="sticky bottom-0 z-20 flex overflow-x-auto border-t border-line bg-surface md:hidden">
      {NAV_LINKS.map((link) => {
        const active = pathname === link.href || pathname.startsWith(`${link.href}/`);
        const Icon = link.icon;
        return (
          <Link
            key={link.href}
            href={link.href}
            className={`flex min-w-[72px] flex-1 flex-col items-center gap-1 px-2 py-2.5 text-[10px] ${
              active ? "text-accent" : "text-text-secondary"
            }`}
          >
            <Icon size={18} />
            {link.label}
          </Link>
        );
      })}
    </nav>
  );
}
