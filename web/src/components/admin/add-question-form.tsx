"use client";

import { useState } from "react";
import { toast } from "sonner";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Checkbox } from "@/components/ui/checkbox";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { apiPost } from "@/lib/api-client";

interface AddQuestionFormProps {
  section: string;
  onAdded: () => void;
}

export function AddQuestionForm({ section, onAdded }: AddQuestionFormProps) {
  const [question, setQuestion] = useState("");
  const [type, setType] = useState("yes_no");
  const [hasScoring, setHasScoring] = useState(true);
  const [isReverse, setIsReverse] = useState(false);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!question.trim()) return;

    setLoading(true);
    try {
      await apiPost("/codebook/items", {
        section,
        question: question.trim(),
        type,
        has_scoring: hasScoring,
        is_reverse: isReverse,
      });
      toast.success("Question added");
      setQuestion("");
      setIsReverse(false);
      onAdded();
    } catch (err) {
      toast.error(
        err instanceof Error ? err.message : "Failed to add question",
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-sm font-medium">
          Add Question
        </CardTitle>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-1.5">
            <Label htmlFor="question">Question Text</Label>
            <Input
              id="question"
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              placeholder="Enter question"
              required
            />
          </div>

          <div className="flex gap-4">
            <div className="space-y-1.5">
              <Label>Type</Label>
              <Select value={type} onValueChange={setType}>
                <SelectTrigger className="w-[150px]">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="yes_no">Yes/No</SelectItem>
                  <SelectItem value="numeric">Numeric</SelectItem>
                  <SelectItem value="text">Text</SelectItem>
                  <SelectItem value="categorical_text">
                    Categorical Text
                  </SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="flex items-end gap-4">
              <label className="flex items-center gap-2 text-sm">
                <Checkbox
                  checked={hasScoring}
                  onCheckedChange={(v) => setHasScoring(v === true)}
                />
                Has Scoring
              </label>
              <label className="flex items-center gap-2 text-sm">
                <Checkbox
                  checked={isReverse}
                  onCheckedChange={(v) => setIsReverse(v === true)}
                />
                Reverse Scored
              </label>
            </div>
          </div>

          <Button
            type="submit"
            disabled={loading}
            className="bg-[#0D7377] hover:bg-[#095456]"
          >
            Add Question
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}
