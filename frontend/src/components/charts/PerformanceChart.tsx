"use client";

import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { MonthlyPoint } from "@/lib/types";

export function PerformanceChart({ data }: { data: MonthlyPoint[] }) {
  if (data.length === 0) {
    return <div className="flex h-64 items-center justify-center text-sm text-text-secondary">Pas encore assez d&apos;historique évalué.</div>;
  }

  return (
    <ResponsiveContainer width="100%" height={260}>
      <LineChart data={data} margin={{ top: 8, right: 16, left: -16, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#223D60" />
        <XAxis dataKey="month" stroke="#91A6C0" fontSize={12} />
        <YAxis yAxisId="left" domain={[0, 1]} stroke="#91A6C0" fontSize={12} />
        <YAxis yAxisId="right" orientation="right" domain={[0, "auto"]} stroke="#91A6C0" fontSize={12} />
        <Tooltip
          contentStyle={{ background: "#10243D", border: "1px solid #223D60", borderRadius: 8, fontSize: 12 }}
        />
        <Legend wrapperStyle={{ fontSize: 12 }} />
        <Line yAxisId="left" type="monotone" dataKey="accuracy" name="Accuracy" stroke="#3EC6F0" strokeWidth={2} dot={false} />
        <Line yAxisId="right" type="monotone" dataKey="brier_score" name="Brier Score" stroke="#e0605a" strokeWidth={2} dot={false} />
      </LineChart>
    </ResponsiveContainer>
  );
}
