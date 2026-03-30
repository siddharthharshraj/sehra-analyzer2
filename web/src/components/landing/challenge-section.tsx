"use client";

import { Clock } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { useInView } from "./use-in-view";

const stats = [
  { value: "2 months", label: "Time to manually analyze one SEHRA report" },
  { value: "309 items", label: "Questions per assessment requiring classification" },
  { value: "6 SEHRAs/yr", label: "Target assessments across multiple countries" },
  { value: "11 themes", label: "Cross-cutting themes requiring expert categorization" },
];

export function ChallengeSection() {
  const { ref, isVisible } = useInView();

  return (
    <section
      id="section-challenge"
      ref={ref}
      className="py-24 px-4 bg-white"
    >
      <div
        className={`mx-auto max-w-5xl transition-all duration-700 ${isVisible ? "opacity-100 translate-y-0" : "opacity-0 translate-y-8"}`}
      >
        {/* Section heading */}
        <div className="flex flex-col items-center text-center mb-14">
          <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-[#0D7377]/10 mb-4">
            <Clock className="h-6 w-6 text-[#0D7377]" />
          </div>
          <h2 className="text-3xl font-bold tracking-tight sm:text-4xl">
            The Challenge
          </h2>
        </div>

        {/* Stat cards */}
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-4 mb-12">
          {stats.map((s, i) => (
            <Card
              key={i}
              className="card-hover shadow-card border-0 bg-gradient-to-b from-white to-[#0D7377]/[0.03]"
              style={{
                opacity: isVisible ? 1 : 0,
                transform: isVisible ? "translateY(0)" : "translateY(16px)",
                transitionProperty: "opacity, transform",
                transitionDuration: "0.5s",
                transitionTimingFunction: "ease-out",
                transitionDelay: isVisible ? `${i * 80}ms` : "0ms",
              }}
            >
              <CardContent className="flex flex-col items-center p-5 text-center">
                <span className="text-2xl font-bold text-[#0D7377] sm:text-3xl">
                  {s.value}
                </span>
                <span className="mt-2 text-xs text-muted-foreground leading-snug">
                  {s.label}
                </span>
              </CardContent>
            </Card>
          ))}
        </div>

        {/* Description */}
        <p className="mx-auto max-w-3xl text-center text-muted-foreground leading-relaxed">
          PRASHO Foundation conducts School Eye Health Rapid Assessments across
          countries like Liberia, India, Laos, Uganda, and Kenya. Each assessment
          contains 309 items across 6 components, with qualitative remarks that
          must be manually classified into enablers and barriers across 11
          cross-cutting themes. This manual process takes approximately{" "}
          <strong className="text-foreground">2 months per analyst</strong> —
          making it impossible to scale.
        </p>
      </div>
    </section>
  );
}
