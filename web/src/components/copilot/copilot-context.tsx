"use client";

import {
  createContext,
  useContext,
  useState,
  useCallback,
  useEffect,
  type ReactNode,
} from "react";
import { usePathname } from "next/navigation";
import { useCopilot } from "@/hooks/use-copilot";
import type { CopilotMessage, CopilotAction, StoredConversation } from "@/lib/types";

interface CopilotContextValue {
  isOpen: boolean;
  toggle: () => void;
  open: () => void;
  close: () => void;
  sehraId: string | null;
  setSehraId: (id: string | null) => void;
  sehraLabel: string | null;
  setSehraLabel: (label: string | null) => void;
  messages: CopilotMessage[];
  isStreaming: boolean;
  thinkingText: string | null;
  sendMessage: (content: string) => void;
  executeAction: (action: CopilotAction) => Promise<unknown>;
  cancel: () => void;
  clearMessages: () => void;
  conversationId: string;
  conversations: StoredConversation[];
  conversationsLoading: boolean;
  loadConversation: (id: string) => void;
  removeConversation: (id: string) => void;
  newConversation: () => void;
  setMessageFeedback: (messageId: string, rating: "up" | "down") => void;
  setMessageEdit: (messageId: string, correctedText: string) => void;
}

const CopilotContext = createContext<CopilotContextValue | null>(null);

export function CopilotProvider({ children }: { children: ReactNode }) {
  const [isOpen, setIsOpen] = useState(false);
  const [sehraId, setSehraId] = useState<string | null>(null);
  const [sehraLabel, setSehraLabel] = useState<string | null>(null);
  const pathname = usePathname();
  const copilot = useCopilot();

  // Auto-detect sehraId from /assessments/[id] URL
  useEffect(() => {
    const match = pathname.match(/^\/assessments\/([^/]+)$/);
    if (match) {
      setSehraId(match[1]);
    } else {
      setSehraId(null);
      setSehraLabel(null);
    }
  }, [pathname]);

  // Keep the hook's sehraContext ref in sync with context state
  useEffect(() => {
    copilot.setSehraContext(sehraId, sehraLabel);
  }, [sehraId, sehraLabel, copilot.setSehraContext]);

  const toggle = useCallback(() => setIsOpen((v) => !v), []);
  const open = useCallback(() => setIsOpen(true), []);
  const close = useCallback(() => setIsOpen(false), []);

  const sendMessage = useCallback(
    (content: string) => {
      copilot.sendMessage(content, sehraId, pathname);
    },
    [copilot.sendMessage, sehraId, pathname],
  );

  const newConversation = useCallback(() => {
    copilot.clearMessages();
  }, [copilot.clearMessages]);

  return (
    <CopilotContext.Provider
      value={{
        isOpen,
        toggle,
        open,
        close,
        sehraId,
        setSehraId,
        sehraLabel,
        setSehraLabel,
        messages: copilot.messages,
        isStreaming: copilot.isStreaming,
        thinkingText: copilot.thinkingText,
        sendMessage,
        executeAction: copilot.executeAction,
        cancel: copilot.cancel,
        clearMessages: copilot.clearMessages,
        conversationId: copilot.conversationId,
        conversations: copilot.conversations,
        conversationsLoading: copilot.conversationsLoading,
        loadConversation: copilot.loadConversation,
        removeConversation: copilot.removeConversation,
        newConversation,
        setMessageFeedback: copilot.setMessageFeedback,
        setMessageEdit: copilot.setMessageEdit,
      }}
    >
      {children}
    </CopilotContext.Provider>
  );
}

export function useCopilotContext() {
  const ctx = useContext(CopilotContext);
  if (!ctx) throw new Error("useCopilotContext must be used within CopilotProvider");
  return ctx;
}
