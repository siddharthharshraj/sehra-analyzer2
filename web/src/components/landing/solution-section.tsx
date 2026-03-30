"use client";

import {
  Zap,
  FileSearch,
  Brain,
  Calculator,
  LayoutDashboard,
  MessageCircle,
  Globe,
} from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { useInView } from "./use-in-view";

const features = [
  {
    icon: FileSearch,
    title: "PDF Parsing",
    desc: "Extracts checkbox responses and remarks from SEHRA PDFs automatically using widget-first extraction",
  },
  {
    icon: Brain,
    title: "AI Classification",
    desc: "Classifies qualitative remarks into 11 themes as enablers or barriers using multi-LLM fallback (Groq, Claude, GPT-4o)",
  },
  {
    icon: Calculator,
    title: "Quantitative Scoring",
    desc: "Deterministic codebook-based scoring with standard and reverse item support",
  },
  {
    icon: LayoutDashboard,
    title: "Interactive Dashboard",
    desc: "KPI cards, radar charts, heatmaps, and inline editing for review",
  },
  {
    icon: MessageCircle,
    title: "AI Copilot",
    desc: "Multi-turn chat assistant with tool calling for data queries and edits",
  },
  {
    icon: Globe,
    title: "Multi-Country",
    desc: "Country-specific codebooks, page ranges, keyword patterns, and knowledge bases",
  },
];

export function SolutionSection() {
  const { ref, isVisible } = useInView();

  return (
    <section ref={ref} className="py-24 px-4 bg-white">
      <div
        className={`mx-auto max-w-5xl transition-all duration-700 ${isVisible ? "opacity-100 translate-y-0" : "opacity-0 translate-y-8"}`}
      >
        {/* Heading */}
        <div className="flex flex-col items-center text-center mb-14">
          <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-[#0D7377]/10 mb-4">
            <Zap className="h-6 w-6 text-[#0D7377]" />
          </div>
          <h2 className="text-3xl font-bold tracking-tight sm:text-4xl">
            What SEHRA Analyzer Does
          </h2>
        </div>

        {/* Feature grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
          {features.map((f, i) => {
            const Icon = f.icon;
            return (
              <Card
                key={i}
                className="card-hover shadow-card border-0 bg-gradient-to-br from-white to-[#0D7377]/[0.02]"
                style={{
                  opacity: isVisible ? 1 : 0,
                  transform: isVisible ? "translateY(0)" : "translateY(16px)",
                  transitionProperty: "opacity, transform",
                  transitionDuration: "0.5s",
                  transitionTimingFunction: "ease-out",
                  transitionDelay: isVisible ? `${i * 70}ms` : "0ms",
                }}
              >
                <CardContent className="p-6">
                  <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-[#0D7377]/10 mb-4">
                    <Icon className="h-5 w-5 text-[#0D7377]" />
                  </div>
                  <h3 className="text-sm font-semibold mb-2">{f.title}</h3>
                  <p className="text-xs text-muted-foreground leading-relaxed">
                    {f.desc}
                  </p>
                </CardContent>
              </Card>
            );
          })}
        </div>
      </div>
    </section>
  );
}
