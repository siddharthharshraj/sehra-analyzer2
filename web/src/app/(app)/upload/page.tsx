"use client";

import { PDFDropzone } from "@/components/upload/pdf-dropzone";
import { AnalysisProgress } from "@/components/upload/analysis-progress";
import { useSSE } from "@/hooks/use-sse";

export default function UploadPage() {
  const sse = useSSE();

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <div>
        <h2 className="text-lg font-semibold">Upload SEHRA PDF</h2>
        <p className="text-sm text-muted-foreground">
          Upload a completed SEHRA assessment PDF. The system will automatically extract all responses, score them, and classify findings as enablers or barriers using AI.
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
    </div>
  );
}
