"use client";

import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { COMPONENT_LABELS, TEAL, RED } from "@/lib/constants";
import { EditClassification } from "./edit-classification";
import type { ComponentAnalysis } from "@/lib/types";
import type { ComponentName } from "@/lib/constants";

interface ComponentTabsProps {
  components: ComponentAnalysis[];
  onRefresh: () => void;
}

export function ComponentTabs({ components, onRefresh }: ComponentTabsProps) {
  if (components.length === 0) return null;

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-sm font-medium">
          Component Analysis
        </CardTitle>
        <p className="text-xs text-muted-foreground mt-1">
          Detailed breakdown by area. Click a tab to see individual findings. You can edit classifications by clicking on the theme or classification badges.
        </p>
      </CardHeader>
      <CardContent>
        <Tabs defaultValue={components[0]?.component}>
          <TabsList className="flex-wrap h-auto gap-1">
            {components.map((c) => (
              <TabsTrigger key={c.component} value={c.component} className="text-xs">
                {COMPONENT_LABELS[c.component as ComponentName] || c.component}
              </TabsTrigger>
            ))}
          </TabsList>

          {components.map((comp) => {
            const enablerSummary = comp.report_sections["enabler_summary"];
            const barrierSummary = comp.report_sections["barrier_summary"];
            const actionPoints = comp.report_sections["action_points"];
            const otherSections = Object.entries(comp.report_sections).filter(
              ([key]) => !["enabler_summary", "barrier_summary", "action_points"].includes(key),
            );

            return (
            <TabsContent key={comp.component} value={comp.component}>
              {/* Metrics */}
              <div className="mb-4 flex gap-4">
                <div className="flex items-center gap-2">
                  <div
                    className="h-3 w-3 rounded-full"
                    style={{ backgroundColor: TEAL }}
                  />
                  <span className="text-sm">
                    {comp.enabler_count} Enablers
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  <div
                    className="h-3 w-3 rounded-full"
                    style={{ backgroundColor: RED }}
                  />
                  <span className="text-sm">
                    {comp.barrier_count} Barriers
                  </span>
                </div>
              </div>

              {/* Summary cards — shown before the entries table */}
              <div className="mb-6 grid gap-4 sm:grid-cols-2">
                {enablerSummary?.content && (
                  <div className="rounded-lg border-l-4 border-[#0D7377] bg-[#0D7377]/5 p-4">
                    <h4 className="mb-2 text-sm font-semibold text-[#0D7377]">
                      Enabler Summary
                    </h4>
                    <p className="whitespace-pre-wrap text-sm leading-relaxed">
                      {enablerSummary.content}
                    </p>
                  </div>
                )}

                {barrierSummary?.content && (
                  <div className="rounded-lg border-l-4 border-[#CC3333] bg-[#CC3333]/5 p-4">
                    <h4 className="mb-2 text-sm font-semibold text-[#CC3333]">
                      Barrier Summary
                    </h4>
                    <p className="whitespace-pre-wrap text-sm leading-relaxed">
                      {barrierSummary.content}
                    </p>
                  </div>
                )}
              </div>

              {actionPoints?.content && (
                <div className="mb-6 rounded-lg border bg-muted/40 p-4">
                  <h4 className="mb-2 text-sm font-semibold">Action Points</h4>
                  <ul className="list-disc space-y-1 pl-5 text-sm leading-relaxed">
                    {actionPoints.content
                      .split(/\n/)
                      .map((line) => line.replace(/^[-•*]\s*/, "").trim())
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

              {/* Qualitative entries */}
              {comp.qualitative_entries.length > 0 && (
                <div className="mb-4">
                  <h4 className="mb-1 text-sm font-medium">
                    Qualitative Entries
                  </h4>
                  <p className="mb-2 text-xs text-muted-foreground">
                    Individual observations extracted from the assessment. Click theme or classification to edit.
                  </p>
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead className="w-[40%]">Remark</TableHead>
                        <TableHead>Theme</TableHead>
                        <TableHead>Classification</TableHead>
                        <TableHead>Confidence</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {comp.qualitative_entries.map((entry) => (
                        <TableRow key={entry.id}>
                          <TableCell className="text-sm">
                            {entry.remark_text}
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
                            <Badge
                              variant={
                                entry.confidence >= 0.8
                                  ? "default"
                                  : "secondary"
                              }
                            >
                              {Math.round(entry.confidence * 100)}%
                            </Badge>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>
              )}
            </TabsContent>
            );
          })}
        </Tabs>
      </CardContent>
    </Card>
  );
}
