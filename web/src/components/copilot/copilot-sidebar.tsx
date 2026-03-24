"use client";

import { useState, useRef, useEffect } from "react";
import {
  Bot,
  X,
  Loader2,
  Sparkles,
  Plus,
  HelpCircle,
  MessageSquare,
  BarChart3,
  FileText,
  Database,
  BookOpen,
  FileSearch,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";
import dynamic from "next/dynamic";
import { useCopilotContext } from "./copilot-context";
import { cn } from "@/lib/utils";
import { toast } from "sonner";
import { MessageBubble } from "./message-bubble";
import { ChatInput } from "./chat-input";
import { ConversationList } from "./conversation-list";
import { HelpPanel } from "./help-panel";
import { CopilotErrorBoundary } from "./error-boundary";
import type { CopilotAction } from "@/lib/types";

const ConfirmationModal = dynamic(
  () => import("./confirmation-modal").then((m) => m.ConfirmationModal),
  { ssr: false },
);

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

function SidebarContent({ onClose }: { onClose: () => void }) {
  const {
    messages,
    isStreaming,
    thinkingText,
    pendingConfirmation,
    sendMessage,
    confirmAction,
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
  const [activeTab, setActiveTab] = useState<"chat" | "help">("chat");
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    scrollRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, thinkingText]);

  function handleSend(text: string) {
    setActiveTab("chat");
    sendMessage(text);
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
      <ConfirmationModal
        request={pendingConfirmation}
        onConfirm={confirmAction}
      />

      {/* Header */}
      <div className="flex items-center justify-between border-b px-4 py-2.5 shrink-0 bg-background/80 backdrop-blur-xl supports-[backdrop-filter]:bg-background/60">
        <div className="flex items-center gap-2">
          <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-gradient-to-br from-[#0D7377] to-[#095456] shadow-sm">
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
            <TooltipProvider delayDuration={300}>
              <Tooltip>
                <TooltipTrigger asChild>
                  <Button variant="ghost" size="icon" className="h-7 w-7" onClick={newConversation}>
                    <Plus className="h-3.5 w-3.5" />
                  </Button>
                </TooltipTrigger>
                <TooltipContent side="bottom" className="text-xs">New conversation</TooltipContent>
              </Tooltip>
            </TooltipProvider>
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
        <ConversationList
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
          <div className="px-4 py-3 bg-gradient-to-b from-transparent via-transparent to-muted/10">
            {isEmpty && (
              <div className="flex flex-col items-center justify-center py-6 text-center">
                <div className="mb-3 rounded-full bg-gradient-to-br from-[#0D7377]/10 to-[#0D7377]/5 p-3 shadow-sm">
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
                      onClick={() => handleSend(prompt.text)}
                      className="w-full flex items-center gap-2.5 rounded-lg border px-3 py-2.5 text-left text-xs hover:bg-muted/70 hover:border-[#0D7377]/20 transition-all"
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
                isStreaming={isStreaming}
                onExecuteAction={handleAction}
                onFeedback={setMessageFeedback}
                onEdit={setMessageEdit}
              />
            ))}

            {thinkingText && (
              <div className="mb-3 copilot-msg-enter">
                <div className="flex items-center gap-2 text-xs text-muted-foreground bg-muted/30 rounded-lg px-3 py-2 backdrop-blur-sm">
                  <Loader2 className="h-3 w-3 animate-spin text-[#0D7377]" />
                  <span>{thinkingText}</span>
                </div>
              </div>
            )}

            <div ref={scrollRef} />
          </div>
        </ScrollArea>
      )}

      <Separator />

      <ChatInput
        sehraId={sehraId}
        sehraLabel={sehraLabel}
        isStreaming={isStreaming}
        onSend={handleSend}
        onCancel={cancel}
      />
    </div>
  );
}

export function CopilotSidebar() {
  const { isOpen, toggle, close } = useCopilotContext();
  const isMobile = useIsMobile();

  return (
    <CopilotErrorBoundary>
      {/* Desktop: fixed right panel */}
      {isOpen && !isMobile && (
        <aside className="fixed inset-y-0 right-0 z-40 w-[380px] border-l bg-background/95 backdrop-blur-xl supports-[backdrop-filter]:bg-background/80 shadow-lg flex flex-col animate-in slide-in-from-right duration-200">
          <SidebarContent onClose={close} />
        </aside>
      )}

      {/* Mobile: overlay + slide-in drawer */}
      {isOpen && isMobile && (
        <>
          <div
            className="fixed inset-0 z-40 bg-black/40 backdrop-blur-sm animate-in fade-in duration-200"
            onClick={close}
          />
          <aside className="fixed inset-y-0 right-0 z-50 w-[340px] max-w-[90vw] bg-background/95 backdrop-blur-xl supports-[backdrop-filter]:bg-background/80 shadow-xl flex flex-col animate-in slide-in-from-right duration-200">
            <SidebarContent onClose={close} />
          </aside>
        </>
      )}

      {/* Floating toggle button */}
      {!isOpen && (
        <button
          onClick={toggle}
          className="fixed bottom-6 right-6 z-30 flex h-12 w-12 items-center justify-center rounded-full bg-gradient-to-br from-[#0D7377] to-[#095456] text-white shadow-lg shadow-[#0D7377]/25 hover:shadow-xl hover:shadow-[#0D7377]/30 hover:scale-105 active:scale-95 transition-all lg:bottom-8 lg:right-8"
          title="Open SEHRA Copilot"
        >
          <Bot className="h-6 w-6" />
        </button>
      )}
    </CopilotErrorBoundary>
  );
}
