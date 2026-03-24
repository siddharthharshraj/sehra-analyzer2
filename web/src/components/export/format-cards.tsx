"use client";

import { useState } from "react";
import { FileText, Table2, Globe, FileDown, Loader2, HelpCircle } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { apiDownload } from "@/lib/api-client";
import { toast } from "sonner";

interface FormatCardsProps {
  sehraId: string;
  country: string;
}

const formats = [
  {
    key: "docx",
    label: "Word Document",
    description: "Full report with formatting, charts, and tables",
    icon: FileText,
    ext: "docx",
    tooltip: "Download a Word document with charts, tables, and narrative sections. Best for editing and printing.",
  },
  {
    key: "xlsx",
    label: "Excel Spreadsheet",
    description: "Data tables and metrics in spreadsheet format",
    icon: Table2,
    ext: "xlsx",
    tooltip: "Download an Excel workbook with multiple sheets — scores, themes, entries, and raw data. Best for further analysis.",
  },
  {
    key: "pdf",
    label: "PDF Report",
    description: "Print-ready formatted report document",
    icon: FileDown,
    ext: "pdf",
    tooltip: "Download a formatted PDF report. Best for sharing via email.",
  },
  {
    key: "html",
    label: "HTML Report",
    description: "Web-viewable report with interactive elements",
    icon: Globe,
    ext: "html",
    tooltip: "Download a self-contained HTML report with interactive charts. Can be opened in any browser without internet.",
  },
];

export function FormatCards({ sehraId, country }: FormatCardsProps) {
  const [generating, setGenerating] = useState<string | null>(null);

  async function handleDownload(format: string, ext: string) {
    setGenerating(format);
    try {
      const filename = `SEHRA_${country}_${sehraId.slice(0, 8)}.${ext}`;
      await apiDownload(`/export/${sehraId}/${format}`, filename);
      toast.success(`${ext.toUpperCase()} downloaded`);
    } catch (err) {
      toast.error(
        err instanceof Error ? err.message : "Download failed",
      );
    } finally {
      setGenerating(null);
    }
  }

  return (
    <div className="grid gap-4 sm:grid-cols-2">
      {formats.map((f) => (
        <Card key={f.key}>
          <CardContent className="flex items-start gap-4 pt-6">
            <div className="rounded-lg bg-[#0D7377]/10 p-2.5">
              <f.icon className="h-5 w-5 text-[#0D7377]" />
            </div>
            <div className="flex-1">
              <h3 className="font-medium inline-flex items-center gap-1.5">
                {f.label}
                <Tooltip>
                  <TooltipTrigger asChild>
                    <HelpCircle className="h-4 w-4 text-muted-foreground cursor-help" />
                  </TooltipTrigger>
                  <TooltipContent side="bottom" className="max-w-[280px] text-sm">
                    <p>{f.tooltip}</p>
                  </TooltipContent>
                </Tooltip>
              </h3>
              <p className="mb-3 text-sm text-muted-foreground">
                {f.description}
              </p>
              <Button
                size="sm"
                variant="outline"
                disabled={generating !== null}
                onClick={() => handleDownload(f.key, f.ext)}
              >
                {generating === f.key ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Generating…
                  </>
                ) : (
                  "Generate"
                )}
              </Button>
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
