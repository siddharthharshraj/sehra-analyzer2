"use client";

import Link from "next/link";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { STATUS_COLORS, TEAL } from "@/lib/constants";
import type { SEHRASummary } from "@/lib/types";

interface AssessmentCardProps {
  sehra: SEHRASummary;
  enablerRate?: number;
}

export function AssessmentCard({ sehra, enablerRate }: AssessmentCardProps) {
  const displayDate = sehra.assessment_date || sehra.upload_date;
  const formattedDate = displayDate
    ? new Date(displayDate).toLocaleDateString("en-US", {
        month: "short",
        day: "numeric",
        year: "numeric",
      })
    : null;

  const rate = enablerRate ?? 0;

  return (
    <Link href={`/assessments/${sehra.id}`}>
      <Card className="transition-colors hover:bg-muted/50 cursor-pointer h-full">
        <CardContent className="pt-6 flex flex-col gap-3">
          <div>
            <h3 className="font-semibold">{sehra.country}</h3>
            {sehra.district && (
              <p className="text-sm text-muted-foreground">{sehra.district}</p>
            )}
          </div>

          {formattedDate && (
            <p className="text-xs text-muted-foreground">{formattedDate}</p>
          )}

          {/* Enabler rate bar */}
          <div className="space-y-1">
            <div className="h-2 w-full rounded-full bg-muted overflow-hidden">
              <div
                className="h-full rounded-full transition-all"
                style={{ width: `${rate}%`, backgroundColor: TEAL }}
              />
            </div>
            <p className="text-xs text-muted-foreground">
              {rate}% readiness
            </p>
          </div>

          <Badge className={`w-fit ${STATUS_COLORS[sehra.status] || ""}`}>
            {sehra.status}
          </Badge>
        </CardContent>
      </Card>
    </Link>
  );
}
