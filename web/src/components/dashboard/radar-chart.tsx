"use client";

import {
  RadarChart as ReRadar,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
  ResponsiveContainer,
  Tooltip,
} from "recharts";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { COMPONENT_LABELS, TEAL } from "@/lib/constants";
import type { ComponentAnalysis } from "@/lib/types";
import type { ComponentName } from "@/lib/constants";

interface RadarChartProps {
  components: ComponentAnalysis[];
}

export function EnablerRadarChart({ components }: RadarChartProps) {
  const data = components.map((c) => {
    const total = c.enabler_count + c.barrier_count;
    const pct = total > 0 ? Math.round((c.enabler_count / total) * 100) : 0;
    return {
      component:
        COMPONENT_LABELS[c.component as ComponentName] || c.component,
      value: pct,
    };
  });

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-sm font-medium">
          Enabler % by Component
        </CardTitle>
        <p className="text-xs text-muted-foreground mt-1">
          Shows readiness level per area — larger shape means stronger performance
        </p>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={300}>
          <ReRadar cx="50%" cy="50%" outerRadius="80%" data={data}>
            <PolarGrid />
            <PolarAngleAxis
              dataKey="component"
              tick={{ fontSize: 11 }}
            />
            <PolarRadiusAxis angle={30} domain={[0, 100]} />
            <Radar
              dataKey="value"
              stroke={TEAL}
              fill={TEAL}
              fillOpacity={0.3}
            />
            <Tooltip />
          </ReRadar>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}
