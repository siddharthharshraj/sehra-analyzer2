"use client";

import { useState, useCallback } from "react";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { apiPatch } from "@/lib/api-client";
import { CLASSIFICATIONS, THEMES } from "@/lib/constants";
import type { QualitativeEntry } from "@/lib/types";

interface EditClassificationProps {
  entry: QualitativeEntry;
  field: "theme" | "classification";
  onSave: () => void;
}

export function EditClassification({
  entry,
  field,
  onSave,
}: EditClassificationProps) {
  const [value, setValue] = useState(
    field === "theme" ? entry.theme : entry.classification,
  );
  const options = field === "theme" ? THEMES : CLASSIFICATIONS;

  const handleChange = useCallback(
    async (newValue: string) => {
      setValue(newValue);
      try {
        await apiPatch(`/entries/${entry.id}`, { [field]: newValue });
        onSave();
      } catch {
        setValue(field === "theme" ? entry.theme : entry.classification);
      }
    },
    [entry.id, entry.theme, entry.classification, field, onSave],
  );

  return (
    <Select value={value} onValueChange={handleChange}>
      <SelectTrigger className="h-8 w-[130px] text-xs">
        <SelectValue />
      </SelectTrigger>
      <SelectContent>
        {options.map((opt) => (
          <SelectItem key={opt} value={opt} className="text-xs">
            {opt}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
}
