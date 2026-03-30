"use client";

import {
  Upload,
  ScanSearch,
  BookOpen,
  Calculator,
  Brain,
  ShieldCheck,
  FileText,
  LayoutDashboard,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { useInView } from "./use-in-view";

const steps = [
  {
    icon: Upload,
    title: "1. User uploads a SEHRA PDF",
    body: "A field team fills out a 44-page form-fillable PDF with checkboxes (Yes/No) and text remarks for each question about school eye health in their country. The user uploads this PDF to the platform.",
  },
  {
    icon: ScanSearch,
    title: "2. The system reads the PDF like a human would — but instantly",
    body: "It doesn't just read text. It finds every checkbox widget on every page, detects which ones are checked (Yes/No), finds the question text next to each checkbox using spatial coordinates, and extracts free-text remarks from text fields. It also reads the country, district, and date from the first page.",
  },
  {
    icon: BookOpen,
    title: "3. Each question is matched to a master codebook",
    body: 'The system has a codebook of ~309 standardized SEHRA questions. It fuzzy-matches each extracted question to the codebook to get the official item ID (e.g., "S15" = Policy question 15). This tells the system which component (Policy, HR, Supply Chain, etc.) and which scoring rule applies.',
  },
  {
    icon: Calculator,
    title: "4. Quantitative scoring — no AI needed",
    body: 'Each Yes/No answer is scored using deterministic rules: Yes = enabler (score 1), No = barrier (score 0). Some questions are reverse-scored (e.g., "Are there challenges?" where Yes = barrier). The system counts enablers and barriers per component and calculates a readiness percentage.',
  },
  {
    icon: Brain,
    title: "5. AI classifies qualitative remarks into 11 themes",
    body: 'This is the step that used to take 2 months manually. Every text remark is sent to an LLM (GPT-4o / Llama / Claude) with rich domain context. The AI classifies each remark into one of 11 health system themes (like Funding, Coordination, Local Capacity) and labels it as an enabler or barrier, with a confidence score.',
  },
  {
    icon: ShieldCheck,
    title: "6. The AI's output is validated and calibrated",
    body: "The system doesn't blindly trust the AI. It checks that every theme name is valid (fuzzy-matching typos), caps confidence when the AI is uncertain, reduces confidence for very short remarks, and sanitizes all input to prevent prompt injection.",
  },
  {
    icon: FileText,
    title: "7. AI generates summaries and recommendations",
    body: "After all 6 components are analyzed, the AI synthesizes everything into an executive summary (2-5 paragraphs covering the whole assessment) and 5-8 prioritized recommendations (actionable next steps based on the barriers found). These are written for program managers and stakeholders.",
  },
  {
    icon: LayoutDashboard,
    title: "8. Everything is saved and ready for review, editing, and export",
    body: "All results are stored in PostgreSQL. The user gets an interactive dashboard with charts (radar, bar, heatmap), can inline-edit any AI classification they disagree with, batch-approve high-confidence entries, chat with an AI copilot about the data, and export professional reports in DOCX, XLSX, HTML, or PDF.",
  },
];

const components = [
  "Context",
  "Policy",
  "Service Delivery",
  "Human Resources",
  "Supply Chain",
  "Barriers",
];

const themes = [
  "Institutional Structure & Stakeholders",
  "Operationalization Strategies",
  "Coordination & Integration",
  "Funding",
  "Local Capacity & Service Delivery",
  "Accessibility & Inclusivity",
  "Cost, Availability & Affordability",
  "Data Considerations",
  "Sociocultural Factors & Compliance",
  "Services at Higher Levels",
  "Procuring Eyeglasses",
];

export function PipelineSection() {
  const { ref, isVisible } = useInView();

  return (
    <section
      ref={ref}
      className="py-24 px-4"
      style={{
        background: "linear-gradient(180deg, #f8fffe 0%, #f0faf9 100%)",
      }}
    >
      <div
        className={`mx-auto max-w-4xl transition-all duration-700 ${isVisible ? "opacity-100 translate-y-0" : "opacity-0 translate-y-8"}`}
      >
        {/* Heading */}
        <div className="flex flex-col items-center text-center mb-16">
          <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-[#0D7377]/10 mb-4">
            <Brain className="h-6 w-6 text-[#0D7377]" />
          </div>
          <h2 className="text-3xl font-bold tracking-tight sm:text-4xl">
            How It Works
          </h2>
          <p className="mt-3 text-muted-foreground max-w-2xl">
            From PDF upload to actionable report — 8 steps, fully automated
          </p>
        </div>

        {/* 8 Steps */}
        <div className="space-y-6">
          {steps.map((step, i) => {
            const Icon = step.icon;
            return (
              <div
                key={i}
                className="flex gap-4 sm:gap-5"
                style={{
                  opacity: isVisible ? 1 : 0,
                  transform: isVisible ? "translateY(0)" : "translateY(16px)",
                  transitionProperty: "opacity, transform",
                  transitionDuration: "0.5s",
                  transitionTimingFunction: "ease-out",
                  transitionDelay: isVisible ? `${i * 80}ms` : "0ms",
                }}
              >
                {/* Icon + connector line */}
                <div className="flex flex-col items-center">
                  <div
                    className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-xl shadow-sm ${
                      i === 4
                        ? "bg-[#0D7377] text-white"
                        : "bg-white border border-[#0D7377]/15 text-[#0D7377]"
                    }`}
                  >
                    <Icon className="h-5 w-5" />
                  </div>
                  {i < steps.length - 1 && (
                    <div className="w-px flex-1 min-h-4 bg-[#0D7377]/15 mt-2" />
                  )}
                </div>

                {/* Content */}
                <div className="pb-6 flex-1 min-w-0">
                  <h3 className="text-sm sm:text-base font-semibold leading-tight mb-1.5">
                    {step.title}
                  </h3>
                  <p className="text-sm text-muted-foreground leading-relaxed">
                    {step.body}
                  </p>
                </div>
              </div>
            );
          })}
        </div>

        {/* Components + Themes */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-10 mt-16">
          {/* 6 Components */}
          <div>
            <h3 className="text-sm font-semibold text-center mb-4 text-muted-foreground uppercase tracking-wider">
              6 SEHRA Components
            </h3>
            <div className="flex flex-wrap justify-center gap-2">
              {components.map((c) => (
                <Badge
                  key={c}
                  variant="outline"
                  className="px-3 py-1.5 text-xs border-[#0D7377]/20 text-[#095456] bg-white"
                >
                  {c}
                </Badge>
              ))}
            </div>
          </div>

          {/* 11 Themes */}
          <div>
            <h3 className="text-sm font-semibold text-center mb-4 text-muted-foreground uppercase tracking-wider">
              11 Cross-Cutting Themes
            </h3>
            <div className="flex flex-wrap justify-center gap-2">
              {themes.map((t) => (
                <Badge
                  key={t}
                  variant="secondary"
                  className="px-3 py-1.5 text-xs"
                >
                  {t}
                </Badge>
              ))}
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
