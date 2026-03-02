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
