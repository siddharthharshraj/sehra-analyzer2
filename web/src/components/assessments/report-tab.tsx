"use client";

import { useCallback } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import {
  FileText,
  FileDown,
  CheckCircle2,
  XCircle,
  BarChart3,
  HelpCircle,
} from "lucide-react";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { apiDownload, apiPatch } from "@/lib/api-client";
import { toast } from "sonner";
import { useComponents } from "@/hooks/use-sehras";
import { useCopilotContext } from "@/components/copilot/copilot-context";
import { EditableSection } from "./editable-section";
import type { SEHRADetail } from "@/lib/types";

interface ReportTabProps {
  sehra: SEHRADetail;
  onRefresh?: () => void;
}

const COMPONENT_NAMES: Record<string, string> = {
  context: "Context",
  policy: "Policy & Strategy",
  service_delivery: "Service Delivery",
  human_resources: "Human Resources",
  supply_chain: "Supply Chain",
  barriers: "Barriers",
};

export function ReportTab({ sehra, onRefresh }: ReportTabProps) {
  const { components } = useComponents(sehra.id);
  const { open: openCopilot, sendMessage } = useCopilotContext();

  async function handleDownload(format: "docx" | "pdf") {
    try {
      const ext = format;
      const filename = `SEHRA_${sehra.country}_${sehra.id.slice(0, 8)}.${ext}`;
      await apiDownload(`/export/${sehra.id}/${format}`, filename);
      toast.success(`${ext.toUpperCase()} downloaded`);
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Download failed");
    }
  }

  const handleSaveExecutiveSummary = useCallback(
    async (newText: string) => {
      await apiPatch(`/sehras/${sehra.id}`, { executive_summary: newText });
      onRefresh?.();
    },
    [sehra.id, onRefresh],
  );

  const handleSaveRecommendations = useCallback(
    async (newText: string) => {
      await apiPatch(`/sehras/${sehra.id}`, { recommendations: newText });
      onRefresh?.();
    },
    [sehra.id, onRefresh],
  );

  const handleSaveSection = useCallback(
    async (sectionId: string, newContent: string) => {
      await apiPatch(`/sections/${sectionId}`, { content: newContent });
      onRefresh?.();
    },
    [onRefresh],
  );

  function handleAskCopilot(prompt: string) {
    openCopilot();
    setTimeout(() => sendMessage(prompt), 150);
  }

  const hasSummary = sehra.executive_summary || sehra.recommendations;
  const totalEnablers = components.reduce((s, c) => s + c.enabler_count, 0);
  const totalBarriers = components.reduce((s, c) => s + c.barrier_count, 0);
  const total = totalEnablers + totalBarriers;
  const readiness = total > 0 ? Math.round((totalEnablers / total) * 100) : 0;

  // Collect all section-level report sections from components for inline editing
  const sectionEntries: { id: string; key: string; content: string; componentName: string }[] = [];
  components.forEach((comp) => {
    const name = COMPONENT_NAMES[comp.component] || comp.component;
    Object.entries(comp.report_sections).forEach(([key, section]) => {
      if (section.content) {
        sectionEntries.push({
          id: section.id,
          key,
          content: section.content,
          componentName: name,
        });
      }
    });
  });

  return (
    <div className="space-y-6 page-enter">
      {/* Executive Summary */}
      <Card className="shadow-card">
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-medium text-muted-foreground uppercase tracking-wider inline-flex items-center gap-1.5">
            Executive Summary
            <Tooltip>
              <TooltipTrigger asChild>
                <HelpCircle className="h-4 w-4 text-muted-foreground cursor-help" />
              </TooltipTrigger>
              <TooltipContent side="bottom" className="max-w-[280px] text-sm">
                <p>AI-generated overview of key findings. Click the pencil icon to edit, or ask the Copilot to improve it.</p>
              </TooltipContent>
            </Tooltip>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <EditableSection
            title="Executive Summary"
            content={sehra.executive_summary || ""}
            onSave={handleSaveExecutiveSummary}
            onAskCopilot={handleAskCopilot}
            emptyText="No executive summary yet. Click Edit to add one, or run the AI analysis."
          />
        </CardContent>
      </Card>

      {/* Recommendations */}
      <Card className="shadow-card">
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-medium text-muted-foreground uppercase tracking-wider inline-flex items-center gap-1.5">
            Recommendations
            <Tooltip>
              <TooltipTrigger asChild>
                <HelpCircle className="h-4 w-4 text-muted-foreground cursor-help" />
              </TooltipTrigger>
              <TooltipContent side="bottom" className="max-w-[280px] text-sm">
                <p>Strategic action items based on identified barriers. Designed for Ministry/NGO stakeholders.</p>
              </TooltipContent>
            </Tooltip>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <EditableSection
            title="Recommendations"
            content={sehra.recommendations || ""}
            onSave={handleSaveRecommendations}
            onAskCopilot={handleAskCopilot}
            emptyText="No recommendations yet. Click Edit to add them."
          />
        </CardContent>
      </Card>

      {/* Per-Component Report Sections */}
      {sectionEntries.length > 0 && (
        <Card className="shadow-card">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground uppercase tracking-wider inline-flex items-center gap-1.5">
              Component Summaries
              <Tooltip>
                <TooltipTrigger asChild>
                  <HelpCircle className="h-4 w-4 text-muted-foreground cursor-help" />
                </TooltipTrigger>
                <TooltipContent side="bottom" className="max-w-[280px] text-sm">
                  <p>Per-component analysis with enabler summaries, barrier summaries, and suggested action points. Click the pencil icon to edit any section.</p>
                </TooltipContent>
              </Tooltip>
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            {sectionEntries.map((entry) => {
              const sectionLabel = entry.key
                .replace(/_/g, " ")
                .replace(/\b\w/g, (c) => c.toUpperCase());
              const fullTitle = `${entry.componentName} - ${sectionLabel}`;
              return (
                <div
                  key={entry.id}
                  className="rounded-xl border border-gray-100 bg-gray-50/50 p-4"
                >
                  <EditableSection
                    title={fullTitle}
                    content={entry.content}
                    onSave={(newContent) =>
                      handleSaveSection(entry.id, newContent)
                    }
                    onAskCopilot={handleAskCopilot}
                  />
                </div>
              );
            })}
          </CardContent>
        </Card>
      )}

      {/* Scoring Summary */}
      {components.length > 0 && (
        <Card className="shadow-card">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-sm font-medium">
              <BarChart3 className="h-4 w-4 text-[#0D7377]" />
              Assessment Scoring Summary
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* Overall metrics */}
            <div className="grid grid-cols-3 gap-4">
              <div className="rounded-xl border-l-4 border-[#0D7377] bg-[#0D7377]/5 p-3">
                <p className="text-2xl font-bold text-[#0D7377]">
                  {totalEnablers}
                </p>
                <p className="text-xs text-muted-foreground">Total Enablers</p>
              </div>
              <div className="rounded-xl border-l-4 border-[#CC3333] bg-[#CC3333]/5 p-3">
                <p className="text-2xl font-bold text-[#CC3333]">
                  {totalBarriers}
                </p>
                <p className="text-xs text-muted-foreground">Total Barriers</p>
              </div>
              <div className="rounded-xl border-l-4 border-gray-400 bg-gray-50 p-3">
                <p className="text-2xl font-bold">{readiness}%</p>
                <p className="text-xs text-muted-foreground">
                  Overall Readiness
                </p>
              </div>
            </div>

            {/* Per-component breakdown */}
            <div className="overflow-hidden rounded-xl border">
              <table className="w-full text-sm">
                <thead>
                  <tr className="bg-[#0D7377] text-white">
                    <th className="px-4 py-2.5 text-left font-medium">
                      Component
                    </th>
                    <th className="px-4 py-2.5 text-center font-medium">
                      Enablers
                    </th>
                    <th className="px-4 py-2.5 text-center font-medium">
                      Barriers
                    </th>
                    <th className="px-4 py-2.5 text-center font-medium">
                      Readiness
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {components.map((c, i) => {
                    const ct = c.enabler_count + c.barrier_count;
                    const cr =
                      ct > 0
                        ? Math.round((c.enabler_count / ct) * 100)
                        : 0;
                    return (
                      <tr
                        key={c.id}
                        className={`border-b last:border-0 transition-colors hover:bg-gray-50 ${i % 2 === 1 ? "bg-gray-50/50" : ""}`}
                      >
                        <td className="px-4 py-2.5 font-medium">
                          {COMPONENT_NAMES[c.component] || c.component}
                        </td>
                        <td className="px-4 py-2.5 text-center">
                          <span className="inline-flex items-center gap-1 text-[#0D7377]">
                            <CheckCircle2 className="h-3.5 w-3.5" />
                            {c.enabler_count}
                          </span>
                        </td>
                        <td className="px-4 py-2.5 text-center">
                          <span className="inline-flex items-center gap-1 text-[#CC3333]">
                            <XCircle className="h-3.5 w-3.5" />
                            {c.barrier_count}
                          </span>
                        </td>
                        <td className="px-4 py-2.5 text-center">
                          <div className="mx-auto w-20">
                            <div className="h-2 rounded-full bg-gray-200 overflow-hidden">
                              <div
                                className="h-2 rounded-full transition-all"
                                style={{
                                  width: `${cr}%`,
                                  background: `linear-gradient(90deg, #0D7377, #14967E)`,
                                }}
                              />
                            </div>
                            <span className="text-xs text-muted-foreground">
                              {cr}%
                            </span>
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>

            {!hasSummary && (
              <p className="text-xs text-muted-foreground italic">
                AI-generated executive summary and recommendations will appear
                above once the analysis includes text remarks from the SEHRA PDF.
              </p>
            )}
          </CardContent>
        </Card>
      )}

      {/* No data at all */}
      {!hasSummary && components.length === 0 && (
        <div className="flex h-[40vh] items-center justify-center">
          <div className="text-center">
            <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-full bg-gray-100">
              <FileText className="h-6 w-6 text-muted-foreground" />
            </div>
            <h3 className="font-semibold">No report available yet</h3>
            <p className="mt-1 text-sm text-muted-foreground">
              The report will appear here once the assessment has been analyzed.
            </p>
          </div>
        </div>
      )}

      {/* Download buttons */}
      <div className="flex gap-3">
        <Button
          variant="outline"
          size="sm"
          onClick={() => handleDownload("docx")}
          className="rounded-lg"
        >
          <FileText className="mr-2 h-4 w-4" />
          Download DOCX
        </Button>
        <Button
          variant="outline"
          size="sm"
          onClick={() => handleDownload("pdf")}
          className="rounded-lg"
        >
          <FileDown className="mr-2 h-4 w-4" />
          Download PDF
        </Button>
      </div>
    </div>
  );
}
