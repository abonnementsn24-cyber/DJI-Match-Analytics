import type { Confidence } from "./types";

export function pct(value: number | null | undefined, digits = 0): string {
  if (value === null || value === undefined) return "—";
  return `${(value * 100).toFixed(digits)} %`;
}

export const CONFIDENCE_LABELS: Record<Confidence, string> = {
  VERY_LOW: "Très faible",
  LOW: "Faible",
  MEDIUM: "Moyenne",
  HIGH: "Élevée",
  VERY_HIGH: "Très élevée",
  INSUFFICIENT_DATA: "Données insuffisantes",
};

export const CONFIDENCE_COLORS: Record<Confidence, string> = {
  VERY_LOW: "text-loss",
  LOW: "text-draw",
  MEDIUM: "text-text-secondary",
  HIGH: "text-accent",
  VERY_HIGH: "text-win",
  INSUFFICIENT_DATA: "text-text-secondary",
};

export const MODEL_LABELS: Record<string, string> = {
  basic: "Poisson Basic",
  form: "Poisson Form",
  elo: "Elo Model",
  ensemble: "Ensemble",
  ml: "Machine Learning",
};

export function formatDateTime(iso: string): string {
  const date = new Date(iso);
  return date.toLocaleString("fr-FR", {
    weekday: "short",
    day: "2-digit",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function formatTime(iso: string): string {
  const date = new Date(iso);
  return date.toLocaleTimeString("fr-FR", { hour: "2-digit", minute: "2-digit" });
}

export function continentLabel(code: string): string {
  const labels: Record<string, string> = {
    AFRICA: "Afrique",
    EUROPE: "Europe",
    SOUTH_AMERICA: "Amérique du Sud",
    NORTH_AMERICA: "Amérique du Nord",
    ASIA: "Asie",
    OCEANIA: "Océanie",
    INTERNATIONAL: "International",
  };
  return labels[code] ?? code;
}
