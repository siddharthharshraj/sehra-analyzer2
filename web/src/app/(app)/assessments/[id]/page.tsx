"use client";

import { useEffect } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { ChevronLeft } from "lucide-react";
import { Skeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useSehra, useComponents } from "@/hooks/use-sehras";
import { useCopilotContext } from "@/components/copilot/copilot-context";
import { STATUS_COLORS } from "@/lib/constants";
import { OverviewTab } from "@/components/assessments/overview-tab";
import { ReportTab } from "@/components/assessments/report-tab";
import { AnalysisTab } from "@/components/assessments/analysis-tab";
import { ExportTab } from "@/components/assessments/export-tab";

export default function AssessmentDetailPage() {
  const params = useParams<{ id: string }>();
  const sehraId = params.id;
  const { sehra, isLoading: sehraLoading, mutate: mutateSehra } = useSehra(sehraId);
  const {
    components,
    isLoading: componentsLoading,
    mutate: mutateComponents,
  } = useComponents(sehraId);
  const { setSehraId, setSehraLabel } = useCopilotContext();

  // Sync copilot context
  useEffect(() => {
    setSehraId(sehraId);
    if (sehra) {
      setSehraLabel(
        `${sehra.country}${sehra.district ? ` - ${sehra.district}` : ""}`,
      );
    }
    return () => {
      setSehraId(null);
      setSehraLabel(null);
    };
  }, [sehraId, sehra, setSehraId, setSehraLabel]);

  function handleRefresh() {
    mutateSehra();
    mutateComponents();
  }

  const label = sehra
    ? `${sehra.country}${sehra.district ? ` - ${sehra.district}` : ""}`
    : sehraId.slice(0, 8);

  if (sehraLoading || componentsLoading) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-6 w-48" />
        <Skeleton className="h-10 w-full" />
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {[...Array(4)].map((_, i) => (
            <Skeleton key={i} className="h-24" />
          ))}
        </div>
      </div>
    );
  }

  if (!sehra) {
    return (
      <div className="flex h-[60vh] items-center justify-center">
        <div className="text-center">
          <h2 className="text-lg font-semibold">Assessment not found</h2>
          <p className="mt-1 text-sm text-muted-foreground">
            This assessment may have been deleted or the link is invalid.
          </p>
          <Link
            href="/assessments"
            className="mt-4 inline-block text-sm text-[#0D7377] hover:underline"
          >
            Back to assessments
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Breadcrumb header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2 text-sm">
          <Link
            href="/assessments"
            className="flex items-center gap-1 text-muted-foreground hover:text-foreground transition-colors"
          >
            <ChevronLeft className="h-4 w-4" />
            Assessments
          </Link>
          <span className="text-muted-foreground">/</span>
          <span className="font-medium">{label}</span>
        </div>
        <Badge className={STATUS_COLORS[sehra.status] || ""}>
          {sehra.status}
        </Badge>
      </div>

      {/* Tabs */}
      <Tabs defaultValue="overview">
        <TabsList>
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="report">Report</TabsTrigger>
          <TabsTrigger value="analysis">Analysis</TabsTrigger>
          <TabsTrigger value="export">Export</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="mt-6">
          <OverviewTab components={components} />
        </TabsContent>

        <TabsContent value="report" className="mt-6">
          <ReportTab sehra={sehra} />
        </TabsContent>

        <TabsContent value="analysis" className="mt-6">
          <AnalysisTab
            sehra={sehra}
            components={components}
            onRefresh={handleRefresh}
          />
        </TabsContent>

        <TabsContent value="export" className="mt-6">
          <ExportTab sehraId={sehraId} country={sehra.country} />
        </TabsContent>
      </Tabs>
    </div>
  );
}
