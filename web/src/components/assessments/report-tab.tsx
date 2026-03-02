"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { FileText, FileDown, CheckCircle2, XCircle } from "lucide-react";
import { apiDownload } from "@/lib/api-client";
import { toast } from "sonner";
import { useComponents } from "@/hooks/use-sehras";
import type { SEHRADetail } from "@/lib/types";

interface ReportTabProps {
  sehra: SEHRADetail;
}

const COMPONENT_NAMES: Record<string, string> = {
  context: "Context",
  policy: "Policy & Strategy",
  service_delivery: "Service Delivery",
  human_resources: "Human Resources",
  supply_chain: "Supply Chain",
  barriers: "Barriers",
};

export function ReportTab({ sehra }: ReportTabProps) {
  const { components } = useComponents(sehra.id);

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

  const hasSummary = sehra.executive_summary || sehra.recommendations;
  const totalEnablers = components.reduce((s, c) => s + c.enabler_count, 0);
  const totalBarriers = components.reduce((s, c) => s + c.barrier_count, 0);
  const total = totalEnablers + totalBarriers;
  const readiness = total > 0 ? Math.round((totalEnablers / total) * 100) : 0;

  return (
    <div className="space-y-6">
      {/* Executive Summary */}
      {sehra.executive_summary && (
        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-medium">
              Executive Summary
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="whitespace-pre-wrap text-sm leading-relaxed">
              {sehra.executive_summary}
            </p>
          </CardContent>
        </Card>
      )}

      {/* Recommendations */}
      {sehra.recommendations && (
        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-medium">
              Recommendations
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="whitespace-pre-wrap text-sm leading-relaxed">
              {sehra.recommendations}
            </p>
          </CardContent>
        </Card>
      )}

      {/* Scoring Summary — always shown when components exist */}
      {components.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-medium">
              Assessment Scoring Summary
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* Overall metrics */}
            <div className="grid grid-cols-3 gap-4">
              <div className="rounded-lg border-l-4 border-[#0D7377] bg-[#0D7377]/5 p-3">
                <p className="text-2xl font-bold text-[#0D7377]">{totalEnablers}</p>
                <p className="text-xs text-muted-foreground">Total Enablers</p>
              </div>
              <div className="rounded-lg border-l-4 border-[#CC3333] bg-[#CC3333]/5 p-3">
                <p className="text-2xl font-bold text-[#CC3333]">{totalBarriers}</p>
                <p className="text-xs text-muted-foreground">Total Barriers</p>
              </div>
              <div className="rounded-lg border-l-4 border-gray-400 bg-gray-50 p-3">
                <p className="text-2xl font-bold">{readiness}%</p>
                <p className="text-xs text-muted-foreground">Overall Readiness</p>
              </div>
            </div>

            {/* Per-component breakdown */}
            <div className="overflow-hidden rounded-lg border">
              <table className="w-full text-sm">
                <thead>
                  <tr className="bg-[#0D7377] text-white">
                    <th className="px-3 py-2 text-left font-medium">Component</th>
                    <th className="px-3 py-2 text-center font-medium">Enablers</th>
                    <th className="px-3 py-2 text-center font-medium">Barriers</th>
                    <th className="px-3 py-2 text-center font-medium">Readiness</th>
                  </tr>
                </thead>
                <tbody>
                  {components.map((c) => {
                    const ct = c.enabler_count + c.barrier_count;
                    const cr = ct > 0 ? Math.round((c.enabler_count / ct) * 100) : 0;
                    return (
                      <tr key={c.id} className="border-b last:border-0 hover:bg-gray-50">
                        <td className="px-3 py-2 font-medium">
                          {COMPONENT_NAMES[c.component] || c.component}
                        </td>
                        <td className="px-3 py-2 text-center">
                          <span className="inline-flex items-center gap-1 text-[#0D7377]">
                            <CheckCircle2 className="h-3.5 w-3.5" />
                            {c.enabler_count}
                          </span>
                        </td>
                        <td className="px-3 py-2 text-center">
                          <span className="inline-flex items-center gap-1 text-[#CC3333]">
                            <XCircle className="h-3.5 w-3.5" />
                            {c.barrier_count}
                          </span>
                        </td>
                        <td className="px-3 py-2 text-center">
                          <div className="mx-auto w-16">
                            <div className="h-1.5 rounded-full bg-gray-200">
                              <div
                                className="h-1.5 rounded-full bg-[#0D7377]"
                                style={{ width: `${cr}%` }}
                              />
                            </div>
                            <span className="text-xs text-muted-foreground">{cr}%</span>
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
                AI-generated executive summary and recommendations will appear above once the analysis includes text remarks from the SEHRA PDF.
              </p>
            )}
          </CardContent>
        </Card>
      )}

      {/* No data at all */}
      {!hasSummary && components.length === 0 && (
        <div className="flex h-[40vh] items-center justify-center">
          <div className="text-center">
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
        >
          <FileText className="mr-2 h-4 w-4" />
          Download DOCX
        </Button>
        <Button
          variant="outline"
          size="sm"
          onClick={() => handleDownload("pdf")}
        >
          <FileDown className="mr-2 h-4 w-4" />
          Download PDF
        </Button>
      </div>
    </div>
  );
}
