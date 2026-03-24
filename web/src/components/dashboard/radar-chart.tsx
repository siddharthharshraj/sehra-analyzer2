"use client";

import {
  RadarChart as ReRadar,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
  ResponsiveContainer,
  Tooltip as RechartsTooltip,
} from "recharts";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { HelpCircle } from "lucide-react";
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
    <Card className="shadow-card rounded-xl border-gray-100">
      <CardHeader>
        <CardTitle className="text-sm font-medium inline-flex items-center gap-1.5">
          Enabler % by Component
          <Tooltip>
            <TooltipTrigger asChild>
              <HelpCircle className="h-4 w-4 text-muted-foreground cursor-help inline-block" />
            </TooltipTrigger>
            <TooltipContent side="bottom" className="max-w-[280px] text-sm">
              <p>Shows the percentage of enablers for each SEHRA component. A fuller shape indicates better overall readiness.</p>
            </TooltipContent>
          </Tooltip>
        </CardTitle>
        <p className="text-xs text-muted-foreground mt-1">
          Shows readiness level per area — larger shape means stronger
          performance
        </p>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={300}>
          <ReRadar cx="50%" cy="50%" outerRadius="80%" data={data}>
            <PolarGrid stroke="#e5e7eb" />
            <PolarAngleAxis
              dataKey="component"
              tick={{ fontSize: 11, fill: "#6b7280" }}
            />
            <PolarRadiusAxis
              angle={30}
              domain={[0, 100]}
              tick={{ fontSize: 10, fill: "#9ca3af" }}
            />
            <Radar
              dataKey="value"
              stroke={TEAL}
              fill={TEAL}
              fillOpacity={0.2}
              strokeWidth={2}
            />
            <RechartsTooltip
              contentStyle={{
                borderRadius: 8,
                border: "1px solid #e5e7eb",
                boxShadow: "0 4px 6px -1px rgb(0 0 0 / 0.06)",
                fontSize: 12,
              }}
            />
          </ReRadar>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}
