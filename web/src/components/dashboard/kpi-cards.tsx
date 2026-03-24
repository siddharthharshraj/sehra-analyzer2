"use client";

import { useEffect, useRef, useState } from "react";
import { Card, CardContent } from "@/components/ui/card";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { TrendingUp, TrendingDown, Percent, Layers, Info } from "lucide-react";
import { TEAL, RED } from "@/lib/constants";
import type { ComponentAnalysis } from "@/lib/types";

interface KPICardsProps {
  components: ComponentAnalysis[];
}

/* ── Animated counter hook ── */
function useCountUp(target: number, duration = 600): number {
  const [value, setValue] = useState(0);
  const rafRef = useRef<number>(0);

  useEffect(() => {
    if (target === 0) {
      setValue(0);
      return;
    }

    const start = performance.now();
    const animate = (now: number) => {
      const elapsed = now - start;
      const progress = Math.min(elapsed / duration, 1);
      // ease-out cubic
      const eased = 1 - Math.pow(1 - progress, 3);
      setValue(Math.round(eased * target));
      if (progress < 1) {
        rafRef.current = requestAnimationFrame(animate);
      }
    };
    rafRef.current = requestAnimationFrame(animate);
    return () => cancelAnimationFrame(rafRef.current);
  }, [target, duration]);

  return value;
}

function AnimatedValue({ target, suffix = "" }: { target: number; suffix?: string }) {
  const value = useCountUp(target);
  return (
    <span className="count-up-enter">
      {value}{suffix}
    </span>
  );
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
  const enablerPct =
    total > 0 ? Math.round((totalEnablers / total) * 100) : 0;
  const componentCount = components.length;

  const cards = [
    {
      label: "Total Enablers",
      numericValue: totalEnablers,
      suffix: "",
      color: TEAL,
      icon: TrendingUp,
      hint: "Positive factors supporting eye health services",
      tooltip: "Factors that support school eye health programmes. Higher is better. Based on codebook scoring of yes/no responses.",
    },
    {
      label: "Total Barriers",
      numericValue: totalBarriers,
      suffix: "",
      color: RED,
      icon: TrendingDown,
      hint: "Challenges hindering eye health services",
      tooltip: "Factors that hinder school eye health. These need action. Identified from both quantitative scores and AI analysis.",
    },
    {
      label: "Enabler Rate",
      numericValue: enablerPct,
      suffix: "%",
      color: TEAL,
      icon: Percent,
      hint: "Percentage of positive findings",
      tooltip: "Percentage of scored items classified as enablers. Above 60% indicates moderate readiness.",
    },
    {
      label: "Components Analyzed",
      numericValue: componentCount,
      suffix: "",
      color: "#6B7280",
      icon: Layers,
      hint: "Key areas assessed",
      tooltip: "Number of SEHRA sections analyzed (Context, Policy, Service Delivery, HR, Supply Chain, Barriers).",
    },
  ];

  return (
    <TooltipProvider delayDuration={200}>
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4 stagger-enter">
        {cards.map((card) => {
          const Icon = card.icon;
          return (
            <Card key={card.label} className="shadow-card rounded-xl border-gray-100">
              <CardContent className="pt-5 pb-4">
                <div className="flex items-start gap-4">
                  <div
                    className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl"
                    style={{ backgroundColor: `${card.color}10` }}
                  >
                    <Icon
                      className="h-5 w-5"
                      style={{ color: card.color }}
                    />
                  </div>
                  <div className="min-w-0 flex-1">
                    <p className="text-2xl font-bold tracking-tight tabular-nums">
                      <AnimatedValue target={card.numericValue} suffix={card.suffix} />
                    </p>
                    <div className="flex items-center gap-1">
                      <p className="text-sm text-muted-foreground truncate">
                        {card.label}
                      </p>
                      <Tooltip>
                        <TooltipTrigger asChild>
                          <Info className="h-3 w-3 text-muted-foreground/50 cursor-help shrink-0" />
                        </TooltipTrigger>
                        <TooltipContent
                          side="bottom"
                          className="max-w-[220px] text-xs"
                        >
                          {card.tooltip}
                        </TooltipContent>
                      </Tooltip>
                    </div>
                    <p className="text-[11px] text-muted-foreground/60 mt-0.5 truncate">
                      {card.hint}
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>
    </TooltipProvider>
  );
}
