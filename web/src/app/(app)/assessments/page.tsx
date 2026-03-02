"use client";

import Link from "next/link";
import { Upload, ClipboardList } from "lucide-react";
import { Skeleton } from "@/components/ui/skeleton";
import { Button } from "@/components/ui/button";
import { useSehras, useComponents } from "@/hooks/use-sehras";
import { AssessmentCard } from "@/components/assessments/assessment-card";
import type { ComponentAnalysis } from "@/lib/types";

function computeEnablerRate(components: ComponentAnalysis[]) {
  const enablers = components.reduce((s, c) => s + c.enabler_count, 0);
  const total = enablers + components.reduce((s, c) => s + c.barrier_count, 0);
  return total > 0 ? Math.round((enablers / total) * 100) : 0;
}

function CardWithRate({ sehra }: { sehra: { id: string; country: string; district: string; province: string; assessment_date: string | null; upload_date: string | null; status: string; pdf_filename: string } }) {
  const { components } = useComponents(sehra.id);
  const rate = computeEnablerRate(components);
  return <AssessmentCard sehra={sehra} enablerRate={rate} />;
}

export default function AssessmentsPage() {
  const { sehras, isLoading } = useSehras();

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <Skeleton className="h-8 w-40" />
          <div className="flex gap-2">
            <Skeleton className="h-9 w-24" />
            <Skeleton className="h-9 w-24" />
          </div>
        </div>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {[...Array(3)].map((_, i) => (
            <Skeleton key={i} className="h-48 rounded-lg" />
          ))}
        </div>
      </div>
    );
  }

  if (sehras.length === 0) {
    return (
      <div className="flex h-[60vh] items-center justify-center">
        <div className="text-center max-w-md">
          <h2 className="text-lg font-semibold">
            Welcome to SEHRA Analysis
          </h2>
          <p className="mt-2 text-sm text-muted-foreground">
            Get started by uploading a completed SEHRA assessment PDF or
            filling in data manually.
          </p>
          <div className="mt-6 grid gap-3 sm:grid-cols-2">
            <Link
              href="/upload"
              className="flex flex-col items-center gap-2 rounded-lg border p-4 hover:bg-muted transition-colors"
            >
              <Upload className="h-6 w-6 text-muted-foreground" />
              <span className="text-sm font-medium">Upload PDF</span>
              <span className="text-xs text-muted-foreground text-center">
                Have a completed assessment? Upload the PDF for automatic
                analysis.
              </span>
            </Link>
            <Link
              href="/collect"
              className="flex flex-col items-center gap-2 rounded-lg border p-4 hover:bg-muted transition-colors"
            >
              <ClipboardList className="h-6 w-6 text-muted-foreground" />
              <span className="text-sm font-medium">Collect Data</span>
              <span className="text-xs text-muted-foreground text-center">
                Fill in assessment data step by step using the guided form.
              </span>
            </Link>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold">All Assessments</h2>
        <div className="flex gap-2">
          <Button asChild variant="outline" size="sm">
            <Link href="/upload">
              <Upload className="mr-2 h-4 w-4" />
              Upload
            </Link>
          </Button>
          <Button asChild variant="outline" size="sm">
            <Link href="/collect">
              <ClipboardList className="mr-2 h-4 w-4" />
              Collect
            </Link>
          </Button>
        </div>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {sehras.map((s) => (
          <CardWithRate key={s.id} sehra={s} />
        ))}
      </div>
    </div>
  );
}
