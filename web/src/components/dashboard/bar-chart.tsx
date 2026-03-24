"use client";

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip as RechartsTooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { HelpCircle } from "lucide-react";
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
    <Card className="shadow-card rounded-xl border-gray-100">
      <CardHeader>
        <CardTitle className="text-sm font-medium inline-flex items-center gap-1.5">
          Enablers vs Barriers
          <Tooltip>
            <TooltipTrigger asChild>
              <HelpCircle className="h-4 w-4 text-muted-foreground cursor-help inline-block" />
            </TooltipTrigger>
            <TooltipContent side="bottom" className="max-w-[280px] text-sm">
              <p>Compares enabler and barrier counts across all components. Teal bars show enablers, red bars show barriers.</p>
            </TooltipContent>
          </Tooltip>
        </CardTitle>
        <p className="text-xs text-muted-foreground mt-1">
          Compares positive factors (enablers) vs challenges (barriers) for
          each component
        </p>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={data}>
            <CartesianGrid
              strokeDasharray="3 3"
              stroke="#f0f0f0"
              vertical={false}
            />
            <XAxis
              dataKey="name"
              tick={{ fontSize: 11, fill: "#6b7280" }}
              angle={-20}
              textAnchor="end"
              height={60}
              axisLine={{ stroke: "#e5e7eb" }}
              tickLine={false}
            />
            <YAxis
              tick={{ fontSize: 11, fill: "#6b7280" }}
              axisLine={false}
              tickLine={false}
            />
            <RechartsTooltip
              contentStyle={{
                borderRadius: 8,
                border: "1px solid #e5e7eb",
                boxShadow: "0 4px 6px -1px rgb(0 0 0 / 0.06)",
                fontSize: 12,
              }}
            />
            <Legend
              wrapperStyle={{ fontSize: 12, paddingTop: 8 }}
            />
            <Bar
              dataKey="Enablers"
              fill={TEAL}
              radius={[4, 4, 0, 0]}
            />
            <Bar
              dataKey="Barriers"
              fill={RED}
              radius={[4, 4, 0, 0]}
            />
          </BarChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}
