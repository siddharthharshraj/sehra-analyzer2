"use client";

import Link from "next/link";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { Globe, Calendar } from "lucide-react";
import { STATUS_COLORS, TEAL } from "@/lib/constants";
import type { SEHRASummary } from "@/lib/types";

const STATUS_HELP: Record<string, string> = {
  draft: "Analysis complete, pending human review",
  reviewed: "Reviewed by analyst, ready to publish",
  published: "Final \u2014 shared with stakeholders",
};

interface AssessmentCardProps {
  sehra: SEHRASummary;
  enablerRate?: number;
}

function getRelativeTime(dateStr: string): string {
  const now = Date.now();
  const then = new Date(dateStr).getTime();
  const diffMs = now - then;
  const diffSec = Math.floor(diffMs / 1000);
  const diffMin = Math.floor(diffSec / 60);
  const diffHour = Math.floor(diffMin / 60);
  const diffDay = Math.floor(diffHour / 24);

  if (diffDay > 30) {
    return new Date(dateStr).toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
    });
  }
  if (diffDay > 0) return `${diffDay}d ago`;
  if (diffHour > 0) return `${diffHour}h ago`;
  if (diffMin > 0) return `${diffMin}m ago`;
  return "Just now";
}

// Simple country name to flag emoji mapping
function getCountryFlag(country: string): string {
  const flags: Record<string, string> = {
    liberia: "\uD83C\uDDF1\uD83C\uDDF7",
    kenya: "\uD83C\uDDF0\uD83C\uDDEA",
    nigeria: "\uD83C\uDDF3\uD83C\uDDEC",
    ghana: "\uD83C\uDDEC\uD83C\uDDED",
    india: "\uD83C\uDDEE\uD83C\uDDF3",
    ethiopia: "\uD83C\uDDEA\uD83C\uDDF9",
    tanzania: "\uD83C\uDDF9\uD83C\uDDFF",
    uganda: "\uD83C\uDDFA\uD83C\uDDEC",
    bangladesh: "\uD83C\uDDE7\uD83C\uDDE9",
    nepal: "\uD83C\uDDF3\uD83C\uDDF5",
    rwanda: "\uD83C\uDDF7\uD83C\uDDFC",
    mozambique: "\uD83C\uDDF2\uD83C\uDDFF",
    zambia: "\uD83C\uDDFF\uD83C\uDDF2",
    malawi: "\uD83C\uDDF2\uD83C\uDDFC",
    cameroon: "\uD83C\uDDE8\uD83C\uDDF2",
    senegal: "\uD83C\uDDF8\uD83C\uDDF3",
    "south africa": "\uD83C\uDDFF\uD83C\uDDE6",
    zimbabwe: "\uD83C\uDDFF\uD83C\uDDFC",
    pakistan: "\uD83C\uDDF5\uD83C\uDDF0",
    cambodia: "\uD83C\uDDF0\uD83C\uDDED",
    myanmar: "\uD83C\uDDF2\uD83C\uDDF2",
    madagascar: "\uD83C\uDDF2\uD83C\uDDEC",
    "sierra leone": "\uD83C\uDDF8\uD83C\uDDF1",
  };
  return flags[country.toLowerCase()] || "";
}

export function AssessmentCard({ sehra, enablerRate }: AssessmentCardProps) {
  const displayDate = sehra.assessment_date || sehra.upload_date;
  const relativeTime = displayDate ? getRelativeTime(displayDate) : null;
  const rate = enablerRate ?? 0;
  const flag = getCountryFlag(sehra.country);

  return (
    <Link href={`/assessments/${sehra.id}`} className="group block">
      <Card className="h-full shadow-card card-hover overflow-hidden rounded-xl border border-gray-100">
        <CardContent className="pt-5 pb-4 px-5 flex flex-col gap-3">
          {/* Country + flag */}
          <div className="flex items-start justify-between">
            <div className="flex items-center gap-2">
              {flag ? (
                <span className="text-xl leading-none">{flag}</span>
              ) : (
                <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-[#0D7377]/10">
                  <Globe className="h-4 w-4 text-[#0D7377]" />
                </div>
              )}
              <div>
                <h3 className="font-semibold text-foreground leading-tight">
                  {sehra.country}
                </h3>
                {sehra.district && (
                  <p className="text-xs text-muted-foreground">
                    {sehra.district}
                    {sehra.province ? `, ${sehra.province}` : ""}
                  </p>
                )}
              </div>
            </div>
            <TooltipProvider delayDuration={200}>
              <Tooltip>
                <TooltipTrigger asChild>
                  <Badge
                    className={`text-[10px] px-2 py-0.5 cursor-help ${STATUS_COLORS[sehra.status] || ""}`}
                  >
                    {sehra.status}
                  </Badge>
                </TooltipTrigger>
                <TooltipContent side="left" className="max-w-[220px] text-xs">
                  {STATUS_HELP[sehra.status] || `Status: ${sehra.status}`}
                </TooltipContent>
              </Tooltip>
            </TooltipProvider>
          </div>

          {/* Date */}
          {relativeTime && (
            <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
              <Calendar className="h-3 w-3" />
              {relativeTime}
            </div>
          )}

          {/* Readiness bar */}
          <div className="space-y-1.5">
            <div className="flex items-center justify-between text-xs">
              <span className="text-muted-foreground">Readiness</span>
              <span className="font-semibold" style={{ color: TEAL }}>
                {rate}%
              </span>
            </div>
            <div className="h-2 w-full rounded-full bg-gray-100 overflow-hidden">
              <div
                className="h-full rounded-full transition-all duration-500"
                style={{
                  width: `${rate}%`,
                  background: `linear-gradient(90deg, #0D7377, #14967E)`,
                }}
              />
            </div>
          </div>
        </CardContent>
      </Card>
    </Link>
  );
}
