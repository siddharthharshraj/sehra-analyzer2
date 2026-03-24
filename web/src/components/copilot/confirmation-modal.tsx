"use client";

import { useState } from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import {
  Pencil,
  CheckCircle2,
  ListChecks,
  FileText,
  ArrowRight,
  AlertTriangle,
} from "lucide-react";
import type { ConfirmationRequest } from "@/lib/types";

const TOOL_CONFIG: Record<string, { label: string; color: string; Icon: typeof Pencil }> = {
  edit_entry: { label: "Edit Entry", color: "bg-emerald-500", Icon: Pencil },
  change_status: { label: "Change Status", color: "bg-blue-500", Icon: CheckCircle2 },
  batch_approve: { label: "Batch Approve", color: "bg-teal-500", Icon: ListChecks },
  edit_executive_summary: { label: "Edit Summary", color: "bg-purple-500", Icon: FileText },
};

interface ConfirmationModalProps {
  request: ConfirmationRequest | null;
  onConfirm: (toolCallId: string, approved: boolean) => void;
}

export function ConfirmationModal({ request, onConfirm }: ConfirmationModalProps) {
  const [editMode, setEditMode] = useState(false);
  const [editedArgs, setEditedArgs] = useState("");

  if (!request) return null;

  const config = TOOL_CONFIG[request.toolName] || {
    label: request.toolName,
    color: "bg-gray-500",
    Icon: AlertTriangle,
  };
  const { label, color, Icon } = config;
  const preview = request.preview;

  function handleApprove() {
    if (!request) return;
    onConfirm(request.toolCallId, true);
    setEditMode(false);
  }

  function handleReject() {
    if (!request) return;
    onConfirm(request.toolCallId, false);
    setEditMode(false);
  }

  function handleEditApprove() {
    if (!request) return;
    onConfirm(request.toolCallId, true);
    setEditMode(false);
  }

  return (
    <Dialog open={!!request} onOpenChange={(open) => { if (!open) handleReject(); }}>
      <DialogContent
        className="sm:max-w-md animate-in slide-in-from-bottom-4 duration-300"
        showCloseButton={false}
      >
        <DialogHeader>
          <div className="flex items-center gap-2.5 mb-1">
            <div className={`flex h-8 w-8 items-center justify-center rounded-lg ${color} text-white shrink-0`}>
              <Icon className="h-4 w-4" />
            </div>
            <div>
              <DialogTitle className="text-base">{label}</DialogTitle>
              <Badge variant="outline" className="mt-0.5 text-[10px] font-mono">
                {request.toolName}
              </Badge>
            </div>
          </div>
          <DialogDescription className="text-sm leading-relaxed mt-2">
            {request.description}
          </DialogDescription>
        </DialogHeader>

        {/* Diff view for before/after */}
        {preview && (preview.oldValue || preview.newValue) && (
          <div className="rounded-lg border overflow-hidden">
            {preview.oldValue && (
              <div className="bg-red-50 dark:bg-red-950/20 px-3 py-2 border-b">
                <div className="flex items-center gap-1.5 mb-1">
                  <span className="text-[10px] font-semibold uppercase tracking-wide text-red-600 dark:text-red-400">Before</span>
                </div>
                <p className="text-sm text-red-800 dark:text-red-300 leading-relaxed line-through decoration-red-400/50">
                  {preview.oldValue}
                </p>
              </div>
            )}
            {preview.newValue && (
              <div className="bg-emerald-50 dark:bg-emerald-950/20 px-3 py-2">
                <div className="flex items-center gap-1.5 mb-1">
                  <span className="text-[10px] font-semibold uppercase tracking-wide text-emerald-600 dark:text-emerald-400">After</span>
                </div>
                <p className="text-sm text-emerald-800 dark:text-emerald-300 leading-relaxed">
                  {preview.newValue}
                </p>
              </div>
            )}
          </div>
        )}

        {/* Batch count display */}
        {preview?.count && preview.count > 1 && (
          <div className="flex items-center gap-3 rounded-lg border border-teal-200 dark:border-teal-800 bg-teal-50 dark:bg-teal-950/20 px-4 py-3">
            <ListChecks className="h-5 w-5 text-teal-600 dark:text-teal-400 shrink-0" />
            <div>
              <p className="text-sm font-medium text-teal-900 dark:text-teal-100">
                This will approve {preview.count} entries
              </p>
              <p className="text-xs text-teal-600 dark:text-teal-400 mt-0.5">
                All matching entries will be updated at once
              </p>
            </div>
          </div>
        )}

        {/* Arguments summary */}
        {Object.keys(request.args).length > 0 && !editMode && (
          <div className="rounded-lg border bg-muted/30 px-3 py-2">
            <p className="text-[10px] font-semibold uppercase tracking-wide text-muted-foreground mb-1.5">Parameters</p>
            <div className="space-y-1">
              {Object.entries(request.args).map(([key, value]) => (
                <div key={key} className="flex items-center gap-2 text-xs">
                  <span className="font-mono text-muted-foreground min-w-[80px]">{key}</span>
                  <ArrowRight className="h-2.5 w-2.5 text-muted-foreground shrink-0" />
                  <span className="font-medium truncate">{String(value)}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Edit mode */}
        {editMode && (
          <div className="rounded-lg border px-3 py-2">
            <p className="text-[10px] font-semibold uppercase tracking-wide text-muted-foreground mb-1.5">Edit Parameters (JSON)</p>
            <textarea
              value={editedArgs}
              onChange={(e) => setEditedArgs(e.target.value)}
              className="w-full min-h-[80px] text-xs font-mono bg-transparent resize-none outline-none"
              autoFocus
            />
          </div>
        )}

        <Separator />

        <DialogFooter className="flex-row gap-2 sm:gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={handleReject}
            className="flex-1"
          >
            Reject
          </Button>
          {!editMode ? (
            <Button
              variant="secondary"
              size="sm"
              onClick={() => {
                setEditedArgs(JSON.stringify(request.args, null, 2));
                setEditMode(true);
              }}
              className="flex-1"
            >
              <Pencil className="h-3 w-3 mr-1" />
              Edit & Approve
            </Button>
          ) : (
            <Button
              variant="secondary"
              size="sm"
              onClick={handleEditApprove}
              className="flex-1"
            >
              <CheckCircle2 className="h-3 w-3 mr-1" />
              Save & Approve
            </Button>
          )}
          {!editMode && (
            <Button
              size="sm"
              onClick={handleApprove}
              className="flex-1 bg-[#0D7377] hover:bg-[#095456] text-white"
            >
              <CheckCircle2 className="h-3 w-3 mr-1" />
              Approve
            </Button>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
