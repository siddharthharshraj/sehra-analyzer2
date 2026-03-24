"use client";

import { useState } from "react";
import {
  ChevronDown,
  ChevronRight,
  Wrench,
  Loader2,
  CheckCircle2,
  Pencil,
  FileText,
  FileSearch,
  Eye,
  Database,
  Zap,
} from "lucide-react";
import { cn } from "@/lib/utils";
import type { CopilotToolCall } from "@/lib/types";

const TOOL_ICONS: Record<string, typeof Wrench> = {
  edit_entry: Pencil,
  change_status: CheckCircle2,
  batch_approve: Zap,
  edit_executive_summary: FileText,
  search_entries: FileSearch,
  get_assessment: Eye,
  list_assessments: Database,
};

export function ToolCallsTimeline({ toolCalls }: { toolCalls: CopilotToolCall[] }) {
  const [expanded, setExpanded] = useState(false);
  if (!toolCalls.length) return null;

  const allDone = toolCalls.every((tc) => tc.status === "done");

  return (
    <div className="my-1.5">
      <button
        onClick={() => setExpanded(!expanded)}
        className="flex items-center gap-1.5 text-xs text-muted-foreground hover:text-foreground transition-colors"
      >
        {expanded ? <ChevronDown className="h-3 w-3" /> : <ChevronRight className="h-3 w-3" />}
        <Wrench className="h-3 w-3" />
        <span>
          {toolCalls.length} tool{toolCalls.length !== 1 ? "s" : ""} used
        </span>
        {!allDone && <Loader2 className="h-3 w-3 animate-spin" />}
      </button>
      {expanded && (
        <div className="mt-2 ml-2 border-l-2 border-muted pl-3 space-y-2">
          {toolCalls.map((tc, i) => {
            const ToolIcon = TOOL_ICONS[tc.tool] || Wrench;
            return (
              <div key={i} className="flex items-start gap-2 text-xs relative">
                <div className={cn(
                  "absolute -left-[17px] top-0.5 h-2.5 w-2.5 rounded-full border-2 border-background",
                  tc.status === "running" ? "bg-blue-500 animate-pulse" :
                  tc.status === "error" ? "bg-red-500" : "bg-emerald-500",
                )} />
                <div className={cn(
                  "flex items-center justify-center h-5 w-5 rounded shrink-0",
                  tc.status === "running" ? "bg-blue-50 text-blue-600 dark:bg-blue-950 dark:text-blue-400" :
                  tc.status === "error" ? "bg-red-50 text-red-600 dark:bg-red-950 dark:text-red-400" :
                  "bg-emerald-50 text-emerald-600 dark:bg-emerald-950 dark:text-emerald-400",
                )}>
                  {tc.status === "running" ? (
                    <Loader2 className="h-3 w-3 animate-spin" />
                  ) : (
                    <ToolIcon className="h-3 w-3" />
                  )}
                </div>
                <div className="min-w-0 flex-1">
                  <span className="font-mono font-medium text-foreground">{tc.tool}</span>
                  {Object.keys(tc.arguments).length > 0 && (
                    <p className="text-muted-foreground truncate mt-0.5">
                      {Object.entries(tc.arguments)
                        .map(([k, v]) => `${k}=${JSON.stringify(v)}`)
                        .join(", ")
                        .slice(0, 60)}
                    </p>
                  )}
                  {tc.result_preview && (
                    <p className="text-muted-foreground/70 italic truncate mt-0.5">
                      {tc.result_preview.slice(0, 80)}
                    </p>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
