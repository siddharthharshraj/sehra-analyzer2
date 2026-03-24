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
  ConfirmationRequest,
  ToolResultCard,
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

/** Parse tool_result events into rich result cards */
function buildToolResultCard(
  tool: string,
  preview: string | undefined,
  args: Record<string, unknown>,
): ToolResultCard {
  const base: ToolResultCard = {
    tool,
    success: true,
    summary: preview || `${tool} completed`,
  };

  switch (tool) {
    case "edit_entry":
      base.summary = "Entry Updated";
      base.details = {};
      if (args.theme) base.details["Theme"] = String(args.theme);
      if (args.classification) base.details["Classification"] = String(args.classification);
      if (args.sehra_id) base.details["Assessment"] = String(args.sehra_id);
      break;
    case "change_status":
      base.summary = "Status Changed";
      base.details = {};
      if (args.new_status) base.details["New Status"] = String(args.new_status);
      if (args.sehra_id) base.details["Assessment"] = String(args.sehra_id);
      break;
    case "batch_approve":
      base.summary = `Batch Approved${args.count ? ` (${args.count} entries)` : ""}`;
      base.details = {};
      if (args.count) base.details["Count"] = String(args.count);
      if (args.threshold) base.details["Threshold"] = `${args.threshold}%`;
      break;
    case "edit_executive_summary":
      base.summary = "Executive Summary Updated";
      base.details = {};
      if (preview) base.details["Preview"] = preview.slice(0, 120);
      break;
  }

  return base;
}

