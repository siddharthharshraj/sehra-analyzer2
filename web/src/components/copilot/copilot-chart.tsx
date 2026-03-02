"use client";

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  Radar,
} from "recharts";
import { TEAL, RED } from "@/lib/constants";
import type { ChartSpec } from "@/lib/types";

const CHART_COLORS = [TEAL, "#10857A", "#14967E", "#18A781", "#1CB885", RED];

export function CopilotChart({ spec }: { spec: ChartSpec }) {
  if (spec.type === "bar") {
    return (
      <ResponsiveContainer width="100%" height={180}>
        <BarChart data={spec.data}>
          <XAxis dataKey="label" tick={{ fontSize: 10 }} />
          <YAxis />
          <Tooltip />
          <Bar dataKey="value" fill={TEAL} radius={[4, 4, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    );
  }

  if (spec.type === "pie") {
    return (
      <ResponsiveContainer width="100%" height={180}>
        <PieChart>
          <Pie
            data={spec.data}
            dataKey="value"
            nameKey="label"
            cx="50%"
            cy="50%"
            outerRadius={70}
            label={({ name }) => name as string}
          >
            {spec.data.map((_, i) => (
              <Cell key={i} fill={CHART_COLORS[i % CHART_COLORS.length]} />
            ))}
          </Pie>
          <Tooltip />
        </PieChart>
      </ResponsiveContainer>
    );
  }

  if (spec.type === "radar") {
    return (
      <ResponsiveContainer width="100%" height={180}>
        <RadarChart data={spec.data}>
          <PolarGrid />
          <PolarAngleAxis dataKey="label" tick={{ fontSize: 10 }} />
          <Radar dataKey="value" stroke={TEAL} fill={TEAL} fillOpacity={0.3} />
          <Tooltip />
        </RadarChart>
      </ResponsiveContainer>
    );
  }

  return null;
}
