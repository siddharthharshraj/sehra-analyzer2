"use client";

import dynamic from "next/dynamic";
import { Skeleton } from "@/components/ui/skeleton";
import { ReviewControls } from "@/components/dashboard/review-controls";
import type { SEHRADetail, ComponentAnalysis } from "@/lib/types";

const ComponentTabs = dynamic(
  () =>
    import("@/components/dashboard/component-tabs").then(
      (m) => m.ComponentTabs,
    ),
  { loading: () => <Skeleton className="h-64 rounded-lg" /> },
);

interface AnalysisTabProps {
  sehra: SEHRADetail;
  components: ComponentAnalysis[];
  onRefresh: () => void;
}

export function AnalysisTab({ sehra, components, onRefresh }: AnalysisTabProps) {
  return (
    <div className="space-y-6">
      <ReviewControls sehra={sehra} onRefresh={onRefresh} />
      <ComponentTabs components={components} onRefresh={onRefresh} />
    </div>
  );
}