export function useCopilot() {
  const [messages, setMessages] = useState<CopilotMessage[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [thinkingText, setThinkingText] = useState<string | null>(null);
  const [pendingConfirmation, setPendingConfirmation] = useState<ConfirmationRequest | null>(null);
  const [conversationId, setConversationId] = useState<string>(newConversationId);
  const [conversations, setConversations] = useState<StoredConversation[]>([]);
  const [conversationsLoading, setConversationsLoading] = useState(true);
  const controllerRef = useRef<AbortController | null>(null);
  const sehraContextRef = useRef<{ sehraId: string | null; sehraLabel: string | null }>({
    sehraId: null,
    sehraLabel: null,
  });
  const prevStreamingRef = useRef(false);
  const onDataChangedRef = useRef<(() => void) | null>(null);

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

  const setOnDataChanged = useCallback((cb: (() => void) | null) => {
    onDataChangedRef.current = cb;
  }, []);

  function updateAssistant(id: string, updates: Partial<CopilotMessage>) {
    setMessages((prev) =>
      prev.map((m) => (m.id === id ? { ...m, ...updates } : m)),
    );
  }

  /** Shared SSE stream reader for both sendMessage and confirmAction */
  async function readSSEStream(
    res: Response,
    assistantId: string,
  ) {
    const reader = res.body?.getReader();
    if (!reader) return;

    const decoder = new TextDecoder();
    let buffer = "";
    const toolCalls: CopilotToolCall[] = [];
    const toolResults: ToolResultCard[] = [];
    let finalText = "";
    let chartSpec: ChartSpec | null = null;
    let actions: CopilotAction[] = [];
    let hadWriteOperation = false;

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

          case "tool_result": {
            // Mark the tool call as done
            for (let i = toolCalls.length - 1; i >= 0; i--) {
              if (toolCalls[i].tool === event.tool && toolCalls[i].status === "running") {
                toolCalls[i].status = "done";
                toolCalls[i].result_preview = event.preview;
                break;
              }
            }
            // Build a result card for write operations
            const writableTools = ["edit_entry", "change_status", "batch_approve", "edit_executive_summary"];
            if (event.tool && writableTools.includes(event.tool)) {
              hadWriteOperation = true;
              const matchingCall = toolCalls.find((tc) => tc.tool === event.tool);
              const card = buildToolResultCard(
                event.tool,
                event.preview,
                matchingCall?.arguments || {},
              );
              toolResults.push(card);
              updateAssistant(assistantId, {
                tool_calls: [...toolCalls],
                tool_results: [...toolResults],
              });
            } else {
              updateAssistant(assistantId, { tool_calls: [...toolCalls] });
            }
            break;
          }

          case "message_delta":
            // Token-level streaming: append text incrementally
            setThinkingText(null);
            setMessages((prev) => {
              const idx = prev.findIndex((m) => m.id === assistantId);
              if (idx === -1) return prev;
              const current = prev[idx];
              return [
                ...prev.slice(0, idx),
                { ...current, content: current.content + (event.text || "") },
                ...prev.slice(idx + 1),
              ];
            });
            break;

          case "message":
            finalText = event.text || "";
            setThinkingText(null);
            updateAssistant(assistantId, { content: finalText });
            break;

          case "confirmation_required":
            // Server is requesting user confirmation before proceeding
            setPendingConfirmation({
              toolCallId: event.tool_call_id || "",
              toolName: event.tool || "",
              description: event.description || "Confirm this action?",
              args: event.arguments || {},
              preview: event.confirmation_preview,
            });
            updateAssistant(assistantId, {
              confirmation: {
                toolCallId: event.tool_call_id || "",
                toolName: event.tool || "",
                description: event.description || "Confirm this action?",
                args: event.arguments || {},
                preview: event.confirmation_preview,
              },
            });
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
            // Trigger data refresh if write operations occurred
            if (hadWriteOperation && onDataChangedRef.current) {
              onDataChangedRef.current();
            }
            break;
        }
      }
    }
  }

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
        tool_results: [],
        status: "streaming",
      };

      setMessages((prev) => [...prev, userMsg, assistantMsg]);
      setIsStreaming(true);
      setThinkingText(null);
      setPendingConfirmation(null);

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

        await readSSEStream(res, assistantId);
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

  /** Confirm a pending tool call (approve or reject) */
  const confirmAction = useCallback(
    async (toolCallId: string, approved: boolean) => {
      setPendingConfirmation(null);

      if (!approved) {
        // Add a system-like message noting rejection
        const rejectMsg: CopilotMessage = {
          id: nextId(),
          role: "assistant",
          content: "Action cancelled by user.",
          status: "done",
        };
        setMessages((prev) => [...prev, rejectMsg]);
        return;
      }

      // Create a new streaming assistant message for the confirmation response
      const assistantId = nextId();
      const assistantMsg: CopilotMessage = {
        id: assistantId,
        role: "assistant",
        content: "",
        tool_calls: [],
        tool_results: [],
        status: "streaming",
      };
      setMessages((prev) => [...prev, assistantMsg]);
      setIsStreaming(true);
      setThinkingText("Executing confirmed action...");

      const controller = new AbortController();
      controllerRef.current = controller;

      try {
        const token = getToken();
        const headers: Record<string, string> = {
          "Content-Type": "application/json",
        };
        if (token) headers["Authorization"] = `Bearer ${token}`;

        const allMessages = messages
          .filter((m) => m.role === "user" || (m.role === "assistant" && m.content))
          .map((m) => ({ role: m.role, content: m.content }));

        const res = await fetch(`${API_BASE}/agent/chat`, {
          method: "POST",
          headers,
          body: JSON.stringify({
            messages: allMessages,
            sehra_id: sehraContextRef.current.sehraId,
            confirmed_tool_call_id: toolCallId,
          }),
          signal: controller.signal,
        });

        if (!res.ok) {
          throw new Error(`Confirmation failed: ${res.status}`);
        }

        await readSSEStream(res, assistantId);
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

  const executeAction = useCallback(async (action: CopilotAction) => {
    const { method, path, body, download } = action.api_call;
    try {
      let result: unknown;
      if (download) {
        const filename = path.split("/").pop() || "export";
        await apiDownload(path, filename);
        result = { success: true };
      } else {
        switch (method) {
          case "POST":
            result = await apiPost(path, body);
            break;
          case "PATCH":
            result = await apiPatch(path, body);
            break;
          case "GET":
            result = await apiGet(path);
            break;
          default:
            result = await apiPost(path, body);
        }
      }
      // Trigger data refresh after action
      if (onDataChangedRef.current) {
        onDataChangedRef.current();
      }
      return result;
    } catch (err) {
      throw err;
    }
  }, []);

  const cancel = useCallback(() => {
    controllerRef.current?.abort();
    setIsStreaming(false);
    setThinkingText(null);
    setPendingConfirmation(null);
  }, []);

  const clearMessages = useCallback(() => {
    setMessages([]);
    setConversationId(newConversationId());
    setPendingConfirmation(null);
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
    pendingConfirmation,
    conversationId,
    conversations,
    conversationsLoading,
    sendMessage,
    confirmAction,
    executeAction,
    cancel,
    clearMessages,
    loadConversation,
    removeConversation,
    setSehraContext,
    setOnDataChanged,
    setMessageFeedback,
    setMessageEdit,
  };
}
