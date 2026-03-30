"use client";

import {
  Sparkles,
  Upload,
  Brain,
  UserCheck,
  FileOutput,
  ArrowRight,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { useInView } from "./use-in-view";

const steps = [
  {
    icon: Upload,
    title: "Upload PDF",
    desc: "Form-fillable SEHRA PDFs parsed automatically",
  },
  {
    icon: Brain,
    title: "AI Analysis",
    desc: "Multi-LLM engine classifies remarks into themes",
  },
  {
    icon: UserCheck,
    title: "Human Review",
    desc: "Analysts review and approve AI classifications",
  },
  {
    icon: FileOutput,
    title: "Export Reports",
    desc: "Professional DOCX, XLSX, HTML, PDF reports",
  },
];

const principles = [
  "AI + Human-in-the-Loop",
  "Multi-Country Support",
  "Domain-Specific Intelligence",
];

export function ApproachSection() {
  const { ref, isVisible } = useInView();

  return (
    <section
      ref={ref}
      className="py-24 px-4"
      style={{ background: "linear-gradient(180deg, #f8fffe 0%, #f0faf9 100%)" }}
    >
      <div
        className={`mx-auto max-w-5xl transition-all duration-700 ${isVisible ? "opacity-100 translate-y-0" : "opacity-0 translate-y-8"}`}
      >
        {/* Heading */}
        <div className="flex flex-col items-center text-center mb-14">
          <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-[#0D7377]/10 mb-4">
            <Sparkles className="h-6 w-6 text-[#0D7377]" />
          </div>
          <h2 className="text-3xl font-bold tracking-tight sm:text-4xl">
            Our Approach
          </h2>
        </div>

        {/* Pipeline */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 mb-12">
          {steps.map((step, i) => {
            const Icon = step.icon;
            return (
              <div
                key={i}
                className="relative flex flex-col items-center text-center"
                style={{
                  opacity: isVisible ? 1 : 0,
                  transform: isVisible ? "translateY(0)" : "translateY(16px)",
                  transitionProperty: "opacity, transform",
                  transitionDuration: "0.5s",
                  transitionTimingFunction: "ease-out",
                  transitionDelay: isVisible ? `${i * 100}ms` : "0ms",
                }}
              >
                {/* Connector arrow (desktop only) */}
                {i < steps.length - 1 && (
                  <div className="absolute right-0 top-8 hidden lg:flex translate-x-1/2 z-10 text-[#0D7377]/30">
                    <ArrowRight className="h-5 w-5" />
                  </div>
                )}

                <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-white shadow-card border border-[#0D7377]/10 mb-4">
                  <Icon className="h-7 w-7 text-[#0D7377]" />
                </div>
                <div className="flex h-6 w-6 items-center justify-center rounded-full bg-[#0D7377] text-white text-xs font-bold mb-3">
                  {i + 1}
                </div>
                <h3 className="text-sm font-semibold mb-1">{step.title}</h3>
                <p className="text-xs text-muted-foreground leading-relaxed max-w-[200px]">
                  {step.desc}
                </p>
              </div>
            );
          })}
        </div>

        {/* Principles */}
        <div className="flex flex-wrap justify-center gap-3">
          {principles.map((p) => (
            <Badge
              key={p}
              variant="outline"
              className="px-4 py-1.5 text-sm font-medium border-[#0D7377]/20 text-[#0D7377] bg-white"
            >
              {p}
            </Badge>
          ))}
        </div>
      </div>
    </section>
  );
}
