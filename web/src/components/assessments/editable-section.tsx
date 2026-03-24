"use client";

import { useState, useRef, useEffect } from "react";
import { Pencil, Check, X, Sparkles, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { toast } from "sonner";
import { cn } from "@/lib/utils";

interface EditableSectionProps {
  title: string;
  content: string;
  onSave: (newContent: string) => Promise<void>;
  onAskCopilot?: (prompt: string) => void;
  emptyText?: string;
}

export function EditableSection({
  title,
  content,
  onSave,
  onAskCopilot,
  emptyText,
}: EditableSectionProps) {
  const [isEditing, setIsEditing] = useState(false);
  const [draft, setDraft] = useState(content);
  const [isSaving, setIsSaving] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    if (isEditing && textareaRef.current) {
      textareaRef.current.focus();
      textareaRef.current.selectionStart = textareaRef.current.value.length;
    }
  }, [isEditing]);

  // Keep draft in sync when content changes externally
  useEffect(() => {
    if (!isEditing) {
      setDraft(content);
    }
  }, [content, isEditing]);

  async function handleSave() {
    if (draft === content) {
      setIsEditing(false);
      return;
    }
    setIsSaving(true);
    try {
      await onSave(draft);
      toast.success(`${title} updated`);
      setIsEditing(false);
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Failed to save");
      setDraft(content);
    } finally {
      setIsSaving(false);
    }
  }

  function handleCancel() {
    setDraft(content);
    setIsEditing(false);
  }

  function handleAskCopilot() {
    if (onAskCopilot) {
      onAskCopilot(
        `Improve the following ${title.toLowerCase()} for the SEHRA report. Make it clearer, more actionable, and better structured:\n\n${draft || content}`,
      );
    }
  }

  const hasContent = !!content;

  return (
    <div className="group relative">
      {/* Header row */}
      <div className="mb-2 flex items-center justify-between">
        <h3 className="text-sm font-semibold text-foreground">{title}</h3>
        {!isEditing && (
          <Tooltip>
            <TooltipTrigger asChild>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setIsEditing(true)}
                className={cn(
                  "h-7 gap-1.5 px-2 text-xs text-muted-foreground transition-opacity",
                  "opacity-0 group-hover:opacity-100 focus:opacity-100",
                )}
              >
                <Pencil className="h-3 w-3" />
                Edit
              </Button>
            </TooltipTrigger>
            <TooltipContent side="bottom" className="max-w-[280px] text-sm">
              <p>Click to edit this section. Your changes are saved and marked as human-reviewed.</p>
            </TooltipContent>
          </Tooltip>
        )}
      </div>

      {/* Content / Editor */}
      {isEditing ? (
        <div className="space-y-3">
          <Textarea
            ref={textareaRef}
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            className="min-h-[120px] resize-y text-sm leading-relaxed focus-teal"
            placeholder={`Enter ${title.toLowerCase()}...`}
          />
          <div className="flex items-center gap-2">
            <Button
              size="sm"
              onClick={handleSave}
              disabled={isSaving}
              className="gap-1.5 bg-[#0D7377] hover:bg-[#095456]"
            >
              {isSaving ? (
                <Loader2 className="h-3.5 w-3.5 animate-spin" />
              ) : (
                <Check className="h-3.5 w-3.5" />
              )}
              Save
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={handleCancel}
              disabled={isSaving}
              className="gap-1.5"
            >
              <X className="h-3.5 w-3.5" />
              Cancel
            </Button>
            {onAskCopilot && (
              <Button
                variant="ghost"
                size="sm"
                onClick={handleAskCopilot}
                disabled={isSaving}
                className="ml-auto gap-1.5 text-xs text-[#0D7377] hover:text-[#095456]"
              >
                <Sparkles className="h-3.5 w-3.5" />
                Ask Copilot to improve
              </Button>
            )}
          </div>
        </div>
      ) : hasContent ? (
        <p className="whitespace-pre-wrap text-sm leading-relaxed text-foreground/80">
          {content}
        </p>
      ) : emptyText ? (
        <p className="text-sm italic text-muted-foreground">{emptyText}</p>
      ) : null}
    </div>
  );
}
