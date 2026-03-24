"use client";

import { useEffect, useMemo, Component, type ReactNode } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import {
  ChevronLeft,
  ChevronRight,
  BarChart3,
  FileText,
  Search,
  Download,
  CheckCircle2,
  XCircle,
  Activity,
  AlertCircle,
  RefreshCw,
  Clock,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { useSehra, useComponents } from "@/hooks/use-sehras";
import { useCopilotContext } from "@/components/copilot/copilot-context";
import { STATUS_COLORS } from "@/lib/constants";

const STATUS_HELP: Record<string, string> = {
  draft: "Analysis complete, pending human review. You can edit AI classifications before publishing.",
  reviewed: "Reviewed by an analyst and ready to publish. Share with stakeholders when ready.",
  published: "Final version shared with stakeholders. No further edits expected.",
};
import { OverviewTab } from "@/components/assessments/overview-tab";
import { ReportTab } from "@/components/assessments/report-tab";
import { AnalysisTab } from "@/components/assessments/analysis-tab";
import { ExportTab } from "@/components/assessments/export-tab";

/* ── Error Boundary for tab content ── */
interface ErrorBoundaryProps {
  children: ReactNode;
  fallback?: ReactNode;
}

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
}

class TabErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error) {
    return { hasError: true, error };
  }

  render() {
    if (this.state.hasError) {
      return (
        this.props.fallback || (
          <div className="flex flex-col items-center justify-center py-16 text-center">
            <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-xl bg-red-50">
              <AlertCircle className="h-6 w-6 text-red-500" />
            </div>
            <h3 className="text-sm font-semibold">Something went wrong</h3>
            <p className="mt-1 text-xs text-muted-foreground max-w-sm">
              This section failed to render. Try refreshing the page.
            </p>
            <Button
              variant="outline"
              size="sm"
              className="mt-3"
              onClick={() => this.setState({ hasError: false, error: null })}
            >
              <RefreshCw className="mr-1.5 h-3.5 w-3.5" />
              Retry
            </Button>
          </div>
        )
      );
    }
    return this.props.children;
  }
}

/* ── Time ago helper ── */
function timeAgo(dateStr: string | null): string | null {
  if (!dateStr) return null;
  const date = new Date(dateStr);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  if (diffMins < 1) return "just now";
  if (diffMins < 60) return `${diffMins}m ago`;
  const diffHours = Math.floor(diffMins / 60);
  if (diffHours < 24) return `${diffHours}h ago`;
  const diffDays = Math.floor(diffHours / 24);
  if (diffDays < 30) return `${diffDays}d ago`;
  const diffMonths = Math.floor(diffDays / 30);
  return `${diffMonths}mo ago`;
}

