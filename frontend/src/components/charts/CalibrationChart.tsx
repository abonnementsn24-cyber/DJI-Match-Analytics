"use client";

import { Bar, BarChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { CalibrationPoint } from "@/lib/types";

export function CalibrationChart({ data }: { data: CalibrationPoint[] }) {
  if (data.length === 0) {
    return <div className="flex h-56 items-center justify-center text-sm text-text-secondary">Pas assez de matchs évalués.</div>;
  }

  const chartData = data.map((d) => ({
    range: d.predicted_range,
    "Probabilité annoncée": Number((d.mean_predicted * 100).toFixed(1)),
    "Fréquence observée": Number((d.actual_frequency * 100).toFixed(1)),
  }));

  return (
    <ResponsiveContainer width="100%" height={240}>
      <BarChart data={chartData} margin={{ top: 8, right: 16, left: -16, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#223D60" />
        <XAxis dataKey="range" stroke="#91A6C0" fontSize={11} />
        <YAxis unit="%" stroke="#91A6C0" fontSize={12} />
        <Tooltip contentStyle={{ background: "#10243D", border: "1px solid #223D60", borderRadius: 8, fontSize: 12 }} />
        <Legend wrapperStyle={{ fontSize: 12 }} />
        <Bar dataKey="Probabilité annoncée" fill="#3EC6F0" radius={[4, 4, 0, 0]} />
        <Bar dataKey="Fréquence observée" fill="#34C77B" radius={[4, 4, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  );
}
