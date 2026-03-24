"use client";

import { useState } from "react";
import { toast } from "sonner";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { CheckCircle2, ArrowRight, RotateCcw, HelpCircle } from "lucide-react";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { apiPost, apiPatch } from "@/lib/api-client";
import { STATUS_COLORS } from "@/lib/constants";
import type { SEHRADetail, BatchApproveResponse } from "@/lib/types";

interface ReviewControlsProps {
  sehra: SEHRADetail;
  onRefresh: () => void;
}

export function ReviewControls({ sehra, onRefresh }: ReviewControlsProps) {
  const [threshold, setThreshold] = useState("0.8");
  const [loading, setLoading] = useState(false);

  async function handleBatchApprove() {
    setLoading(true);
    try {
      const res = await apiPost<BatchApproveResponse>(
        `/sehras/${sehra.id}/batch-approve`,
        { confidence_threshold: parseFloat(threshold) },
      );
      toast.success(`Approved ${res.approved_count} entries`);
      onRefresh();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Failed to approve");
    } finally {
      setLoading(false);
    }
  }

  async function handleStatusChange(status: string) {
    try {
      await apiPatch(`/sehras/${sehra.id}/status`, { status });
      toast.success(`Status updated to ${status}`);
      onRefresh();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Failed to update");
    }
  }

  return (
    <Card className="shadow-card rounded-xl border-gray-100">
      <CardHeader>
        <CardTitle className="flex items-center justify-between text-sm font-medium">
          <span>Review Controls</span>
          <Badge className={STATUS_COLORS[sehra.status] || ""}>
            {sehra.status}
          </Badge>
        </CardTitle>
        <p className="text-xs text-muted-foreground mt-1">
          Review AI classifications, approve entries, and update the assessment
          status. Workflow: Draft &rarr; Reviewed &rarr; Published.
        </p>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Batch approve */}
        <div className="rounded-xl border border-gray-100 bg-gray-50/50 p-4">
          <div className="flex items-center gap-1.5 mb-3">
            <p className="text-xs text-muted-foreground">
              Auto-approve AI classifications with confidence above the threshold
            </p>
            <Tooltip>
              <TooltipTrigger asChild>
                <HelpCircle className="h-3.5 w-3.5 text-muted-foreground cursor-help shrink-0" />
              </TooltipTrigger>
              <TooltipContent side="bottom" className="max-w-[280px] text-sm">
                <p>Approve all AI classifications above the confidence threshold at once. This marks them as human-verified.</p>
              </TooltipContent>
            </Tooltip>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-sm whitespace-nowrap">
              Approve entries above
            </span>
            <Tooltip>
              <TooltipTrigger asChild>
                <Input
                  type="number"
                  min="0"
                  max="1"
                  step="0.05"
                  value={threshold}
                  onChange={(e) => setThreshold(e.target.value)}
                  className="w-20 rounded-lg"
                />
              </TooltipTrigger>
              <TooltipContent side="bottom" className="max-w-[280px] text-sm">
                <p>Set the minimum confidence level. Only entries above this threshold will be approved. We recommend 0.8 (80%) or higher.</p>
              </TooltipContent>
            </Tooltip>
            <Button
              onClick={handleBatchApprove}
              disabled={loading}
              size="sm"
              variant="outline"
              className="gap-1.5 rounded-lg"
            >
              <CheckCircle2 className="h-3.5 w-3.5" />
              Apply
            </Button>
          </div>
        </div>

        {/* Status buttons */}
        <div className="flex items-center gap-1.5 mb-1">
          <span className="text-xs text-muted-foreground font-medium">Status Workflow</span>
          <Tooltip>
            <TooltipTrigger asChild>
              <HelpCircle className="h-3.5 w-3.5 text-muted-foreground cursor-help" />
            </TooltipTrigger>
            <TooltipContent side="bottom" className="max-w-[280px] text-sm">
              <p>Draft = initial AI analysis. Reviewed = analyst has verified. Published = ready for stakeholders.</p>
            </TooltipContent>
          </Tooltip>
        </div>
        <div className="flex flex-wrap gap-2">
          {sehra.status === "draft" && (
            <Button
              onClick={() => handleStatusChange("reviewed")}
              size="sm"
              className="gap-1.5 rounded-lg bg-blue-600 hover:bg-blue-700"
            >
              <ArrowRight className="h-3.5 w-3.5" />
              Mark Reviewed
            </Button>
          )}
          {(sehra.status === "draft" || sehra.status === "reviewed") && (
            <Button
              onClick={() => handleStatusChange("published")}
              size="sm"
              className="gap-1.5 rounded-lg bg-green-600 hover:bg-green-700"
            >
              <CheckCircle2 className="h-3.5 w-3.5" />
              Publish
            </Button>
          )}
          {sehra.status !== "draft" && (
            <Button
              onClick={() => handleStatusChange("draft")}
              size="sm"
              variant="outline"
              className="gap-1.5 rounded-lg"
            >
              <RotateCcw className="h-3.5 w-3.5" />
              Revert to Draft
            </Button>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
