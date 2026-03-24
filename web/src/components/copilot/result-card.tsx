"use client";

import {
  CheckCircle2,
  Pencil,
  ListChecks,
  FileText,
  ArrowRight,
  RotateCcw,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import type { ToolResultCard, CopilotAction } from "@/lib/types";

const TOOL_STYLES: Record<string, {
  label: string;
  borderColor: string;
  bgColor: string;
  badgeColor: string;
  iconColor: string;
  Icon: typeof Pencil;
}> = {
  edit_entry: {
    label: "Entry Updated",
    borderColor: "border-emerald-200 dark:border-emerald-800",
    bgColor: "bg-emerald-50/50 dark:bg-emerald-950/20",
    badgeColor: "bg-emerald-100 text-emerald-700 dark:bg-emerald-900 dark:text-emerald-300",
    iconColor: "text-emerald-600 dark:text-emerald-400",
    Icon: Pencil,
  },
  change_status: {
    label: "Status Changed",
    borderColor: "border-blue-200 dark:border-blue-800",
    bgColor: "bg-blue-50/50 dark:bg-blue-950/20",
    badgeColor: "bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300",
    iconColor: "text-blue-600 dark:text-blue-400",
    Icon: CheckCircle2,
  },
  batch_approve: {
    label: "Batch Approved",
    borderColor: "border-teal-200 dark:border-teal-800",
    bgColor: "bg-teal-50/50 dark:bg-teal-950/20",
    badgeColor: "bg-teal-100 text-teal-700 dark:bg-teal-900 dark:text-teal-300",
    iconColor: "text-teal-600 dark:text-teal-400",
    Icon: ListChecks,
  },
  edit_executive_summary: {
    label: "Summary Updated",
    borderColor: "border-purple-200 dark:border-purple-800",
    bgColor: "bg-purple-50/50 dark:bg-purple-950/20",
    badgeColor: "bg-purple-100 text-purple-700 dark:bg-purple-900 dark:text-purple-300",
    iconColor: "text-purple-600 dark:text-purple-400",
    Icon: FileText,
  },
};

interface ResultCardProps {
  result: ToolResultCard;
  onExecuteAction?: (action: CopilotAction) => void;
}

export function ResultCard({ result, onExecuteAction }: ResultCardProps) {
  const style = TOOL_STYLES[result.tool] || {
    label: result.summary,
    borderColor: "border-gray-200 dark:border-gray-700",
    bgColor: "bg-gray-50/50 dark:bg-gray-900/20",
    badgeColor: "bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300",
    iconColor: "text-gray-600 dark:text-gray-400",
    Icon: CheckCircle2,
  };

  const { borderColor, bgColor, badgeColor, iconColor, Icon } = style;

  return (
    <div className={`rounded-lg border ${borderColor} ${bgColor} overflow-hidden animate-in fade-in slide-in-from-bottom-2 duration-300`}>
      {/* Header */}
      <div className="flex items-center gap-2 px-3 py-2 border-b border-inherit">
        <div className={`flex items-center justify-center ${iconColor}`}>
          {result.success ? (
            <CheckCircle2 className="h-4 w-4" />
          ) : (
            <Icon className="h-4 w-4" />
          )}
        </div>
        <span className="text-sm font-medium flex-1">{result.summary}</span>
        <Badge className={`text-[10px] ${badgeColor} border-0`}>
          {result.tool.replace(/_/g, " ")}
        </Badge>
      </div>

      {/* Details */}
      {result.details && Object.keys(result.details).length > 0 && (
        <div className="px-3 py-2 space-y-1">
          {Object.entries(result.details).map(([key, value]) => (
            <div key={key} className="flex items-center gap-2 text-xs">
              <span className="text-muted-foreground min-w-[90px] font-medium">{key}</span>
              <ArrowRight className="h-2.5 w-2.5 text-muted-foreground/50 shrink-0" />
              <span className="font-medium truncate">{value}</span>
            </div>
          ))}
        </div>
      )}

      {/* Actions */}
      {result.undoAction && onExecuteAction && (
        <div className="flex items-center gap-2 px-3 py-2 border-t border-inherit">
          <Button
            variant="ghost"
            size="sm"
            className="h-7 text-xs gap-1.5 text-muted-foreground hover:text-foreground"
            onClick={() => onExecuteAction(result.undoAction!)}
          >
            <RotateCcw className="h-3 w-3" />
            Undo
          </Button>
        </div>
      )}
    </div>
  );
}
