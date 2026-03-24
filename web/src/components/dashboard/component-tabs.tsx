"use client";

import { useState, useMemo } from "react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import {
  ChevronDown,
  ChevronUp,
  Search,
  ArrowUpDown,
  ArrowUp,
  ArrowDown,
  Inbox,
  HelpCircle,
} from "lucide-react";
import { COMPONENT_LABELS, TEAL, RED } from "@/lib/constants";
import { EditClassification } from "./edit-classification";
import type { ComponentAnalysis, QualitativeEntry } from "@/lib/types";
import type { ComponentName } from "@/lib/constants";

interface ComponentTabsProps {
  components: ComponentAnalysis[];
  onRefresh: () => void;
}

const CLASSIFICATION_COLORS: Record<string, string> = {
  enabler: "bg-[#0D7377]/10 text-[#0D7377] border-[#0D7377]/20",
  barrier: "bg-[#CC3333]/10 text-[#CC3333] border-[#CC3333]/20",
  strength: "bg-blue-50 text-blue-700 border-blue-200",
  weakness: "bg-amber-50 text-amber-700 border-amber-200",
  neutral: "bg-gray-50 text-gray-600 border-gray-200",
};

type SortDirection = "none" | "high" | "low";

function ConfidenceBar({ value }: { value: number }) {
  const pct = Math.round(value * 100);
  let color = "bg-green-500";
  if (value < 0.5) color = "bg-red-500";
  else if (value < 0.8) color = "bg-amber-500";

  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <div className="flex items-center gap-2 min-w-[80px] cursor-help">
          <div className="h-1.5 flex-1 rounded-full bg-gray-100 overflow-hidden">
            <div
              className={`h-full rounded-full transition-all ${color}`}
              style={{ width: `${pct}%` }}
            />
          </div>
          <span className="text-xs text-muted-foreground tabular-nums w-8 text-right">
            {pct}%
          </span>
        </div>
      </TooltipTrigger>
      <TooltipContent side="bottom" className="max-w-[280px] text-sm">
        <p>AI confidence: Green (&gt;80%) = high certainty, Yellow (50-80%) = review recommended, Red (&lt;50%) = needs human verification.</p>
      </TooltipContent>
    </Tooltip>
  );
}

function RemarkCell({ text }: { text: string }) {
  const [expanded, setExpanded] = useState(false);
  const isLong = text.length > 120;

  if (!isLong) {
    return <span className="text-sm text-foreground/80">{text}</span>;
  }

  return (
    <div>
      <span className="text-sm text-foreground/80">
        {expanded ? text : `${text.slice(0, 120)}...`}
      </span>
      <Button
        variant="link"
        size="sm"
        onClick={() => setExpanded(!expanded)}
        className="ml-1 h-auto p-0 text-xs text-[#0D7377]"
      >
        {expanded ? (
          <>
            Less <ChevronUp className="ml-0.5 h-3 w-3" />
          </>
        ) : (
          <>
            More <ChevronDown className="ml-0.5 h-3 w-3" />
          </>
        )}
      </Button>
    </div>
  );
}

function ClassificationBadge({ classification }: { classification: string }) {
  const colors =
    CLASSIFICATION_COLORS[classification] || CLASSIFICATION_COLORS.neutral;
  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <span
          className={`inline-flex items-center rounded-full border px-2 py-0.5 text-[11px] font-medium capitalize cursor-help ${colors}`}
        >
          {classification}
        </span>
      </TooltipTrigger>
      <TooltipContent side="bottom" className="max-w-[280px] text-sm">
        <p>enabler = supports eye health, barrier = hinders eye health, strength = existing capability, weakness = gap to address.</p>
      </TooltipContent>
    </Tooltip>
  );
}

function EmptyEntries() {
  return (
    <div className="flex flex-col items-center justify-center py-12 text-center">
      <div className="mx-auto mb-3 flex h-10 w-10 items-center justify-center rounded-xl bg-gray-100">
        <Inbox className="h-5 w-5 text-muted-foreground" />
      </div>
      <p className="text-sm font-medium text-muted-foreground">
        No entries classified yet
      </p>
      <p className="mt-1 text-xs text-muted-foreground/70 max-w-xs">
        Qualitative entries will appear here once the assessment data has been
        processed and classified.
      </p>
    </div>
  );
}

