"use client";

import React, { useState } from "react";
import {
  ChevronDown,
  ChevronRight,
  Plus,
  Loader2,
  History,
  Trash2,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import type { StoredConversation } from "@/lib/types";

function relativeDate(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return "Just now";
  if (mins < 60) return `${mins}m ago`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  if (days < 7) return `${days}d ago`;
  return new Date(iso).toLocaleDateString();
}

interface ConversationListProps {
  conversations: StoredConversation[];
  activeId: string;
  onLoad: (id: string) => void;
  onDelete: (id: string) => void;
  onNew: () => void;
  loading: boolean;
}

export const ConversationList = React.memo(function ConversationList({
  conversations,
  activeId,
  onLoad,
  onDelete,
  onNew,
  loading,
}: ConversationListProps) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className="border-b shrink-0">
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center gap-2 px-4 py-2 text-xs text-muted-foreground hover:text-foreground transition-colors"
      >
        <History className="h-3 w-3" />
        <span>
          {loading
            ? "Loading..."
            : `${conversations.length} conversation${conversations.length !== 1 ? "s" : ""}`}
        </span>
        {expanded ? (
          <ChevronDown className="h-3 w-3 ml-auto" />
        ) : (
          <ChevronRight className="h-3 w-3 ml-auto" />
        )}
      </button>
      {expanded && (
        <div className="px-2 pb-2 max-h-[200px] overflow-y-auto space-y-0.5">
          <button
            onClick={onNew}
            className="w-full flex items-center gap-2 rounded-md px-2 py-1.5 text-xs font-medium text-[#0D7377] hover:bg-[#0D7377]/5 transition-colors"
          >
            <Plus className="h-3 w-3" />
            New conversation
          </button>
          {loading && (
            <div className="flex items-center justify-center py-3">
              <Loader2 className="h-3 w-3 animate-spin text-muted-foreground" />
            </div>
          )}
          {!loading && conversations.length === 0 && (
            <div className="px-2 py-6 text-center">
              <p className="text-[11px] text-muted-foreground">
                Start your first conversation by typing below
              </p>
            </div>
          )}
          {conversations.map((convo) => (
            <div
              key={convo.id}
              className={cn(
                "group flex items-center gap-2 rounded-md px-2 py-1.5 text-xs cursor-pointer transition-colors",
                convo.id === activeId
                  ? "bg-[#0D7377]/10 text-[#0D7377]"
                  : "hover:bg-muted/50 text-foreground",
              )}
              onClick={() => onLoad(convo.id)}
            >
              <div className="flex-1 min-w-0">
                <div className="truncate font-medium">{convo.title}</div>
                <div className="flex items-center gap-1.5 text-[10px] text-muted-foreground">
                  <span>{relativeDate(convo.updatedAt)}</span>
                  {convo.sehraLabel && (
                    <>
                      <span className="text-muted-foreground/40">|</span>
                      <Badge variant="outline" className="text-[8px] px-1 py-0 h-3.5 border-[#0D7377]/30 text-[#0D7377]">
                        {convo.sehraLabel}
                      </Badge>
                    </>
                  )}
                </div>
              </div>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  onDelete(convo.id);
                }}
                className="opacity-0 group-hover:opacity-100 shrink-0 p-0.5 rounded hover:bg-red-100 hover:text-red-600 transition-all"
                title="Delete conversation"
              >
                <Trash2 className="h-3 w-3" />
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
});
