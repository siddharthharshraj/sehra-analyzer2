"use client";

import { useState } from "react";
import useSWR from "swr";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import { InfoTooltip } from "@/components/ui/info-tooltip";
import { apiGet } from "@/lib/api-client";
import { COMPONENT_LABELS } from "@/lib/constants";
import { CodebookTable } from "@/components/admin/codebook-table";
import { AddQuestionForm } from "@/components/admin/add-question-form";
import type { CodebookItem } from "@/lib/types";
import type { ComponentName } from "@/lib/constants";

export default function AdminPage() {
  const { data: sections, isLoading } = useSWR<string[]>(
    "/codebook/sections",
    (url: string) => apiGet<string[]>(url),
  );

  const [selectedSection, setSelectedSection] = useState<string>("");

  const activeSection = selectedSection || sections?.[0] || "";

  const {
    data: items,
    isLoading: itemsLoading,
    mutate: mutateItems,
  } = useSWR<CodebookItem[]>(
    activeSection ? `/codebook/items?section=${activeSection}` : null,
    (url: string) => apiGet<CodebookItem[]>(url),
  );

  if (isLoading) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-10 w-64" />
        <Skeleton className="h-64" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <div className="flex items-center gap-1 mb-3">
          <h2 className="text-lg font-semibold">Manage Questions</h2>
          <InfoTooltip
            text="The codebook defines how each SEHRA question is scored. Enabler=1, Barrier=0. Reverse-scored items flip this. Changes affect future analyses only."
            side="right"
            maxWidth="max-w-[320px]"
          />
        </div>
      </div>
      <div className="flex items-center gap-2">
        <Select
          value={activeSection}
          onValueChange={(v) => setSelectedSection(v)}
        >
          <SelectTrigger className="w-[300px]">
            <SelectValue placeholder="Select section" />
          </SelectTrigger>
        <SelectContent>
          {(sections || []).map((s) => (
            <SelectItem key={s} value={s}>
              {COMPONENT_LABELS[s as ComponentName] || s}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
      <InfoTooltip
        text="Select a SEHRA component to view its questions and scoring rules."
        side="right"
      />
      </div>

      {activeSection && (
        <>
          <Card>
            <CardHeader>
              <CardTitle className="text-sm font-medium capitalize">
                {COMPONENT_LABELS[activeSection as ComponentName] ||
                  activeSection.replace(/_/g, " ")}
              </CardTitle>
            </CardHeader>
            <CardContent>
              {itemsLoading ? (
                <Skeleton className="h-32" />
              ) : (
                <CodebookTable
                  items={items || []}
                  onRefresh={() => mutateItems()}
                />
              )}
            </CardContent>
          </Card>

          <AddQuestionForm
            section={activeSection}
            onAdded={() => mutateItems()}
          />
        </>
      )}
    </div>
  );
}