function QualitativeSection({
  entries,
  onRefresh,
}: {
  entries: QualitativeEntry[];
  onRefresh: () => void;
}) {
  const [searchQuery, setSearchQuery] = useState("");
  const [sortDir, setSortDir] = useState<SortDirection>("none");

  const filteredAndSorted = useMemo(() => {
    let result = entries;

    // Filter by search
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      result = result.filter(
        (e) =>
          e.remark_text.toLowerCase().includes(q) ||
          e.theme.toLowerCase().includes(q) ||
          e.classification.toLowerCase().includes(q),
      );
    }

    // Sort by confidence
    if (sortDir !== "none") {
      result = [...result].sort((a, b) =>
        sortDir === "high"
          ? b.confidence - a.confidence
          : a.confidence - b.confidence,
      );
    }

    return result;
  }, [entries, searchQuery, sortDir]);

  const cycleSortDir = () => {
    setSortDir((prev) => {
      if (prev === "none") return "high";
      if (prev === "high") return "low";
      return "none";
    });
  };

  const SortIcon =
    sortDir === "high" ? ArrowDown : sortDir === "low" ? ArrowUp : ArrowUpDown;

  if (entries.length === 0) {
    return <EmptyEntries />;
  }

  return (
    <div className="mb-4">
      <div className="flex items-center justify-between mb-3">
        <div>
          <h4 className="text-sm font-medium">Qualitative Entries</h4>
          <p className="text-xs text-muted-foreground">
            {filteredAndSorted.length} of {entries.length} entries
            {searchQuery ? " matching filter" : ""}. Click theme or
            classification to edit.
          </p>
        </div>
      </div>

      {/* Search + Sort controls */}
      <div className="flex items-center gap-2 mb-3">
        <div className="relative flex-1 max-w-xs">
          <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-muted-foreground" />
          <Tooltip>
            <TooltipTrigger asChild>
              <Input
                placeholder="Filter entries..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-8 h-8 text-sm rounded-lg"
              />
            </TooltipTrigger>
            <TooltipContent side="bottom" className="max-w-[280px] text-sm">
              <p>Filter entries by remark text, theme name, or classification type.</p>
            </TooltipContent>
          </Tooltip>
        </div>
        <Tooltip>
          <TooltipTrigger asChild>
            <Button
              variant="outline"
              size="sm"
              onClick={cycleSortDir}
              className={`h-8 gap-1.5 rounded-lg text-xs ${sortDir !== "none" ? "border-[#0D7377] text-[#0D7377]" : ""}`}
            >
              <SortIcon className="h-3.5 w-3.5" />
              Confidence{sortDir === "high" ? " (High)" : sortDir === "low" ? " (Low)" : ""}
            </Button>
          </TooltipTrigger>
          <TooltipContent side="bottom" className="max-w-[280px] text-sm">
            <p>Sort entries by AI confidence score. Higher confidence means the AI is more certain about the classification.</p>
          </TooltipContent>
        </Tooltip>
      </div>

      {filteredAndSorted.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-8 text-center rounded-xl border border-dashed border-gray-200">
          <Search className="h-5 w-5 text-muted-foreground mb-2" />
          <p className="text-sm text-muted-foreground">
            No entries match &ldquo;{searchQuery}&rdquo;
          </p>
        </div>
      ) : (
        <div className="overflow-hidden rounded-xl border">
          <Table>
            <TableHeader>
              <TableRow className="bg-gray-50/80">
                <TableHead className="w-[40%] text-xs font-medium">
                  Remark
                </TableHead>
                <TableHead className="text-xs font-medium">
                  <span className="inline-flex items-center gap-1">
                    Theme
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <HelpCircle className="h-3 w-3 text-muted-foreground/50 cursor-help" />
                      </TooltipTrigger>
                      <TooltipContent side="bottom" className="max-w-[280px] text-sm">
                        <p>Click on a theme value to edit the AI's classification. Your corrections help improve future analyses.</p>
                      </TooltipContent>
                    </Tooltip>
                  </span>
                </TableHead>
                <TableHead className="text-xs font-medium">
                  <span className="inline-flex items-center gap-1">
                    Classification
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <HelpCircle className="h-3 w-3 text-muted-foreground/50 cursor-help" />
                      </TooltipTrigger>
                      <TooltipContent side="bottom" className="max-w-[280px] text-sm">
                        <p>Click on a classification to change it. enabler = supports eye health, barrier = hinders eye health, strength = existing capability, weakness = gap to address.</p>
                      </TooltipContent>
                    </Tooltip>
                  </span>
                </TableHead>
                <TableHead className="text-xs font-medium">
                  Confidence
                </TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredAndSorted.map(
                (entry: QualitativeEntry, idx: number) => (
                  <TableRow
                    key={entry.id}
                    className={`transition-colors hover:bg-gray-50 ${idx % 2 === 1 ? "bg-gray-50/40" : ""}`}
                  >
                    <TableCell>
                      <RemarkCell text={entry.remark_text} />
                    </TableCell>
                    <TableCell>
                      <EditClassification
                        entry={entry}
                        field="theme"
                        onSave={onRefresh}
                      />
                    </TableCell>
                    <TableCell>
                      <EditClassification
                        entry={entry}
                        field="classification"
                        onSave={onRefresh}
                      />
                    </TableCell>
                    <TableCell>
                      <ConfidenceBar value={entry.confidence} />
                    </TableCell>
                  </TableRow>
                ),
              )}
            </TableBody>
          </Table>
        </div>
      )}
    </div>
  );
}

