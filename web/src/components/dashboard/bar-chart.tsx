"use client";

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { COMPONENT_LABELS, TEAL, RED } from "@/lib/constants";
import type { ComponentAnalysis } from "@/lib/types";
import type { ComponentName } from "@/lib/constants";

interface BarChartProps {
  components: ComponentAnalysis[];
}

export function EnablerBarrierChart({ components }: BarChartProps) {
  const data = components.map((c) => ({
    name:
      COMPONENT_LABELS[c.component as ComponentName] || c.component,
    Enablers: c.enabler_count,
    Barriers: c.barrier_count,
  }));

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-sm font-medium">
          Enablers vs Barriers
        </CardTitle>
        <p className="text-xs text-muted-foreground mt-1">
          Compares positive factors (enablers) vs challenges (barriers) for each component
        </p>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={data}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis
              dataKey="name"
              tick={{ fontSize: 11 }}
              angle={-20}
              textAnchor="end"
              height={60}
            />
            <YAxis />
            <Tooltip />
            <Legend />
            <Bar dataKey="Enablers" fill={TEAL} radius={[4, 4, 0, 0]} />
            <Bar dataKey="Barriers" fill={RED} radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}
