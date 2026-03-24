"use client";

import dynamic from "next/dynamic";
import { Skeleton } from "@/components/ui/skeleton";
import { BarChart3 } from "lucide-react";
import { KPICards } from "@/components/dashboard/kpi-cards";
import type { ComponentAnalysis } from "@/lib/types";

const ChartSkeleton = () => (
  <div className="rounded-xl border bg-card p-6">
    <Skeleton className="mb-4 h-5 w-40" />
    <Skeleton className="h-[300px] rounded-lg" />
  </div>
);

const EnablerRadarChart = dynamic(
  () =>
    import("@/components/dashboard/radar-chart").then(
      (m) => m.EnablerRadarChart,
    ),
  { ssr: false, loading: ChartSkeleton },
);

const EnablerBarrierChart = dynamic(
  () =>
    import("@/components/dashboard/bar-chart").then(
      (m) => m.EnablerBarrierChart,
    ),
  { ssr: false, loading: ChartSkeleton },
);

interface OverviewTabProps {
  components: ComponentAnalysis[];
}

function EmptyOverview() {
  return (
    <div className="flex flex-col items-center justify-center py-20 text-center page-enter">
      <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-gray-100">
        <BarChart3 className="h-6 w-6 text-muted-foreground" />
      </div>
      <h3 className="text-sm font-semibold">No data available</h3>
      <p className="mt-1 text-xs text-muted-foreground max-w-xs">
        This assessment has no component data yet. Upload a PDF or enter data
        manually to see KPI metrics and charts here.
      </p>
    </div>
  );
}

export function OverviewTab({ components }: OverviewTabProps) {
  if (components.length === 0) {
    return <EmptyOverview />;
  }

  return (
    <div className="space-y-6 page-enter">
      <KPICards components={components} />
      <div className="grid gap-6 lg:grid-cols-2">
        <EnablerRadarChart components={components} />
        <EnablerBarrierChart components={components} />
      </div>
    </div>
  );
}
