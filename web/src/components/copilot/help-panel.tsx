"use client";

import { useState } from "react";
import {
  ChevronDown,
  ChevronRight,
  Upload,
  BarChart3,
  Shield,
  FileText,
  BookOpen,
  Bot,
} from "lucide-react";
import { Separator } from "@/components/ui/separator";

const HELP_TOPICS = [
  {
    icon: Upload,
    question: "How do I upload a SEHRA assessment?",
    answer:
      "Go to Upload PDF in the sidebar. Drag & drop your SEHRA assessment PDF or click to browse. The system will automatically extract, score, and classify all data using AI. You can track real-time progress as each component is analyzed.",
  },
  {
    icon: BarChart3,
    question: "How do I read the dashboard?",
    answer:
      "The Dashboard shows KPI cards (total enablers, barriers, readiness score), a radar chart comparing components, and a bar chart for enabler/barrier breakdown. Select an assessment from the dropdown at the top. Click any component tab to see individual qualitative entries and report sections.",
  },
  {
    icon: Shield,
    question: "How does the review workflow work?",
    answer:
      "Each AI-classified entry has a confidence score. You can edit classifications inline (click theme/classification badges), batch approve high-confidence entries (>80%), then mark the assessment as Reviewed and finally Published. The status flow is: Draft -> Reviewed -> Published.",
  },
  {
    icon: FileText,
    question: "What export formats are available?",
    answer:
      "Go to Export & Share. You can download reports as DOCX (Word), XLSX (Excel), HTML, or PDF. You can also create shareable links with passcode protection and optional expiry dates.",
  },
  {
    icon: BookOpen,
    question: "What is the codebook?",
    answer:
      "The codebook defines all SEHRA questions, organized by component (Context, Policy, Service Delivery, Human Resources, Supply Chain, Barriers). Admins can manage questions via Manage Questions. Each item has scoring rules (yes/no, reverse scoring) used for automated analysis.",
  },
  {
    icon: Bot,
    question: "What can the Copilot do?",
    answer:
      "The Copilot can list assessments, summarize findings, compare enablers vs barriers with charts, search entries by theme or confidence, compare two assessments side by side, and suggest next actions like batch approving entries or changing status. Just ask in natural language!",
  },
];

interface HelpPanelProps {
  onSwitchToChat: () => void;
}

export function HelpPanel({ onSwitchToChat }: HelpPanelProps) {
  const [expandedIndex, setExpandedIndex] = useState<number | null>(null);

  return (
    <div className="px-4 py-3">
      <div className="mb-3">
        <h3 className="text-sm font-medium mb-1">Platform Help</h3>
        <p className="text-xs text-muted-foreground">
          Tap a topic to learn more, or ask the Copilot any question.
        </p>
      </div>
      <div className="space-y-1.5">
        {HELP_TOPICS.map((topic, i) => (
          <div key={i} className="rounded-lg border overflow-hidden">
            <button
              onClick={() => setExpandedIndex(expandedIndex === i ? null : i)}
              className="w-full flex items-center gap-2.5 px-3 py-2.5 text-left hover:bg-muted/50 transition-colors"
            >
              <topic.icon className="h-4 w-4 text-[#0D7377] shrink-0" />
              <span className="text-sm font-medium flex-1">{topic.question}</span>
              {expandedIndex === i ? (
                <ChevronDown className="h-3.5 w-3.5 text-muted-foreground shrink-0" />
              ) : (
                <ChevronRight className="h-3.5 w-3.5 text-muted-foreground shrink-0" />
              )}
            </button>
            {expandedIndex === i && (
              <div className="px-3 pb-3 pt-0">
                <p className="text-xs text-muted-foreground leading-relaxed">
                  {topic.answer}
                </p>
              </div>
            )}
          </div>
        ))}
      </div>
      <Separator className="my-3" />
      <p className="text-xs text-muted-foreground text-center">
        Have a different question? Switch to{" "}
        <button
          onClick={onSwitchToChat}
          className="text-[#0D7377] font-medium hover:underline"
        >
          Chat
        </button>{" "}
        and ask the Copilot.
      </p>
    </div>
  );
}
