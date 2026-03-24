"use client";

import Link from "next/link";
import { Upload, ClipboardList, FileText, AlertCircle, RefreshCw } from "lucide-react";
import { Button } from "@/components/ui/button";
import { InfoTooltip } from "@/components/ui/info-tooltip";
import { useSehras, useComponents } from "@/hooks/use-sehras";
import { AssessmentCard } from "@/components/assessments/assessment-card";
import type { ComponentAnalysis } from "@/lib/types";

function computeEnablerRate(components: ComponentAnalysis[]) {
  const enablers = components.reduce((s, c) => s + c.enabler_count, 0);
  const total =
    enablers + components.reduce((s, c) => s + c.barrier_count, 0);
  return total > 0 ? Math.round((enablers / total) * 100) : 0;
}

function CardWithRate({
  sehra,
}: {
  sehra: {
    id: string;
    country: string;
    district: string;
    province: string;
    assessment_date: string | null;
    upload_date: string | null;
    status: string;
    pdf_filename: string;
  };
}) {
  const { components } = useComponents(sehra.id);
  const rate = computeEnablerRate(components);
  return <AssessmentCard sehra={sehra} enablerRate={rate} />;
}

function LoadingSkeleton() {
  return (
    <div className="space-y-6 page-enter">
      <div className="flex items-center justify-between">
        <div className="space-y-2">
          <div className="h-6 w-40 rounded-lg skeleton-shimmer" />
          <div className="h-3 w-24 rounded skeleton-shimmer" />
        </div>
        <div className="flex gap-2">
          <div className="h-9 w-28 rounded-lg skeleton-shimmer" />
          <div className="h-9 w-28 rounded-lg skeleton-shimmer" />
        </div>
      </div>
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {[...Array(6)].map((_, i) => (
          <div
            key={i}
            className="rounded-xl border border-gray-100 p-5 space-y-4"
          >
            <div className="flex justify-between items-start">
              <div className="space-y-2">
                <div className="h-5 w-32 rounded skeleton-shimmer" />
                <div className="h-3 w-20 rounded skeleton-shimmer" />
              </div>
              <div className="h-5 w-16 rounded-full skeleton-shimmer" />
            </div>
            <div className="space-y-2">
              <div className="flex justify-between">
                <div className="h-3 w-24 rounded skeleton-shimmer" />
                <div className="h-3 w-10 rounded skeleton-shimmer" />
              </div>
              <div className="h-2 w-full rounded-full skeleton-shimmer" />
            </div>
            <div className="flex gap-2">
              <div className="h-6 w-20 rounded skeleton-shimmer" />
              <div className="h-6 w-20 rounded skeleton-shimmer" />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function EmptyState() {
  return (
    <div className="flex h-[60vh] items-center justify-center page-enter">
      <div className="text-center max-w-md">
        <div className="mx-auto mb-5 flex h-16 w-16 items-center justify-center rounded-2xl bg-[#0D7377]/10">
          <FileText className="h-7 w-7 text-[#0D7377]" />
        </div>
        <h2 className="text-lg font-semibold">No assessments yet</h2>
        <p className="mt-2 text-sm text-muted-foreground">
          Get started by uploading a completed SEHRA assessment PDF or
          filling in data manually. Your assessments will appear here.
        </p>
        <div className="mt-6 flex flex-col sm:flex-row gap-3 justify-center">
          <Button asChild className="bg-[#0D7377] hover:bg-[#095456]">
            <Link href="/upload">
              <Upload className="mr-2 h-4 w-4" />
              Upload SEHRA PDF
            </Link>
          </Button>
          <Button asChild variant="outline">
            <Link href="/collect">
              <ClipboardList className="mr-2 h-4 w-4" />
              Enter Data Manually
            </Link>
          </Button>
        </div>
      </div>
    </div>
  );
}

function ErrorState({ onRetry }: { onRetry: () => void }) {
  return (
    <div className="flex h-[60vh] items-center justify-center page-enter">
      <div className="text-center max-w-md">
        <div className="mx-auto mb-5 flex h-16 w-16 items-center justify-center rounded-2xl bg-red-50">
          <AlertCircle className="h-7 w-7 text-red-500" />
        </div>
        <h2 className="text-lg font-semibold">Failed to load assessments</h2>
        <p className="mt-2 text-sm text-muted-foreground">
          Something went wrong while fetching your assessments. Please check
          your connection and try again.
        </p>
        <Button
          onClick={onRetry}
          variant="outline"
          className="mt-4"
        >
          <RefreshCw className="mr-2 h-4 w-4" />
          Try Again
        </Button>
      </div>
    </div>
  );
}

export default function AssessmentsPage() {
  const { sehras, isLoading, error, mutate } = useSehras();

  if (isLoading) {
    return <LoadingSkeleton />;
  }

  if (error) {
    return <ErrorState onRetry={() => mutate()} />;
  }

  if (sehras.length === 0) {
    return <EmptyState />;
  }

  return (
    <div className="space-y-6 page-enter">
      <div className="flex items-center justify-between">
        <div>
          <div className="flex items-center gap-1">
            <h2 className="text-lg font-semibold tracking-tight">
              All Assessments
            </h2>
            <InfoTooltip
              text="All SEHRA assessments uploaded to the platform. Click any card to view its analysis, edit results, or export reports."
              side="right"
              maxWidth="max-w-[300px]"
            />
          </div>
          <p className="text-xs text-muted-foreground mt-0.5">
            {sehras.length} assessment{sehras.length !== 1 ? "s" : ""}
          </p>
        </div>
        <div className="flex gap-2">
          <Button asChild variant="outline" size="sm" className="rounded-lg">
            <Link href="/upload">
              <Upload className="mr-2 h-4 w-4" />
              Upload
            </Link>
          </Button>
          <Button asChild variant="outline" size="sm" className="rounded-lg">
            <Link href="/collect">
              <ClipboardList className="mr-2 h-4 w-4" />
              Collect
            </Link>
          </Button>
        </div>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 stagger-enter">
        {sehras.map((s) => (
          <CardWithRate key={s.id} sehra={s} />
        ))}
      </div>
    </div>
  );
}
