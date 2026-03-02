"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import type { CodebookItem } from "@/lib/types";

interface SectionFormProps {
  section: string;
  items: CodebookItem[];
  responses: Record<string, { answer: string; remark: string }>;
  onChange: (
    responses: Record<string, { answer: string; remark: string }>,
  ) => void;
}

export function SectionForm({
  section,
  items,
  responses,
  onChange,
}: SectionFormProps) {
  function handleAnswer(itemId: string, answer: string) {
    onChange({
      ...responses,
      [itemId]: { ...(responses[itemId] || { answer: "", remark: "" }), answer },
    });
  }

  function handleRemark(itemId: string, remark: string) {
    onChange({
      ...responses,
      [itemId]: { ...(responses[itemId] || { answer: "", remark: "" }), remark },
    });
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-sm font-medium capitalize">
          {section.replace(/_/g, " ")}
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        {items.map((item) => (
          <div key={item.id} className="space-y-2 border-b pb-4 last:border-0">
            <Label className="text-sm">{item.question}</Label>
            {item.type === "yes_no" && (
              <Select
                value={responses[item.id]?.answer || ""}
                onValueChange={(v) => handleAnswer(item.id, v)}
              >
                <SelectTrigger className="w-[120px]">
                  <SelectValue placeholder="Select" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="yes">Yes</SelectItem>
                  <SelectItem value="no">No</SelectItem>
                  <SelectItem value="na">N/A</SelectItem>
                </SelectContent>
              </Select>
            )}
            {item.type === "numeric" && (
              <Input
                type="number"
                value={responses[item.id]?.answer || ""}
                onChange={(e) => handleAnswer(item.id, e.target.value)}
                className="w-[150px]"
                placeholder="Enter value"
              />
            )}
            {(item.type === "text" || item.type === "categorical_text") && (
              <Textarea
                value={responses[item.id]?.answer || ""}
                onChange={(e) => handleAnswer(item.id, e.target.value)}
                placeholder="Enter response"
                rows={2}
              />
            )}
            <Textarea
              value={responses[item.id]?.remark || ""}
              onChange={(e) => handleRemark(item.id, e.target.value)}
              placeholder="Additional remarks (optional)"
              rows={1}
              className="text-xs"
            />
          </div>
        ))}
        {items.length === 0 && (
          <p className="text-sm text-muted-foreground">
            No questions in this section.
          </p>
        )}
      </CardContent>
    </Card>
  );
}