export function ComponentTabs({ components, onRefresh }: ComponentTabsProps) {
  if (components.length === 0) {
    return (
      <Card className="shadow-card rounded-xl border-gray-100">
        <CardContent className="py-0">
          <EmptyEntries />
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="shadow-card rounded-xl border-gray-100">
      <CardHeader>
        <CardTitle className="text-sm font-medium">
          Component Analysis
        </CardTitle>
        <p className="text-xs text-muted-foreground mt-1">
          Detailed breakdown by area. Click a tab to see individual findings.
          You can edit classifications by clicking on the theme or
          classification badges.
        </p>
      </CardHeader>
      <CardContent>
        <Tabs defaultValue={components[0]?.component}>
          <TabsList className="flex-wrap h-auto gap-1 bg-gray-50 rounded-lg p-1">
            {components.map((c) => (
              <TabsTrigger
                key={c.component}
                value={c.component}
                className="text-xs rounded-md data-[state=active]:bg-white data-[state=active]:shadow-sm"
              >
                {COMPONENT_LABELS[c.component as ComponentName] ||
                  c.component}
              </TabsTrigger>
            ))}
          </TabsList>

          {components.map((comp) => {
            const enablerSummary = comp.report_sections["enabler_summary"];
            const barrierSummary = comp.report_sections["barrier_summary"];
            const actionPoints = comp.report_sections["action_points"];
            const otherSections = Object.entries(
              comp.report_sections,
            ).filter(
              ([key]) =>
                !["enabler_summary", "barrier_summary", "action_points"].includes(key),
            );

            return (
              <TabsContent key={comp.component} value={comp.component}>
                {/* Metrics */}
                <div className="mb-4 flex gap-4">
                  <div className="flex items-center gap-2 rounded-lg bg-[#0D7377]/5 px-3 py-1.5">
                    <div
                      className="h-2.5 w-2.5 rounded-full"
                      style={{ backgroundColor: TEAL }}
                    />
                    <span className="text-sm font-medium text-[#0D7377]">
                      {comp.enabler_count} Enablers
                    </span>
                  </div>
                  <div className="flex items-center gap-2 rounded-lg bg-[#CC3333]/5 px-3 py-1.5">
                    <div
                      className="h-2.5 w-2.5 rounded-full"
                      style={{ backgroundColor: RED }}
                    />
                    <span className="text-sm font-medium text-[#CC3333]">
                      {comp.barrier_count} Barriers
                    </span>
                  </div>
                </div>

                {/* Summary cards */}
                <div className="mb-6 grid gap-4 sm:grid-cols-2">
                  {enablerSummary?.content && (
                    <div className="rounded-xl border-l-4 border-[#0D7377] bg-[#0D7377]/5 p-4">
                      <h4 className="mb-2 text-sm font-semibold text-[#0D7377]">
                        Enabler Summary
                      </h4>
                      <p className="whitespace-pre-wrap text-sm leading-relaxed text-foreground/80">
                        {enablerSummary.content}
                      </p>
                    </div>
                  )}

                  {barrierSummary?.content && (
                    <div className="rounded-xl border-l-4 border-[#CC3333] bg-[#CC3333]/5 p-4">
                      <h4 className="mb-2 text-sm font-semibold text-[#CC3333]">
                        Barrier Summary
                      </h4>
                      <p className="whitespace-pre-wrap text-sm leading-relaxed text-foreground/80">
                        {barrierSummary.content}
                      </p>
                    </div>
                  )}
                </div>

                {actionPoints?.content && (
                  <div className="mb-6 rounded-xl border bg-muted/30 p-4">
                    <h4 className="mb-2 text-sm font-semibold">
                      Action Points
                    </h4>
                    <ul className="list-disc space-y-1 pl-5 text-sm leading-relaxed text-foreground/80">
                      {actionPoints.content
                        .split(/\n/)
                        .map((line) => line.replace(/^[-\u2022*]\s*/, "").trim())
                        .filter(Boolean)
                        .map((point, i) => (
                          <li key={i}>{point}</li>
                        ))}
                    </ul>
                  </div>
                )}

                {/* Other report sections */}
                {otherSections.map(([key, section]) => (
                  <div key={key} className="mb-4">
                    <h4 className="mb-1 text-sm font-medium capitalize">
                      {key.replace(/_/g, " ")}
                    </h4>
                    <p className="whitespace-pre-wrap text-sm text-muted-foreground">
                      {section.content}
                    </p>
                  </div>
                ))}

                {/* Qualitative entries with search + sort */}
                <QualitativeSection
                  entries={comp.qualitative_entries}
                  onRefresh={onRefresh}
                />
              </TabsContent>
            );
          })}
        </Tabs>
      </CardContent>
    </Card>
  );
}
