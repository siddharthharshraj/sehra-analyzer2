"use client";

import { BarChart3 } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { useInView } from "./use-in-view";

const metrics = [
  { value: "~90%", label: "Effort reduction for Liberia analysis", accent: true },
  { value: "6", label: "Countries supported (Liberia, India, Laos, Uganda, Kenya + extensible)" },
  { value: "198", label: "Comprehensive tests, all passing" },
  { value: "4", label: "Export formats — DOCX, XLSX, HTML, PDF" },
  { value: "11", label: "Cross-cutting health system themes" },
  { value: "3", label: "LLM providers with automatic fallback" },
];

export function ImpactSection() {
  const { ref, isVisible } = useInView();

  return (
    <section ref={ref} className="py-24 px-4 bg-white">
      <div
        className={`mx-auto max-w-5xl transition-all duration-700 ${isVisible ? "opacity-100 translate-y-0" : "opacity-0 translate-y-8"}`}
      >
        {/* Heading */}
        <div className="flex flex-col items-center text-center mb-14">
          <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-[#0D7377]/10 mb-4">
            <BarChart3 className="h-6 w-6 text-[#0D7377]" />
          </div>
          <h2 className="text-3xl font-bold tracking-tight sm:text-4xl">
            Impact
          </h2>
        </div>

        {/* Metric cards */}
        <div className="grid grid-cols-2 lg:grid-cols-3 gap-5">
          {metrics.map((m, i) => (
            <Card
              key={i}
              className={`card-hover shadow-card border-0 ${m.accent ? "bg-gradient-to-br from-[#0D7377] to-[#095456] text-white" : "bg-gradient-to-br from-white to-[#0D7377]/[0.03]"}`}
              style={{
                opacity: isVisible ? 1 : 0,
                transform: isVisible ? "translateY(0) scale(1)" : "translateY(16px) scale(0.97)",
                transitionProperty: "opacity, transform",
                transitionDuration: "0.5s",
                transitionTimingFunction: "ease-out",
                transitionDelay: isVisible ? `${i * 80}ms` : "0ms",
              }}
            >
              <CardContent className="flex flex-col items-center p-6 text-center">
                <span
                  className={`text-4xl font-bold sm:text-5xl ${m.accent ? "text-white" : "text-[#0D7377]"}`}
                >
                  {m.value}
                </span>
                <span
                  className={`mt-3 text-xs leading-relaxed ${m.accent ? "text-white/80" : "text-muted-foreground"}`}
                >
                  {m.label}
                </span>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    </section>
  );
}