/* ── Loading skeleton ── */
function DetailSkeleton() {
  return (
    <div className="space-y-6 page-enter">
      {/* Breadcrumb skeleton */}
      <div className="flex items-center gap-2">
        <div className="h-8 w-8 rounded-lg skeleton-shimmer" />
        <div className="space-y-1.5">
          <div className="h-5 w-48 rounded skeleton-shimmer" />
          <div className="h-3 w-32 rounded skeleton-shimmer" />
        </div>
        <div className="ml-2 h-5 w-16 rounded-full skeleton-shimmer" />
      </div>
      {/* Stats bar skeleton */}
      <div className="flex flex-wrap gap-4 rounded-xl border border-gray-100 bg-gray-50/50 px-5 py-3">
        {[...Array(4)].map((_, i) => (
          <div key={i} className="flex items-center gap-2">
            <div className="h-4 w-4 rounded skeleton-shimmer" />
            <div className="h-4 w-8 rounded skeleton-shimmer" />
            <div className="h-3 w-16 rounded skeleton-shimmer" />
            {i < 3 && <div className="h-5 w-px bg-gray-200 ml-4" />}
          </div>
        ))}
      </div>
      {/* Tabs skeleton */}
      <div className="flex gap-1 border-b border-gray-200 pb-2">
        {[...Array(4)].map((_, i) => (
          <div key={i} className="h-9 w-24 rounded-lg skeleton-shimmer" />
        ))}
      </div>
      {/* Content skeleton */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {[...Array(4)].map((_, i) => (
          <div key={i} className="rounded-xl border border-gray-100 p-5 space-y-3">
            <div className="flex gap-3">
              <div className="h-10 w-10 rounded-xl skeleton-shimmer" />
              <div className="space-y-2 flex-1">
                <div className="h-6 w-16 rounded skeleton-shimmer" />
                <div className="h-3 w-24 rounded skeleton-shimmer" />
              </div>
            </div>
          </div>
        ))}
      </div>
      <div className="grid gap-6 lg:grid-cols-2">
        <div className="rounded-xl border p-6 space-y-4">
          <div className="h-5 w-40 rounded skeleton-shimmer" />
          <div className="h-[250px] rounded-lg skeleton-shimmer" />
        </div>
        <div className="rounded-xl border p-6 space-y-4">
          <div className="h-5 w-40 rounded skeleton-shimmer" />
          <div className="h-[250px] rounded-lg skeleton-shimmer" />
        </div>
      </div>
    </div>
  );
}

export default function AssessmentDetailPage() {
  const params = useParams<{ id: string }>();
  const sehraId = params.id;
  const {
    sehra,
    isLoading: sehraLoading,
    error: sehraError,
    mutate: mutateSehra,
  } = useSehra(sehraId);
  const {
    components,
    isLoading: componentsLoading,
    error: componentsError,
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

  const lastUpdated = useMemo(() => {
    if (!sehra) return null;
    return timeAgo(sehra.upload_date || sehra.assessment_date);
  }, [sehra]);

  if (sehraLoading || componentsLoading) {
    return <DetailSkeleton />;
  }

  if (sehraError || componentsError) {
    return (
      <div className="flex h-[60vh] items-center justify-center page-enter">
        <div className="text-center max-w-md">
          <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-full bg-red-50">
            <AlertCircle className="h-6 w-6 text-red-500" />
          </div>
          <h2 className="text-lg font-semibold">Failed to load assessment</h2>
          <p className="mt-1 text-sm text-muted-foreground">
            Could not fetch the assessment data. Please check your connection and try again.
          </p>
          <Button
            onClick={handleRefresh}
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

  if (!sehra) {
    return (
      <div className="flex h-[60vh] items-center justify-center page-enter">
        <div className="text-center">
          <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-full bg-gray-100">
            <Search className="h-6 w-6 text-muted-foreground" />
          </div>
          <h2 className="text-lg font-semibold">Assessment not found</h2>
          <p className="mt-1 text-sm text-muted-foreground">
            This assessment may have been deleted or the link is invalid.
          </p>
          <Link
            href="/assessments"
            className="mt-4 inline-flex items-center gap-1 text-sm text-[#0D7377] hover:underline"
          >
            <ChevronLeft className="h-3.5 w-3.5" />
            Back to assessments
          </Link>
        </div>
      </div>
    );
  }

  // Quick stats
  const totalEnablers = components.reduce((s, c) => s + c.enabler_count, 0);
  const totalBarriers = components.reduce((s, c) => s + c.barrier_count, 0);
  const total = totalEnablers + totalBarriers;
  const readiness = total > 0 ? Math.round((totalEnablers / total) * 100) : 0;

  return (
    <div className="space-y-6 page-enter">
      {/* Header with breadcrumb */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-center gap-3">
          <Link
            href="/assessments"
            className="flex h-8 w-8 items-center justify-center rounded-lg border border-gray-200 text-muted-foreground hover:text-foreground hover:bg-gray-50 transition-colors"
          >
            <ChevronLeft className="h-4 w-4" />
          </Link>
          <div>
            {/* Breadcrumb */}
            <nav className="flex items-center gap-1 text-xs text-muted-foreground mb-0.5">
              <Link href="/assessments" className="hover:text-foreground transition-colors">
                Assessments
              </Link>
              <ChevronRight className="h-3 w-3" />
              <span className="text-foreground font-medium">
                {sehra.country}
                {sehra.district ? ` - ${sehra.district}` : ""}
              </span>
            </nav>
            <h1 className="text-lg font-semibold tracking-tight">{label}</h1>
            <div className="flex items-center gap-2 mt-0.5">
              {sehra.assessment_date && (
                <p className="text-xs text-muted-foreground">
                  {new Date(sehra.assessment_date).toLocaleDateString("en-US", {
                    month: "long",
                    day: "numeric",
                    year: "numeric",
                  })}
                </p>
              )}
              {lastUpdated && (
                <span className="flex items-center gap-1 text-xs text-muted-foreground">
                  <Clock className="h-3 w-3" />
                  Updated {lastUpdated}
                </span>
              )}
            </div>
          </div>
          <TooltipProvider delayDuration={200}>
            <Tooltip>
              <TooltipTrigger asChild>
                <Badge
                  className={`ml-1 text-[10px] cursor-help ${STATUS_COLORS[sehra.status] || ""}`}
                >
                  {sehra.status}
                </Badge>
              </TooltipTrigger>
              <TooltipContent side="right" className="max-w-[260px] text-xs">
                {STATUS_HELP[sehra.status] || `Status: ${sehra.status}`}
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>
        </div>
      </div>

      {/* Quick stats bar */}
      {components.length > 0 && (
        <TooltipProvider delayDuration={200}>
          <div className="flex flex-wrap gap-4 rounded-xl border border-gray-100 bg-gray-50/50 px-5 py-3">
            <Tooltip>
              <TooltipTrigger asChild>
                <div className="flex items-center gap-2 cursor-help">
                  <CheckCircle2 className="h-4 w-4 text-[#0D7377]" />
                  <span className="text-sm font-medium">{totalEnablers}</span>
                  <span className="text-xs text-muted-foreground">Enablers</span>
                </div>
              </TooltipTrigger>
              <TooltipContent side="bottom" className="max-w-[240px] text-xs">
                Positive factors that support school eye health readiness. Higher is better.
              </TooltipContent>
            </Tooltip>
            <div className="h-5 w-px bg-gray-200" />
            <Tooltip>
              <TooltipTrigger asChild>
                <div className="flex items-center gap-2 cursor-help">
                  <XCircle className="h-4 w-4 text-[#CC3333]" />
                  <span className="text-sm font-medium">{totalBarriers}</span>
                  <span className="text-xs text-muted-foreground">Barriers</span>
                </div>
              </TooltipTrigger>
              <TooltipContent side="bottom" className="max-w-[240px] text-xs">
                Gaps or challenges identified. These are areas needing attention or intervention.
              </TooltipContent>
            </Tooltip>
            <div className="h-5 w-px bg-gray-200" />
            <Tooltip>
              <TooltipTrigger asChild>
                <div className="flex items-center gap-2 cursor-help">
                  <Activity className="h-4 w-4 text-[#0D7377]" />
                  <span className="text-sm font-medium">{readiness}%</span>
                  <span className="text-xs text-muted-foreground">Readiness</span>
                </div>
              </TooltipTrigger>
              <TooltipContent side="bottom" className="max-w-[260px] text-xs">
                Overall readiness score: percentage of enablers out of total findings. 100% means fully ready.
              </TooltipContent>
            </Tooltip>
            <div className="h-5 w-px bg-gray-200" />
            <Tooltip>
              <TooltipTrigger asChild>
                <div className="flex items-center gap-2 cursor-help">
                  <BarChart3 className="h-4 w-4 text-gray-500" />
                  <span className="text-sm font-medium">{components.length}</span>
                  <span className="text-xs text-muted-foreground">Components</span>
                </div>
              </TooltipTrigger>
              <TooltipContent side="bottom" className="max-w-[260px] text-xs">
                Number of SEHRA sections analyzed (e.g., Human Resources, Infrastructure, Governance).
              </TooltipContent>
            </Tooltip>
          </div>
        </TooltipProvider>
      )}

      {/* Tabs - underline style */}
      <Tabs defaultValue="overview">
        <TooltipProvider delayDuration={300}>
          <TabsList className="h-auto bg-transparent p-0 border-b border-gray-200 rounded-none w-full justify-start gap-0">
            <Tooltip>
              <TooltipTrigger asChild>
                <TabsTrigger
                  value="overview"
                  className="relative rounded-none border-b-2 border-transparent px-4 py-2.5 text-sm font-medium text-muted-foreground transition-colors data-[state=active]:border-[#0D7377] data-[state=active]:text-[#0D7377] data-[state=active]:shadow-none data-[state=active]:bg-transparent hover:text-foreground"
                >
                  <BarChart3 className="mr-1.5 h-3.5 w-3.5" />
                  Overview
                </TabsTrigger>
              </TooltipTrigger>
              <TooltipContent side="bottom" className="max-w-[260px] text-xs">
                High-level summary with enabler/barrier counts, readiness scores, and radar chart
              </TooltipContent>
            </Tooltip>
            <Tooltip>
              <TooltipTrigger asChild>
                <TabsTrigger
                  value="report"
                  className="relative rounded-none border-b-2 border-transparent px-4 py-2.5 text-sm font-medium text-muted-foreground transition-colors data-[state=active]:border-[#0D7377] data-[state=active]:text-[#0D7377] data-[state=active]:shadow-none data-[state=active]:bg-transparent hover:text-foreground"
                >
                  <FileText className="mr-1.5 h-3.5 w-3.5" />
                  Report
                </TabsTrigger>
              </TooltipTrigger>
              <TooltipContent side="bottom" className="max-w-[260px] text-xs">
                AI-generated narrative report with summaries and action points. Click edit to refine.
              </TooltipContent>
            </Tooltip>
            <Tooltip>
              <TooltipTrigger asChild>
                <TabsTrigger
                  value="analysis"
                  className="relative rounded-none border-b-2 border-transparent px-4 py-2.5 text-sm font-medium text-muted-foreground transition-colors data-[state=active]:border-[#0D7377] data-[state=active]:text-[#0D7377] data-[state=active]:shadow-none data-[state=active]:bg-transparent hover:text-foreground"
                >
                  <Search className="mr-1.5 h-3.5 w-3.5" />
                  Analysis
                </TabsTrigger>
              </TooltipTrigger>
              <TooltipContent side="bottom" className="max-w-[280px] text-xs">
                Detailed qualitative entries. Review AI classifications, edit themes, and approve entries.
              </TooltipContent>
            </Tooltip>
            <Tooltip>
              <TooltipTrigger asChild>
                <TabsTrigger
                  value="export"
                  className="relative rounded-none border-b-2 border-transparent px-4 py-2.5 text-sm font-medium text-muted-foreground transition-colors data-[state=active]:border-[#0D7377] data-[state=active]:text-[#0D7377] data-[state=active]:shadow-none data-[state=active]:bg-transparent hover:text-foreground"
                >
                  <Download className="mr-1.5 h-3.5 w-3.5" />
                  Export
                </TabsTrigger>
              </TooltipTrigger>
              <TooltipContent side="bottom" className="max-w-[280px] text-xs">
                Download reports in DOCX, Excel, HTML, or PDF. Create password-protected share links.
              </TooltipContent>
            </Tooltip>
          </TabsList>
        </TooltipProvider>

        <TabsContent value="overview" className="mt-6">
          <TabErrorBoundary>
            <OverviewTab components={components} />
          </TabErrorBoundary>
        </TabsContent>

        <TabsContent value="report" className="mt-6">
          <TabErrorBoundary>
            <ReportTab sehra={sehra} onRefresh={handleRefresh} />
          </TabErrorBoundary>
        </TabsContent>

        <TabsContent value="analysis" className="mt-6">
          <TabErrorBoundary>
            <AnalysisTab
              sehra={sehra}
              components={components}
              onRefresh={handleRefresh}
            />
          </TabErrorBoundary>
        </TabsContent>

        <TabsContent value="export" className="mt-6">
          <TabErrorBoundary>
            <ExportTab sehraId={sehraId} country={sehra.country} />
          </TabErrorBoundary>
        </TabsContent>
      </Tabs>
    </div>
  );
}
