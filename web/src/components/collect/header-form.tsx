"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

interface HeaderFormProps {
  header: Record<string, string>;
  onChange: (header: Record<string, string>) => void;
}

const fields = [
  { key: "country", label: "Country" },
  { key: "province", label: "Province / State" },
  { key: "district", label: "District" },
  { key: "assessment_date", label: "Assessment Date", type: "date" },
];

export function HeaderForm({ header, onChange }: HeaderFormProps) {
  function handleChange(key: string, value: string) {
    onChange({ ...header, [key]: value });
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-sm font-medium">
          Assessment Details
        </CardTitle>
      </CardHeader>
      <CardContent className="grid gap-4 sm:grid-cols-2">
        {fields.map((f) => (
          <div key={f.key} className="space-y-1.5">
            <Label htmlFor={f.key}>{f.label}</Label>
            <Input
              id={f.key}
              type={f.type || "text"}
              value={header[f.key] || ""}
              onChange={(e) => handleChange(f.key, e.target.value)}
              placeholder={f.label}
            />
          </div>
        ))}
      </CardContent>
    </Card>
  );
}
