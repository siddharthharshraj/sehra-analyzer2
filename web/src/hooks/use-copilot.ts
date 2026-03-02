"use client";

import { useState, useCallback, useRef, useEffect } from "react";
import { getToken } from "@/lib/auth";
import { apiPost, apiPatch, apiGet, apiDownload } from "@/lib/api-client";
import {
  getConversations,
  getConversation,
  saveConversation,
  deleteConversation as deleteConversationApi,
  submitFeedback,
  submitCorrection,
} from "@/lib/copilot-store";
import type {
  CopilotMessage,
  CopilotSSEEvent,
  CopilotAction,
  ChartSpec,
  CopilotToolCall,
  StoredConversation,
} from "@/lib/types";

const API_BASE =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

let messageIdCounter = 0;
function nextId() {
  return `msg-${++messageIdCounter}-${Date.now()}`;
}

function newConversationId() {
  if (typeof crypto !== "undefined" && crypto.randomUUID) {
    return crypto.randomUUID();
  }
  return `conv-${Date.now()}-${Math.random().toString(36).slice(2, 9)}`;
}

export function useCopilot() {
  const [messages, setMessages] = useState<CopilotMessage[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [thinkingText, setThinkingText] = useState<string | null>(null);
  const [conversationId, setConversationId] = useState<string>(newConversationId);
  const [conversations, setConversations] = useState<StoredConversation[]>([]);
  const [conversationsLoading, setConversationsLoading] = useState(true);
  const controllerRef = useRef<AbortController | null>(null);
  const sehraContextRef = useRef<{ sehraId: string | null; sehraLabel: string | null }>({
    sehraId: null,
    sehraLabel: null,
  });
  const prevStreamingRef = useRef(false);

  // Load conversation list on mount via API
  useEffect(() => {
    setConversationsLoading(true);
    getConversations()
      .then(setConversations)
      .finally(() => setConversationsLoading(false));
  }, []);

  // Persist when streaming completes (true -> false transition)
  useEffect(() => {
    if (prevStreamingRef.current && !isStreaming && messages.length > 0) {
      saveConversation(
        conversationId,
        messages,
        sehraContextRef.current.sehraId,
        sehraContextRef.current.sehraLabel,
      ).then(() => {
        getConversations().then(setConversations);
      });
    }
    prevStreamingRef.current = isStreaming;
  }, [isStreaming, messages, conversationId]);

  const setSehraContext = useCallback(
    (sehraId: string | null, sehraLabel: string | null) => {
      sehraContextRef.current = { sehraId, sehraLabel };
    },
    [],
  );

  const sendMessage = useCallback(
    async (
      content: string,
      sehraId: string | null,
      pageContext: string | null,
    ) => {
      const userMsg: CopilotMessage = {
        id: nextId(),
        role: "user",
        content,
        status: "done",
      };
      const assistantId = nextId();
      const assistantMsg: CopilotMessage = {
        id: assistantId,
        role: "assistant",
        content: "",
        tool_calls: [],
        status: "streaming",
      };

      setMessages((prev) => [...prev, userMsg, assistantMsg]);
      setIsStreaming(true);
      setThinkingText(null);

      const allMessages = [
        ...messages
          .filter((m) => m.role === "user" || (m.role === "assistant" && m.content))
          .map((m) => ({ role: m.role, content: m.content })),
        { role: "user" as const, content },
      ];

      const controller = new AbortController();
      controllerRef.current = controller;

      try {
        const token = getToken();
        const headers: Record<string, string> = {
          "Content-Type": "application/json",
        };
        if (token) headers["Authorization"] = `Bearer ${token}`;

        const res = await fetch(`${API_BASE}/agent/chat`, {
          method: "POST",
          headers,
          body: JSON.stringify({
            messages: allMessages,
            sehra_id: sehraId,
            page_context: pageContext,
          }),
          signal: controller.signal,
        });

        if (!res.ok) {
          throw new Error(`SSE failed: ${res.status}`);
        }

        const reader = res.body?.getReader();
        if (!reader) return;

        const decoder = new TextDecoder();
        let buffer = "";
        const toolCalls: CopilotToolCall[] = [];
        let finalText = "";
        let chartSpec: ChartSpec | null = null;
        let actions: CopilotAction[] = [];

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split("\n");
          buffer = lines.pop() || "";

          for (const line of lines) {
            const trimmed = line.trim();
            if (!trimmed || trimmed.startsWith(":")) continue;
            if (!trimmed.startsWith("data:")) continue;

            const jsonStr = trimmed.slice(5).trim();
            if (!jsonStr) continue;

            let event: CopilotSSEEvent;
            try {
              event = JSON.parse(jsonStr);
            } catch {
              continue;
            }

            switch (event.type) {
              case "thinking":
                setThinkingText(event.text || "Thinking...");
                break;

              case "tool_call":
                toolCalls.push({
                  tool: event.tool || "",
                  arguments: event.arguments || {},
                  status: "running",
                });
                updateAssistant(assistantId, { tool_calls: [...toolCalls] });
                break;

              case "tool_result":
                for (let i = toolCalls.length - 1; i >= 0; i--) {
                  if (toolCalls[i].tool === event.tool && toolCalls[i].status === "running") {
                    toolCalls[i].status = "done";
                    toolCalls[i].result_preview = event.preview;
                    break;
                  }
                }
                updateAssistant(assistantId, { tool_calls: [...toolCalls] });
                break;

              case "message":
                finalText = event.text || "";
                setThinkingText(null);
                updateAssistant(assistantId, { content: finalText });
                break;

              case "chart":
                chartSpec = event.spec || null;
                updateAssistant(assistantId, { chart: chartSpec });
                break;

              case "actions":
                actions = event.actions || [];
                updateAssistant(assistantId, { actions });
                break;

              case "error":
                updateAssistant(assistantId, {
                  content: `Error: ${event.text}`,
                  status: "error",
                });
                break;

              case "done":
                updateAssistant(assistantId, { status: "done" });
                break;
            }
          }
        }
      } catch (err) {
        if ((err as Error).name !== "AbortError") {
          updateAssistant(assistantId, {
            content: `Error: ${err instanceof Error ? err.message : "Unknown error"}`,
            status: "error",
          });
        }
      } finally {
        setIsStreaming(false);
        setThinkingText(null);
        controllerRef.current = null;
      }
    },
    [messages],
  );

  function updateAssistant(id: string, updates: Partial<CopilotMessage>) {
    setMessages((prev) =>
      prev.map((m) => (m.id === id ? { ...m, ...updates } : m)),
    );
  }

  const executeAction = useCallback(async (action: CopilotAction) => {
    const { method, path, body, download } = action.api_call;
    try {
      if (download) {
        const filename = path.split("/").pop() || "export";
        await apiDownload(path, filename);
        return { success: true };
      }
      switch (method) {
        case "POST":
          return await apiPost(path, body);
        case "PATCH":
          return await apiPatch(path, body);
        case "GET":
          return await apiGet(path);
        default:
          return await apiPost(path, body);
      }
    } catch (err) {
      throw err;
    }
  }, []);

  const cancel = useCallback(() => {
    controllerRef.current?.abort();
    setIsStreaming(false);
    setThinkingText(null);
  }, []);

  const clearMessages = useCallback(() => {
    setMessages([]);
    setConversationId(newConversationId());
  }, []);

  const loadConversation = useCallback(async (id: string) => {
    const convo = await getConversation(id);
    if (convo) {
      setConversationId(convo.id);
      setMessages(convo.messages);
    }
  }, []);

  const removeConversation = useCallback(
    async (id: string) => {
      await deleteConversationApi(id);
      const updated = await getConversations();
      setConversations(updated);
      if (id === conversationId) {
        setMessages([]);
        setConversationId(newConversationId());
      }
    },
    [conversationId],
  );

  const setMessageFeedback = useCallback(
    (messageId: string, rating: "up" | "down") => {
      setMessages((prev) =>
        prev.map((m) =>
          m.id === messageId ? { ...m, feedback: m.feedback === rating ? null : rating } : m,
        ),
      );
      submitFeedback(messageId, conversationId, rating);
    },
    [conversationId],
  );

  const setMessageEdit = useCallback(
    (messageId: string, correctedText: string) => {
      setMessages((prev) =>
        prev.map((m) => {
          if (m.id !== messageId) return m;
          submitCorrection(
            m.content,
            correctedText,
            "copilot_message",
            sehraContextRef.current.sehraId,
            messageId,
          );
          return { ...m, edited: true, editedContent: correctedText };
        }),
      );
    },
    [],
  );

  return {
    messages,
    isStreaming,
    thinkingText,
    conversationId,
    conversations,
    conversationsLoading,
    sendMessage,
    executeAction,
    cancel,
    clearMessages,
    loadConversation,
    removeConversation,
    setSehraContext,
    setMessageFeedback,
    setMessageEdit,
  };
}
