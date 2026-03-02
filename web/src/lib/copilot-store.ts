import { getToken } from "./auth";
import type { CopilotMessage, StoredConversation, ConversationSummary } from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

function authHeaders(): Record<string, string> {
  const token = getToken();
  const headers: Record<string, string> = { "Content-Type": "application/json" };
  if (token) headers["Authorization"] = `Bearer ${token}`;
  return headers;
}

export async function getConversations(): Promise<StoredConversation[]> {
  try {
    const res = await fetch(`${API_BASE}/conversations`, {
      headers: authHeaders(),
    });
    if (!res.ok) return [];
    const data: ConversationSummary[] = await res.json();
    return data.map((c) => ({
      id: c.id,
      title: c.title,
      sehraId: c.sehra_id,
      sehraLabel: c.sehra_label,
      messages: [],
      createdAt: c.created_at,
      updatedAt: c.updated_at,
    }));
  } catch {
    return [];
  }
}

export async function getConversation(id: string): Promise<StoredConversation | null> {
  try {
    const res = await fetch(`${API_BASE}/conversations/${id}`, {
      headers: authHeaders(),
    });
    if (!res.ok) return null;
    const data = await res.json();
    return {
      id: data.id,
      title: data.title,
      sehraId: data.sehra_id,
      sehraLabel: data.sehra_label,
      messages: data.messages || [],
      createdAt: data.created_at,
      updatedAt: data.updated_at,
    };
  } catch {
    return null;
  }
}

export async function saveConversation(
  id: string,
  messages: CopilotMessage[],
  sehraId: string | null,
  sehraLabel: string | null,
): Promise<void> {
  if (messages.length === 0) return;
  const firstUserMsg = messages.find((m) => m.role === "user");
  const title = firstUserMsg
    ? firstUserMsg.content.slice(0, 50)
    : "New conversation";

  try {
    await fetch(`${API_BASE}/conversations`, {
      method: "POST",
      headers: authHeaders(),
      body: JSON.stringify({
        id,
        title,
        messages,
        sehra_id: sehraId,
        sehra_label: sehraLabel,
      }),
    });
  } catch {
    // Silently fail - conversations are non-critical
  }
}

export async function deleteConversation(id: string): Promise<void> {
  try {
    await fetch(`${API_BASE}/conversations/${id}`, {
      method: "DELETE",
      headers: authHeaders(),
    });
  } catch {
    // Silently fail
  }
}

export async function submitFeedback(
  messageId: string,
  conversationId: string | null,
  rating: "up" | "down",
): Promise<void> {
  try {
    await fetch(`${API_BASE}/feedback`, {
      method: "POST",
      headers: authHeaders(),
      body: JSON.stringify({
        message_id: messageId,
        conversation_id: conversationId,
        rating,
        comment: "",
      }),
    });
  } catch {
    // Silently fail
  }
}

export async function submitCorrection(
  originalText: string,
  correctedText: string,
  context: string,
  sehraId: string | null,
  messageId: string | null,
): Promise<void> {
  try {
    await fetch(`${API_BASE}/corrections`, {
      method: "POST",
      headers: authHeaders(),
      body: JSON.stringify({
        original_text: originalText,
        corrected_text: correctedText,
        context,
        sehra_id: sehraId,
        message_id: messageId,
      }),
    });
  } catch {
    // Silently fail
  }
}
