"use client";

import { PDFDropzone } from "@/components/upload/pdf-dropzone";
import { AnalysisProgress } from "@/components/upload/analysis-progress";
import { InfoTooltip } from "@/components/ui/info-tooltip";
import { useSSE } from "@/hooks/use-sse";
import { useSehras } from "@/hooks/use-sehras";
import Link from "next/link";
import { FileText, Clock, ChevronRight } from "lucide-react";

function RecentUploads() {
  const { sehras, isLoading } = useSehras();

  if (isLoading || sehras.length === 0) return null;

  // Show only the 5 most recent uploads
  const recent = sehras
    .filter((s) => s.upload_date)
    .sort(
      (a, b) =>
        new Date(b.upload_date!).getTime() - new Date(a.upload_date!).getTime(),
    )
    .slice(0, 5);

  if (recent.length === 0) return null;

  return (
    <div className="rounded-xl border border-gray-100 bg-gray-50/50 p-4">
      <div className="flex items-center gap-2 mb-3">
        <Clock className="h-4 w-4 text-muted-foreground" />
        <h3 className="text-sm font-medium">Recent Uploads</h3>
      </div>
      <div className="space-y-1.5">
        {recent.map((s) => (
          <Link
            key={s.id}
            href={`/assessments/${s.id}`}
            className="flex items-center justify-between rounded-lg px-3 py-2 text-sm hover:bg-white transition-colors group"
          >
            <div className="flex items-center gap-2.5 min-w-0">
              <FileText className="h-4 w-4 text-[#0D7377] shrink-0" />
              <span className="truncate font-medium">
                {s.country}
                {s.district ? ` - ${s.district}` : ""}
              </span>
            </div>
            <div className="flex items-center gap-2 shrink-0">
              <span className="text-xs text-muted-foreground">
                {s.upload_date
                  ? new Date(s.upload_date).toLocaleDateString("en-US", {
                      month: "short",
                      day: "numeric",
                    })
                  : ""}
              </span>
              <ChevronRight className="h-3.5 w-3.5 text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity" />
            </div>
          </Link>
        ))}
      </div>
    </div>
  );
}

export default function UploadPage() {
  const sse = useSSE();

  return (
    <div className="mx-auto max-w-2xl space-y-6 page-enter">
      <div>
        <div className="flex items-center gap-1">
          <h2 className="text-lg font-semibold">Upload SEHRA PDF</h2>
          <InfoTooltip
            text="Upload a completed SEHRA PDF (max 50MB). The system will automatically extract all questions, score them, and run AI analysis."
            side="right"
            maxWidth="max-w-[300px]"
          />
        </div>
        <p className="text-sm text-muted-foreground">
          Upload a completed SEHRA assessment PDF. The system will automatically
          extract all responses, score them, and classify findings as enablers or
          barriers using AI.
        </p>
      </div>

      <div className="rounded-lg border border-blue-200 bg-blue-50 px-4 py-3 text-sm text-blue-800">
        <p className="font-medium mb-1">How it works</p>
        <ol className="list-decimal list-inside space-y-0.5 text-xs text-blue-700">
          <li>Drop your PDF or click to browse</li>
          <li>AI extracts responses from each section</li>
          <li>Findings are classified as enablers or barriers</li>
          <li>Review results on the Dashboard</li>
        </ol>
      </div>

      <PDFDropzone
        onFileSelect={(file) => sse.startUpload(file)}
        disabled={sse.status === "running"}
      />

      <AnalysisProgress
        status={sse.status}
        step={sse.step}
        totalSteps={sse.totalSteps}
        label={sse.label}
        progress={sse.progress}
        sehraId={sse.sehraId}
        enablerCount={sse.enablerCount}
        barrierCount={sse.barrierCount}
        errorMessage={sse.errorMessage}
        onCancel={sse.cancel}
        onReset={sse.reset}
      />

      <RecentUploads />
    </div>
  );
}
