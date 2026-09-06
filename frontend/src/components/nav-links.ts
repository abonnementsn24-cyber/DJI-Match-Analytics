import type { LucideIcon } from "lucide-react";
import {
  BarChart3,
  Beaker,
  Globe2,
  History,
  LayoutDashboard,
  Settings,
  ShieldCheck,
  Users,
} from "lucide-react";

export interface NavLink {
  href: string;
  label: string;
  icon: LucideIcon;
}

export const NAV_LINKS: NavLink[] = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/matches", label: "Matchs", icon: BarChart3 },
  { href: "/competitions", label: "Compétitions", icon: Globe2 },
  { href: "/teams", label: "Équipes", icon: Users },
  { href: "/models", label: "Model Lab", icon: Beaker },
  { href: "/backtesting", label: "Backtesting", icon: ShieldCheck },
  { href: "/history", label: "Historique", icon: History },
  { href: "/settings", label: "Paramètres", icon: Settings },
];
