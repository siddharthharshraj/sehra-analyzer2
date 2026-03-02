"use client";

import { useState, useRef, useEffect, type ReactNode } from "react";
import {
  Bot,
  Send,
  X,
  Loader2,
  ChevronDown,
  ChevronRight,
  Wrench,
  CheckCircle2,
  AlertCircle,
  Sparkles,
  Plus,
  Square,
  HelpCircle,
  MessageSquare,
  BarChart3,
  FileText,
  Upload,
  Shield,
  Database,
  BookOpen,
  FileSearch,
  History,
  Trash2,
  Pencil,
  Check,
  ThumbsUp,
  ThumbsDown,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import dynamic from "next/dynamic";

const CopilotChart = dynamic(
  () => import("./copilot-chart").then((m) => m.CopilotChart),
  { ssr: false },
);
import { useCopilotContext } from "./copilot-context";
import { cn } from "@/lib/utils";
import { toast } from "sonner";
import type { CopilotMessage, CopilotToolCall, CopilotAction, StoredConversation } from "@/lib/types";

// --- Suggested prompts ---
const PROMPTS_WITH_CONTEXT = [
  { icon: BarChart3, text: "Summarize this assessment" },
  { icon: FileText, text: "Compare enablers vs barriers" },
  { icon: Sparkles, text: "What should I do next?" },
  { icon: Database, text: "Show low-confidence entries" },
];

const PROMPTS_NO_CONTEXT = [
  { icon: FileSearch, text: "List all assessments" },
  { icon: BarChart3, text: "How many assessments have been uploaded?" },
  { icon: BookOpen, text: "What sections does the codebook have?" },
  { icon: Sparkles, text: "Help me get started" },
];

// --- Help topics ---
const HELP_TOPICS = [
  {
    icon: Upload,
    question: "How do I upload a SEHRA assessment?",
    answer:
      "Go to Upload PDF in the sidebar. Drag & drop your SEHRA assessment PDF or click to browse. The system will automatically extract, score, and classify all data using AI. You can track real-time progress as each component is analyzed.",
  },
  {
    icon: BarChart3,
    question: "How do I read the dashboard?",
    answer:
      "The Dashboard shows KPI cards (total enablers, barriers, readiness score), a radar chart comparing components, and a bar chart for enabler/barrier breakdown. Select an assessment from the dropdown at the top. Click any component tab to see individual qualitative entries and report sections.",
  },
  {
    icon: Shield,
    question: "How does the review workflow work?",
    answer:
      "Each AI-classified entry has a confidence score. You can edit classifications inline (click theme/classification badges), batch approve high-confidence entries (>80%), then mark the assessment as Reviewed and finally Published. The status flow is: Draft -> Reviewed -> Published.",
  },
  {
    icon: FileText,
    question: "What export formats are available?",
    answer:
      "Go to Export & Share. You can download reports as DOCX (Word), XLSX (Excel), HTML, or PDF. You can also create shareable links with passcode protection and optional expiry dates.",
  },
  {
    icon: BookOpen,
    question: "What is the codebook?",
    answer:
      "The codebook defines all SEHRA questions, organized by component (Context, Policy, Service Delivery, Human Resources, Supply Chain, Barriers). Admins can manage questions via Manage Questions. Each item has scoring rules (yes/no, reverse scoring) used for automated analysis.",
  },
  {
    icon: Bot,
    question: "What can the Copilot do?",
    answer:
      "The Copilot can list assessments, summarize findings, compare enablers vs barriers with charts, search entries by theme or confidence, compare two assessments side by side, and suggest next actions like batch approving entries or changing status. Just ask in natural language!",
  },
];

// --- Tool calls collapsible ---
function ToolCallsSection({ toolCalls }: { toolCalls: CopilotToolCall[] }) {
  const [expanded, setExpanded] = useState(false);
  if (!toolCalls.length) return null;

  const allDone = toolCalls.every((tc) => tc.status === "done");

  return (
    <div className="my-1.5">
      <button
        onClick={() => setExpanded(!expanded)}
        className="flex items-center gap-1.5 text-xs text-muted-foreground hover:text-foreground transition-colors"
      >
        {expanded ? <ChevronDown className="h-3 w-3" /> : <ChevronRight className="h-3 w-3" />}
        <Wrench className="h-3 w-3" />
        <span>
          {toolCalls.length} tool{toolCalls.length !== 1 ? "s" : ""} used
        </span>
        {!allDone && <Loader2 className="h-3 w-3 animate-spin" />}
      </button>
      {expanded && (
        <div className="mt-1.5 ml-5 space-y-1">
          {toolCalls.map((tc, i) => (
            <div key={i} className="flex items-start gap-1.5 text-xs">
              {tc.status === "running" ? (
                <Loader2 className="h-3 w-3 animate-spin text-blue-500 mt-0.5 shrink-0" />
              ) : tc.status === "error" ? (
                <AlertCircle className="h-3 w-3 text-red-500 mt-0.5 shrink-0" />
              ) : (
                <CheckCircle2 className="h-3 w-3 text-green-500 mt-0.5 shrink-0" />
              )}
              <span className="font-mono text-muted-foreground truncate">
                {tc.tool}
                {Object.keys(tc.arguments).length > 0
                  ? `(${Object.entries(tc.arguments)
                      .map(([k, v]) => `${k}=${JSON.stringify(v)}`)
                      .join(", ")
                      .slice(0, 50)})`
                  : "()"}
              </span>
            </div>
          ))}
        </div>
      )}
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

// --- Relative date helper ---
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

// --- Conversation history panel ---
function ConversationHistory({
  conversations,
  activeId,
  onLoad,
  onDelete,
  onNew,
  loading,
}: {
  conversations: StoredConversation[];
  activeId: string;
  onLoad: (id: string) => void;
  onDelete: (id: string) => void;
  onNew: () => void;
  loading: boolean;
}) {
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
            <p className="px-2 py-3 text-center text-[10px] text-muted-foreground">
              No previous conversations
            </p>
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
                      <span>·</span>
                      <span className="truncate">{convo.sehraLabel}</span>
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
}

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

function MarkdownContent({ content }: { content: string }) {
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

  return <div className="space-y-0.5">{elements}</div>;
}

// --- Message bubble with edit + feedback ---
function MessageBubble({
  message,
  onExecuteAction,
  onFeedback,
  onEdit,
}: {
  message: CopilotMessage;
  onExecuteAction: (action: CopilotAction) => void;
  onFeedback: (messageId: string, rating: "up" | "down") => void;
  onEdit: (messageId: string, correctedText: string) => void;
}) {
  const [isEditing, setIsEditing] = useState(false);
  const [editText, setEditText] = useState("");

  if (message.role === "user") {
    return (
      <div className="flex justify-end mb-3">
        <div className="max-w-[85%] rounded-2xl rounded-br-sm bg-[#0D7377] px-3.5 py-2 text-sm text-white whitespace-pre-wrap">
          {message.content}
        </div>
      </div>
    );
  }

  const displayContent = message.edited ? message.editedContent || message.content : message.content;
  const isDone = message.status === "done" || message.status === "error";

  return (
    <div className="mb-3 group/msg">
      {message.tool_calls && message.tool_calls.length > 0 && (
        <ToolCallsSection toolCalls={message.tool_calls} />
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
            <div className="max-w-[95%] rounded-2xl rounded-bl-sm bg-muted px-3.5 py-2.5 text-sm leading-relaxed">
              <MarkdownContent content={displayContent} />
              {message.edited && (
                <span className="inline-block mt-1 text-[10px] text-[#0D7377] font-medium">
                  Edited
                </span>
              )}
            </div>
          )}
          {/* Action bar: edit + feedback */}
          {isDone && !isEditing && (
            <div className="flex items-center gap-0.5 mt-1 opacity-0 group-hover/msg:opacity-100 transition-opacity">
              <button
                onClick={() => {
                  setEditText(displayContent);
                  setIsEditing(true);
                }}
                className="p-1 rounded hover:bg-muted text-muted-foreground hover:text-foreground transition-colors"
                title="Edit response"
              >
                <Pencil className="h-3 w-3" />
              </button>
              <button
                onClick={() => onFeedback(message.id, "up")}
                className={cn(
                  "p-1 rounded transition-colors",
                  message.feedback === "up"
                    ? "text-green-600 bg-green-50"
                    : "text-muted-foreground hover:text-foreground hover:bg-muted",
                )}
                title="Helpful"
              >
                <ThumbsUp className="h-3 w-3" />
              </button>
              <button
                onClick={() => onFeedback(message.id, "down")}
                className={cn(
                  "p-1 rounded transition-colors",
                  message.feedback === "down"
                    ? "text-red-600 bg-red-50"
                    : "text-muted-foreground hover:text-foreground hover:bg-muted",
                )}
                title="Not helpful"
              >
                <ThumbsDown className="h-3 w-3" />
              </button>
            </div>
          )}
        </div>
      )}
      {message.chart && (
        <div className="mt-2 rounded-lg border bg-background p-3">
          <CopilotChart spec={message.chart} />
        </div>
      )}
      {message.actions && (
        <ActionButtons actions={message.actions} onExecute={onExecuteAction} />
      )}
    </div>
  );
}

// --- Help panel ---
function HelpPanel({ onSwitchToChat }: { onSwitchToChat: () => void }) {
  const [expandedIndex, setExpandedIndex] = useState<number | null>(null);

  return (
    <div className="px-4 py-3">
      <div className="mb-3">
        <h3 className="text-sm font-medium mb-1">Platform Help</h3>
        <p className="text-xs text-muted-foreground">
          Tap a topic to learn more, or ask the Copilot any question.
        </p>
      </div>
      <div className="space-y-1.5">
        {HELP_TOPICS.map((topic, i) => (
          <div key={i} className="rounded-lg border overflow-hidden">
            <button
              onClick={() => setExpandedIndex(expandedIndex === i ? null : i)}
              className="w-full flex items-center gap-2.5 px-3 py-2.5 text-left hover:bg-muted/50 transition-colors"
            >
              <topic.icon className="h-4 w-4 text-[#0D7377] shrink-0" />
              <span className="text-sm font-medium flex-1">{topic.question}</span>
              {expandedIndex === i ? (
                <ChevronDown className="h-3.5 w-3.5 text-muted-foreground shrink-0" />
              ) : (
                <ChevronRight className="h-3.5 w-3.5 text-muted-foreground shrink-0" />
              )}
            </button>
            {expandedIndex === i && (
              <div className="px-3 pb-3 pt-0">
                <p className="text-xs text-muted-foreground leading-relaxed">
                  {topic.answer}
                </p>
              </div>
            )}
          </div>
        ))}
      </div>
      <Separator className="my-3" />
      <p className="text-xs text-muted-foreground text-center">
        Have a different question? Switch to{" "}
        <button
          onClick={onSwitchToChat}
          className="text-[#0D7377] font-medium hover:underline"
        >
          Chat
        </button>{" "}
        and ask the Copilot.
      </p>
    </div>
  );
}

// --- Main sidebar content ---
function SidebarContent({ onClose }: { onClose: () => void }) {
  const {
    messages,
    isStreaming,
    thinkingText,
    sendMessage,
    executeAction,
    cancel,
    sehraId,
    sehraLabel,
    conversationId,
    conversations,
    conversationsLoading,
    loadConversation,
    removeConversation,
    newConversation,
    setMessageFeedback,
    setMessageEdit,
  } = useCopilotContext();
  const [input, setInput] = useState("");
  const [activeTab, setActiveTab] = useState<"chat" | "help">("chat");
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    scrollRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, thinkingText]);

  function handleSend() {
    if (!input.trim() || isStreaming) return;
    setActiveTab("chat");
    sendMessage(input.trim());
    setInput("");
  }

  async function handleAction(action: CopilotAction) {
    try {
      await executeAction(action);
      toast.success(`${action.label} completed`);
    } catch (err) {
      toast.error(
        `Failed: ${err instanceof Error ? err.message : "Unknown error"}`,
      );
    }
  }

  const isEmpty = messages.length === 0;
  const prompts = sehraId ? PROMPTS_WITH_CONTEXT : PROMPTS_NO_CONTEXT;

  return (
    <div className="flex h-full flex-col">
      {/* Header */}
      <div className="flex items-center justify-between border-b px-4 py-2.5 shrink-0">
        <div className="flex items-center gap-2">
          <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-[#0D7377]">
            <Bot className="h-4 w-4 text-white" />
          </div>
          <div>
            <span className="font-semibold text-sm leading-none">SEHRA Copilot</span>
            {sehraLabel && (
              <p className="text-[10px] text-muted-foreground leading-tight mt-0.5 truncate max-w-[200px]">
                {sehraLabel}
              </p>
            )}
          </div>
        </div>
        <div className="flex items-center gap-0.5">
          {messages.length > 0 && (
            <Button
              variant="ghost"
              size="icon"
              className="h-7 w-7"
              onClick={newConversation}
              title="New conversation"
            >
              <Plus className="h-3.5 w-3.5" />
            </Button>
          )}
          <Button variant="ghost" size="icon" className="h-7 w-7" onClick={onClose}>
            <X className="h-4 w-4" />
          </Button>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex border-b shrink-0">
        <button
          onClick={() => setActiveTab("chat")}
          className={cn(
            "flex-1 flex items-center justify-center gap-1.5 py-2 text-xs font-medium transition-colors border-b-2",
            activeTab === "chat"
              ? "border-[#0D7377] text-[#0D7377]"
              : "border-transparent text-muted-foreground hover:text-foreground",
          )}
        >
          <MessageSquare className="h-3.5 w-3.5" />
          Chat
          {messages.length > 0 && (
            <span className="ml-0.5 flex h-4 min-w-4 items-center justify-center rounded-full bg-[#0D7377]/10 px-1 text-[10px] font-medium text-[#0D7377]">
              {messages.length}
            </span>
          )}
        </button>
        <button
          onClick={() => setActiveTab("help")}
          className={cn(
            "flex-1 flex items-center justify-center gap-1.5 py-2 text-xs font-medium transition-colors border-b-2",
            activeTab === "help"
              ? "border-[#0D7377] text-[#0D7377]"
              : "border-transparent text-muted-foreground hover:text-foreground",
          )}
        >
          <HelpCircle className="h-3.5 w-3.5" />
          Help
        </button>
      </div>

      {/* Conversation history */}
      {activeTab === "chat" && (
        <ConversationHistory
          conversations={conversations}
          activeId={conversationId}
          onLoad={(id) => {
            loadConversation(id);
            setActiveTab("chat");
          }}
          onDelete={removeConversation}
          onNew={newConversation}
          loading={conversationsLoading}
        />
      )}

      {/* Content */}
      {activeTab === "help" ? (
        <ScrollArea className="flex-1 min-h-0">
          <HelpPanel onSwitchToChat={() => setActiveTab("chat")} />
        </ScrollArea>
      ) : (
        <ScrollArea className="flex-1 min-h-0">
          <div className="px-4 py-3">
            {isEmpty && (
              <div className="flex flex-col items-center justify-center py-6 text-center">
                <div className="mb-3 rounded-full bg-[#0D7377]/10 p-3">
                  <Sparkles className="h-6 w-6 text-[#0D7377]" />
                </div>
                <h3 className="mb-1 font-medium text-sm">How can I help?</h3>
                <p className="mb-4 text-xs text-muted-foreground max-w-[240px]">
                  {sehraId
                    ? `Ask about ${sehraLabel || "this assessment"}, get insights, or take actions.`
                    : "Ask questions about your SEHRA assessments, get insights, or take actions."}
                </p>
                <div className="space-y-1.5 w-full">
                  {prompts.map((prompt) => (
                    <button
                      key={prompt.text}
                      onClick={() => sendMessage(prompt.text)}
                      className="w-full flex items-center gap-2.5 rounded-lg border px-3 py-2.5 text-left text-xs hover:bg-muted transition-colors"
                    >
                      <prompt.icon className="h-3.5 w-3.5 text-[#0D7377] shrink-0" />
                      {prompt.text}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {messages.map((msg) => (
              <MessageBubble
                key={msg.id}
                message={msg}
                onExecuteAction={handleAction}
                onFeedback={setMessageFeedback}
                onEdit={setMessageEdit}
              />
            ))}

            {thinkingText && (
              <div className="mb-3 flex items-center gap-2 text-xs text-muted-foreground">
                <Loader2 className="h-3 w-3 animate-spin" />
                {thinkingText}
              </div>
            )}

            <div ref={scrollRef} />
          </div>
        </ScrollArea>
      )}

      <Separator />

      {/* Input */}
      <div className="p-3 shrink-0">
        <div className="flex gap-2">
          <Input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder={
              sehraId
                ? `Ask about ${sehraLabel || "this assessment"}...`
                : "Ask anything..."
            }
            onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && handleSend()}
            disabled={isStreaming}
            className={cn(
              "text-sm transition-all",
              isStreaming && "opacity-60 border-[#0D7377]/40 animate-pulse",
            )}
          />
          {isStreaming ? (
            <Button
              onClick={cancel}
              variant="outline"
              size="icon"
              className="shrink-0"
              title="Stop"
            >
              <Square className="h-4 w-4" />
            </Button>
          ) : (
            <Button
              onClick={handleSend}
              disabled={!input.trim()}
              className="shrink-0 bg-[#0D7377] hover:bg-[#095456]"
              size="icon"
            >
              <Send className="h-4 w-4" />
            </Button>
          )}
        </div>
      </div>
    </div>
  );
}

// --- Mobile detection hook ---
function useIsMobile() {
  const [isMobile, setIsMobile] = useState(false);
  useEffect(() => {
    const mq = window.matchMedia("(max-width: 1023px)");
    setIsMobile(mq.matches);
    const handler = (e: MediaQueryListEvent) => setIsMobile(e.matches);
    mq.addEventListener("change", handler);
    return () => mq.removeEventListener("change", handler);
  }, []);
  return isMobile;
}

// --- Exported sidebar component ---
export function CopilotSidebar() {
  const { isOpen, toggle, close } = useCopilotContext();
  const isMobile = useIsMobile();

  return (
    <>
      {/* Desktop: fixed right panel */}
      {isOpen && !isMobile && (
        <aside className="fixed inset-y-0 right-0 z-40 w-[380px] border-l bg-background shadow-lg flex flex-col animate-in slide-in-from-right duration-200">
          <SidebarContent onClose={close} />
        </aside>
      )}

      {/* Mobile: overlay + slide-in drawer */}
      {isOpen && isMobile && (
        <>
          <div
            className="fixed inset-0 z-40 bg-black/40 animate-in fade-in duration-200"
            onClick={close}
          />
          <aside className="fixed inset-y-0 right-0 z-50 w-[340px] max-w-[90vw] bg-background shadow-xl flex flex-col animate-in slide-in-from-right duration-200">
            <SidebarContent onClose={close} />
          </aside>
        </>
      )}

      {/* Floating toggle button */}
      {!isOpen && (
        <button
          onClick={toggle}
          className="fixed bottom-6 right-6 z-30 flex h-12 w-12 items-center justify-center rounded-full bg-[#0D7377] text-white shadow-lg hover:bg-[#095456] hover:scale-105 active:scale-95 transition-all lg:bottom-8 lg:right-8"
          title="Open SEHRA Copilot"
        >
          <Bot className="h-6 w-6" />
        </button>
      )}
    </>
  );
}
