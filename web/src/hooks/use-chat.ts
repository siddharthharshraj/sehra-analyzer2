"use client";

import { useState, useCallback } from "react";
import { apiPost } from "@/lib/api-client";
import type { ChatResponse, ChartSpec } from "@/lib/types";

interface ChatMessage {
  role: "user" | "assistant";
  text: string;
  chart?: ChartSpec | null;
}

export function useChat() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  const sendMessage = useCallback(
    async (question: string, sehraId: string) => {
      setMessages((prev) => [...prev, { role: "user", text: question }]);
      setIsLoading(true);

      try {
        const res = await apiPost<ChatResponse>("/chat", {
          question,
          sehra_id: sehraId,
        });
        setMessages((prev) => [
          ...prev,
          { role: "assistant", text: res.text, chart: res.chart_spec },
        ]);
      } catch (err) {
        setMessages((prev) => [
          ...prev,
          {
            role: "assistant",
            text: `Error: ${err instanceof Error ? err.message : "Unknown error"}`,
          },
        ]);
      } finally {
        setIsLoading(false);
      }
    },
    [],
  );

  const clearMessages = useCallback(() => {
    setMessages([]);
  }, []);

  return { messages, isLoading, sendMessage, clearMessages };
}
