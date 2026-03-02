"use client";

import { CheckCircle2, XCircle, Loader2 } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Button } from "@/components/ui/button";
import Link from "next/link";

interface AnalysisProgressProps {
  status: "idle" | "running" | "complete" | "error";
  step: number;
  totalSteps: number;
  label: string;
  progress: number;
  sehraId: string | null;
  enablerCount: number;
  barrierCount: number;
  errorMessage: string | null;
  onCancel: () => void;
  onReset: () => void;
}

export function AnalysisProgress({
  status,
  step,
  totalSteps,
  label,
  progress,
  sehraId,
  enablerCount,
  barrierCount,
  errorMessage,
  onCancel,
  onReset,
}: AnalysisProgressProps) {
  if (status === "idle") return null;

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-sm font-medium">
          {status === "running" && "Analyzing..."}
          {status === "complete" && "Analysis Complete"}
          {status === "error" && "Analysis Failed"}
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {status === "running" && (
          <>
            <div className="flex items-center gap-3">
              <Loader2 className="h-5 w-5 animate-spin text-[#0D7377]" />
              <div className="flex-1">
                <p className="text-sm font-medium">{label}</p>
                <p className="text-xs text-muted-foreground">
                  Step {step} of {totalSteps}
                </p>
              </div>
            </div>
            <Progress value={progress * 100} className="h-2" />
            <Button variant="outline" size="sm" onClick={onCancel}>
              Cancel
            </Button>
          </>
        )}

        {status === "complete" && (
          <>
            <div className="flex items-center gap-3">
              <CheckCircle2 className="h-6 w-6 text-green-600" />
              <div>
                <p className="font-medium">
                  Assessment analyzed successfully
                </p>
                <p className="text-sm text-muted-foreground">
                  {enablerCount} enablers, {barrierCount} barriers identified
                </p>
              </div>
            </div>
            <div className="flex gap-2">
              <Button asChild className="bg-[#0D7377] hover:bg-[#095456]">
                <Link href="/dashboard">View Dashboard</Link>
              </Button>
              <Button variant="outline" onClick={onReset}>
                Upload Another
              </Button>
            </div>
          </>
        )}

        {status === "error" && (
          <>
            <div className="flex items-center gap-3">
              <XCircle className="h-6 w-6 text-destructive" />
              <div>
                <p className="font-medium">Analysis failed</p>
                <p className="text-sm text-muted-foreground">
                  {errorMessage}
                </p>
              </div>
            </div>
            <Button variant="outline" onClick={onReset}>
              Try Again
            </Button>
          </>
        )}
      </CardContent>
    </Card>
  );
}
