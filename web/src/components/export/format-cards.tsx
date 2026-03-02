"use client";

import { useState } from "react";
import { FileText, Table2, Globe, FileDown, Loader2 } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
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
  },
  {
    key: "xlsx",
    label: "Excel Spreadsheet",
    description: "Data tables and metrics in spreadsheet format",
    icon: Table2,
    ext: "xlsx",
  },
  {
    key: "pdf",
    label: "PDF Report",
    description: "Print-ready formatted report document",
    icon: FileDown,
    ext: "pdf",
  },
  {
    key: "html",
    label: "HTML Report",
    description: "Web-viewable report with interactive elements",
    icon: Globe,
    ext: "html",
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
              <h3 className="font-medium">{f.label}</h3>
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
