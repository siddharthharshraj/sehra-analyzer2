"use client";

import { useState } from "react";
import { toast } from "sonner";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
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
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center justify-between text-sm font-medium">
          Review Controls
          <Badge className={STATUS_COLORS[sehra.status] || ""}>
            {sehra.status}
          </Badge>
        </CardTitle>
        <p className="text-xs text-muted-foreground mt-1">
          Review AI classifications, approve entries, and update the assessment status. Workflow: Draft → Reviewed → Published.
        </p>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Batch approve */}
        <div>
          <p className="text-xs text-muted-foreground mb-2">
            Auto-approve AI classifications with confidence above the threshold (0.8 = 80% confident)
          </p>
          <div className="flex items-center gap-2">
            <span className="text-sm whitespace-nowrap">
              Approve entries above
            </span>
          <Input
            type="number"
            min="0"
            max="1"
            step="0.05"
            value={threshold}
            onChange={(e) => setThreshold(e.target.value)}
            className="w-20"
          />
          <Button
            onClick={handleBatchApprove}
            disabled={loading}
            size="sm"
            variant="outline"
          >
            Apply
          </Button>
          </div>
        </div>

        {/* Status buttons */}
        <div className="flex flex-wrap gap-2">
          {sehra.status === "draft" && (
            <Button
              onClick={() => handleStatusChange("reviewed")}
              size="sm"
              className="bg-blue-600 hover:bg-blue-700"
            >
              Mark Reviewed
            </Button>
          )}
          {(sehra.status === "draft" || sehra.status === "reviewed") && (
            <Button
              onClick={() => handleStatusChange("published")}
              size="sm"
              className="bg-green-600 hover:bg-green-700"
            >
              Publish
            </Button>
          )}
          {sehra.status !== "draft" && (
            <Button
              onClick={() => handleStatusChange("draft")}
              size="sm"
              variant="outline"
            >
              Revert to Draft
            </Button>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
