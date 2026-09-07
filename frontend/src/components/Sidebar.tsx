"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { motion } from "framer-motion";
import { Activity } from "lucide-react";
import { NAV_LINKS } from "./nav-links";

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="sticky top-0 hidden h-screen w-64 shrink-0 flex-col border-r border-line bg-surface md:flex">
      <div className="flex items-center gap-2 px-6 py-6">
        <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-accent/15 text-accent">
          <Activity size={20} />
        </div>
        <div>
          <div className="text-sm font-bold leading-tight">EMDJI Match Analytics</div>
          <div className="text-[11px] leading-tight text-text-secondary">Football Intelligence</div>
        </div>
      </div>

      <nav className="flex-1 space-y-1 px-3">
        {NAV_LINKS.map((link) => {
          const active = pathname === link.href || pathname.startsWith(`${link.href}/`);
          const Icon = link.icon;
          return (
            <Link
              key={link.href}
              href={link.href}
              className={`relative flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm transition-colors ${
                active ? "text-text" : "text-text-secondary hover:text-text"
              }`}
            >
              {active && (
                <motion.div
                  layoutId="sidebar-active"
                  className="absolute inset-0 rounded-lg bg-surface-2"
                  transition={{ duration: 0.2 }}
                />
              )}
              <Icon size={18} className="relative z-10" />
              <span className="relative z-10">{link.label}</span>
            </Link>
          );
        })}
      </nav>

      <div className="border-t border-line px-6 py-4 text-[11px] text-text-secondary">
        Analyse statistique uniquement.
        <br />
        Aucun pari, aucune cote.
      </div>
    </aside>
  );
}
