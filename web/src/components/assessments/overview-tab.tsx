"use client";

import dynamic from "next/dynamic";
import { Skeleton } from "@/components/ui/skeleton";
import { KPICards } from "@/components/dashboard/kpi-cards";
import type { ComponentAnalysis } from "@/lib/types";

const ChartSkeleton = () => <Skeleton className="h-[360px] rounded-lg" />;

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

export function OverviewTab({ components }: OverviewTabProps) {
  return (
    <div className="space-y-6">
      <KPICards components={components} />
      <div className="grid gap-6 lg:grid-cols-2">
        <EnablerRadarChart components={components} />
        <EnablerBarrierChart components={components} />
      </div>
    </div>
  );
}
