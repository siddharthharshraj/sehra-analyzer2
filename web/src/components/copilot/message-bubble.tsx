"use client";

import React, { useState, type ReactNode } from "react";
import {
  Pencil,
  Check,
  ThumbsUp,
  ThumbsDown,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";
import dynamic from "next/dynamic";
import { cn } from "@/lib/utils";
import { TypingIndicator } from "./typing-indicator";
import { ToolCallsTimeline } from "./tool-timeline";
import type { CopilotMessage, CopilotAction } from "@/lib/types";

const CopilotChart = dynamic(
  () => import("./copilot-chart").then((m) => m.CopilotChart),
  { ssr: false },
);

const ResultCard = dynamic(
  () => import("./result-card").then((m) => m.ResultCard),
  { ssr: false },
);

// --- Simple markdown renderer ---
function formatInline(text: string): ReactNode[] {
  const parts = text.split(/(\*\*.*?\*\*|\*.*?\*|`.*?`)/g);
  return parts.map((part, i) => {
    if (part.startsWith("**") && part.endsWith("**")) {
      return <strong key={i}>{part.slice(2, -2)}</strong>;
    }
    if (part.startsWith("*") && part.endsWith("*") && part.length > 2) {
      return <em key={i}>{part.slice(1, -1)}</em>;
    }
    if (part.startsWith("`") && part.endsWith("`")) {
      return (
        <code key={i} className="bg-black/5 dark:bg-white/10 px-1 py-0.5 rounded text-xs font-mono">
          {part.slice(1, -1)}
        </code>
      );
    }
    return part;
  });
}

function MarkdownContent({ content, isStreaming }: { content: string; isStreaming?: boolean }) {
  const lines = content.split("\n");
  const elements: ReactNode[] = [];
  let listItems: { text: string; ordered: boolean }[] = [];

  function flushList() {
    if (listItems.length === 0) return;
    const isOrdered = listItems[0].ordered;
    const ListTag = isOrdered ? "ol" : "ul";
    elements.push(
      <ListTag
        key={`list-${elements.length}`}
        className={cn("my-1 space-y-0.5 pl-4", isOrdered ? "list-decimal" : "list-disc")}
      >
        {listItems.map((item, i) => (
          <li key={i} className="leading-relaxed">{formatInline(item.text)}</li>
        ))}
      </ListTag>,
    );
    listItems = [];
  }

  for (let i = 0; i < lines.length; i++) {
    const trimmed = lines[i].trim();

    if (trimmed.startsWith("### ")) {
      flushList();
      elements.push(
        <h4 key={i} className="font-semibold text-[13px] mt-3 mb-1">{formatInline(trimmed.slice(4))}</h4>,
      );
    } else if (trimmed.startsWith("## ")) {
      flushList();
      elements.push(
        <h3 key={i} className="font-semibold text-sm mt-3 mb-1">{formatInline(trimmed.slice(3))}</h3>,
      );
    } else if (trimmed.startsWith("# ")) {
      flushList();
      elements.push(
        <h3 key={i} className="font-bold text-sm mt-3 mb-1">{formatInline(trimmed.slice(2))}</h3>,
      );
    } else if (trimmed.startsWith("- ") || trimmed.startsWith("* ")) {
      if (listItems.length > 0 && listItems[0].ordered) flushList();
      listItems.push({ text: trimmed.slice(2), ordered: false });
    } else if (/^\d+\.\s/.test(trimmed)) {
      if (listItems.length > 0 && !listItems[0].ordered) flushList();
      listItems.push({ text: trimmed.replace(/^\d+\.\s/, ""), ordered: true });
    } else {
      flushList();
      if (trimmed === "") {
        elements.push(<div key={i} className="h-1.5" />);
      } else {
        elements.push(
          <p key={i} className="leading-relaxed">{formatInline(trimmed)}</p>,
        );
      }
    }
  }
  flushList();

  return (
    <div className="space-y-0.5">
      {elements}
      {isStreaming && <span className="streaming-cursor" />}
    </div>
  );
}

// --- Action buttons ---
function ActionButtons({
  actions,
  onExecute,
}: {
  actions: CopilotAction[];
  onExecute: (action: CopilotAction) => void;
}) {
  if (!actions.length) return null;
  return (
    <div className="mt-2 space-y-1.5">
      {actions.map((action, i) => (
        <button
          key={i}
          onClick={() => onExecute(action)}
          className="w-full text-left rounded-lg border border-[#0D7377]/30 bg-[#0D7377]/5 px-3 py-2 text-sm hover:bg-[#0D7377]/10 transition-colors group"
        >
          <div className="font-medium text-[#0D7377] group-hover:underline">
            {action.label}
          </div>
          <div className="text-xs text-muted-foreground mt-0.5">
            {action.description}
          </div>
        </button>
      ))}
    </div>
  );
}

// --- Message bubble with edit + feedback ---
interface MessageBubbleProps {
  message: CopilotMessage;
  isStreaming: boolean;
  onExecuteAction: (action: CopilotAction) => void;
  onFeedback: (messageId: string, rating: "up" | "down") => void;
  onEdit: (messageId: string, correctedText: string) => void;
}

export const MessageBubble = React.memo(function MessageBubble({
  message,
  isStreaming,
  onExecuteAction,
  onFeedback,
  onEdit,
}: MessageBubbleProps) {
  const [isEditing, setIsEditing] = useState(false);
  const [editText, setEditText] = useState("");

  const isCurrentlyStreaming = message.status === "streaming" && isStreaming;

  if (message.role === "user") {
    return (
      <div className="flex justify-end mb-3 copilot-msg-enter">
        <div className="max-w-[85%] rounded-2xl rounded-br-sm bg-gradient-to-br from-[#0D7377] to-[#095456] px-3.5 py-2 text-sm text-white whitespace-pre-wrap shadow-sm">
          {message.content}
        </div>
      </div>
    );
  }

  const displayContent = message.edited ? message.editedContent || message.content : message.content;
  const isDone = message.status === "done" || message.status === "error";
  const showCursor = isCurrentlyStreaming && displayContent.length > 0;

  return (
    <div className="mb-3 group/msg copilot-msg-enter">
      {/* Tool calls timeline */}
      {message.tool_calls && message.tool_calls.length > 0 && (
        <ToolCallsTimeline toolCalls={message.tool_calls} />
      )}

      {/* Tool result cards */}
      {message.tool_results && message.tool_results.length > 0 && (
        <div className="space-y-2 mb-2">
          {message.tool_results.map((result, i) => (
            <ResultCard key={i} result={result} onExecuteAction={onExecuteAction} />
          ))}
        </div>
      )}

      {/* Streaming with no content yet -- show typing indicator */}
      {isCurrentlyStreaming && !displayContent && !message.tool_calls?.length && (
        <div className="max-w-[95%] rounded-2xl rounded-bl-sm bg-muted/60 backdrop-blur-sm">
          <TypingIndicator />
        </div>
      )}

      {displayContent && (
        <div className="relative">
          {isEditing ? (
            <div className="rounded-2xl rounded-bl-sm border-2 border-[#0D7377]/30 p-2">
              <textarea
                value={editText}
                onChange={(e) => setEditText(e.target.value)}
                className="w-full min-h-[80px] text-sm bg-transparent resize-none outline-none"
                autoFocus
              />
              <div className="flex gap-1.5 justify-end mt-1">
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-7 text-xs"
                  onClick={() => setIsEditing(false)}
                >
                  Cancel
                </Button>
                <Button
                  size="sm"
                  className="h-7 text-xs bg-[#0D7377] hover:bg-[#095456]"
                  onClick={() => {
                    if (editText.trim() && editText !== message.content) {
                      onEdit(message.id, editText.trim());
                    }
                    setIsEditing(false);
                  }}
                >
                  <Check className="h-3 w-3 mr-1" />
                  Save
                </Button>
              </div>
            </div>
          ) : (
            <div className={cn(
              "max-w-[95%] rounded-2xl rounded-bl-sm px-3.5 py-2.5 text-sm leading-relaxed shadow-sm",
              "bg-gradient-to-br from-muted/80 to-muted/50 backdrop-blur-sm",
            )}>
              <MarkdownContent content={displayContent} isStreaming={showCursor} />
              {message.edited && (
                <span className="inline-block mt-1 text-[10px] text-[#0D7377] font-medium">
                  Edited
                </span>
              )}
            </div>
          )}
          {/* Action bar: edit + feedback */}
          {isDone && !isEditing && (
            <TooltipProvider delayDuration={300}>
              <div className="flex items-center gap-0.5 mt-1 opacity-0 group-hover/msg:opacity-100 transition-opacity">
                <Tooltip>
                  <TooltipTrigger asChild>
                    <button
                      onClick={() => {
                        setEditText(displayContent);
                        setIsEditing(true);
                      }}
                      className="p-1 rounded hover:bg-muted text-muted-foreground hover:text-foreground transition-colors"
                    >
                      <Pencil className="h-3 w-3" />
                    </button>
                  </TooltipTrigger>
                  <TooltipContent side="bottom" className="text-xs">Edit response</TooltipContent>
                </Tooltip>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <button
                      onClick={() => onFeedback(message.id, "up")}
                      className={cn(
                        "p-1 rounded transition-colors",
                        message.feedback === "up"
                          ? "text-emerald-600 bg-emerald-50"
                          : "text-muted-foreground hover:text-foreground hover:bg-muted",
                      )}
                    >
                      <ThumbsUp className="h-3 w-3" />
                    </button>
                  </TooltipTrigger>
                  <TooltipContent side="bottom" className="text-xs">Helpful</TooltipContent>
                </Tooltip>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <button
                      onClick={() => onFeedback(message.id, "down")}
                      className={cn(
                        "p-1 rounded transition-colors",
                        message.feedback === "down"
                          ? "text-red-600 bg-red-50"
                          : "text-muted-foreground hover:text-foreground hover:bg-muted",
                      )}
                    >
                      <ThumbsDown className="h-3 w-3" />
                    </button>
                  </TooltipTrigger>
                  <TooltipContent side="bottom" className="text-xs">Not helpful</TooltipContent>
                </Tooltip>
              </div>
            </TooltipProvider>
          )}
        </div>
      )}
      {message.chart && (
        <div className="mt-2 rounded-lg border bg-background p-3 shadow-sm">
          <CopilotChart spec={message.chart} />
        </div>
      )}
      {message.actions && (
        <ActionButtons actions={message.actions} onExecute={onExecuteAction} />
      )}
    </div>
  );
});
