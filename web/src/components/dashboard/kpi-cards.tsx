"use client";

import { Card, CardContent } from "@/components/ui/card";
import { TEAL, RED } from "@/lib/constants";
import type { ComponentAnalysis } from "@/lib/types";

interface KPICardsProps {
  components: ComponentAnalysis[];
}

export function KPICards({ components }: KPICardsProps) {
  const totalEnablers = components.reduce(
    (sum, c) => sum + c.enabler_count,
    0,
  );
  const totalBarriers = components.reduce(
    (sum, c) => sum + c.barrier_count,
    0,
  );
  const total = totalEnablers + totalBarriers;
  const enablerPct = total > 0 ? Math.round((totalEnablers / total) * 100) : 0;
  const componentCount = components.length;

  const cards = [
    {
      label: "Total Enablers",
      value: totalEnablers,
      color: TEAL,
      hint: "Positive factors supporting eye health services",
    },
    {
      label: "Total Barriers",
      value: totalBarriers,
      color: RED,
      hint: "Challenges hindering eye health services",
    },
    {
      label: "Enabler Rate",
      value: `${enablerPct}%`,
      color: TEAL,
      hint: "Percentage of positive findings — higher is better",
    },
    {
      label: "Components Analyzed",
      value: componentCount,
      color: "#6B7280",
      hint: "Key areas assessed (e.g. Policy, HR, Supply Chain)",
    },
  ];

  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
      {cards.map((card) => (
        <Card key={card.label}>
          <CardContent className="pt-6">
            <div className="flex items-center gap-4">
              <div
                className="h-12 w-1 rounded-full"
                style={{ backgroundColor: card.color }}
              />
              <div>
                <p className="text-2xl font-bold">{card.value}</p>
                <p className="text-sm text-muted-foreground">{card.label}</p>
                <p className="text-[11px] text-muted-foreground/70 mt-0.5">{card.hint}</p>
              </div>
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
