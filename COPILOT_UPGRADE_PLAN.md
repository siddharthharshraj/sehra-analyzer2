# SEHRA Copilot Upgrade Plan: "Claude Code for SEHRA"

**Date**: March 2, 2026
**Status**: Planned
**Scope**: Transform copilot from basic chatbot → intelligent, learning AI assistant

---

## Table of Contents

- [1. Free LLM Providers](#1-free-llm-providers)
- [2. What We're Building](#2-what-were-building)
- [3. Phase 1: Backend Changes](#3-phase-1-backend-changes)
- [4. Phase 2: Frontend Changes](#4-phase-2-frontend-changes)
- [5. Phase 3: Testing](#5-phase-3-testing)
- [6. File Change Summary](#6-file-change-summary)
- [7. Dependency Additions](#7-dependency-additions)

---

## 1. Free LLM Providers

### Comparison (with Tool Calling Support)

| Rank | Provider | Free Tier | Tool Calling | Speed | Best Model |
|------|----------|-----------|--------------|-------|------------|
| 1 | **Google Gemini** | 250K TPM, 250 RPD (Flash) | Yes | ~245 t/s | Gemini 2.5 Flash |
| 2 | **Cerebras** | 1M tokens/day, 30 RPM | Yes | ~2,600 t/s | Llama 4 Scout |
| 3 | **Groq** (current) | 100K-500K TPD | Yes | ~300 t/s | Llama 4 Scout (500K TPD) |
| 4 | **SambaNova** | 200K tokens/day, 10-30 RPM | Yes | Very fast | Llama 3.3 70B |
| 5 | **Mistral** | 1B tokens/month, **2 RPM** | Yes | Good | Mistral Small 3.2 |

### Recommended Fallback Chain

```
Primary:   Cerebras  (1M TPD, fastest inference at 2,600 t/s)
Secondary: Google Gemini Flash  (250 RPD, best quality-to-cost ratio)
Tertiary:  Groq Llama 4 Scout  (500K TPD, current provider)
```

- **Combined budget**: ~1.75M+ tokens/day free, tool calling on all three
- **All use OpenAI-compatible APIs** — minimal integration effort
- **Mistral excluded** — 2 RPM makes it unusable for interactive chat despite massive token budget

---

## 2. What We're Building

Transform the copilot from a basic chatbot into an intelligent assistant that:

| # | Capability | Current State | Target State |
|---|------------|---------------|--------------|
| 1 | Edit confirmation | No confirmation, silent execution | Human-in-the-loop approval with diff preview |
| 2 | Past conversations | Can view history, but no context resume | Load past conversation → agent has full context → continue chatting |
| 3 | Learning | Last 10 corrections injected into prompt | Semantic memory, per-user preferences, field-specific corrections |
| 4 | Web search | Not available | Tavily-powered search with citations |
| 5 | UI feedback | Tool results hidden in collapsed section | Prominent result cards with before/after display |
| 6 | Page refresh | Stale data after copilot edits | Auto-refresh with optimistic updates |
| 7 | Inline editing | Only theme/classification dropdowns | Executive summary, recommendations, report sections |
| 8 | LLM providers | Groq only (100K TPD limit) | Cerebras → Gemini → Groq auto-failover (1.75M+ TPD) |
| 9 | Streaming | Full response then display | Token-level streaming (3-5x perceived speed improvement) |
| 10 | Audit trail | None | Full audit log with undo/rollback capability |

---

## 3. Phase 1: Backend Changes

### 3.1 `api/config.py` — New Settings

Add provider API keys and Tavily config:

```python
cerebras_api_key: str = ""
gemini_api_key: str = ""
tavily_api_key: str = ""
sambanova_api_key: str = ""  # optional
```

### 3.2 `api/core/copilot_agent.py` — Major Rewrite

**Multi-provider failover:**
- Try Cerebras → Gemini → Groq → OpenAI
- Catch rate limit errors (429) and automatically fallback to next provider
- Each provider uses OpenAI-compatible client with different `base_url`

**Token-level streaming:**
```python
# BEFORE (blocking):
response = client.chat.completions.create(model=model, messages=messages, tools=tools)

# AFTER (streaming):
stream = client.chat.completions.create(model=model, messages=messages, tools=tools, stream=True)
for chunk in stream:
    if chunk.choices[0].delta.content:
        yield _sse_event("message_delta", {"text": chunk.choices[0].delta.content})
```

**Confirmation flow for write tools:**
- When LLM calls a write tool, yield `confirmation_required` SSE event instead of executing
- Include: tool name, args, human-readable description, affected records preview
- Wait for follow-up request with `confirmed_tool_call_id` to resume execution

**Conversation context loading:**
- Accept optional `conversation_id` parameter
- If provided, load prior messages from DB and prepend to message history
- Agent gets full context from past chats when user resumes a conversation

**Web search integration:**
- Add Tavily as a callable tool within the agent loop

### 3.3 `api/core/agent_tools.py` — Enhancements

**New tool — `search_web`:**
```python
def search_web(query: str, num_results: int = 5) -> dict:
    """Search the web for relevant eye health, SEHRA, or policy information."""
    from tavily import TavilyClient
    client = TavilyClient(api_key=settings.tavily_api_key)
    results = client.search(query, max_results=num_results)
    return {
        "results": [
            {"title": r["title"], "url": r["url"], "snippet": r["content"]}
            for r in results["results"]
        ]
    }
```

**Better tool results (before/after):**
- `edit_entry` → returns `{"success": true, "old_theme": "X", "new_theme": "Y", "old_classification": "A", "new_classification": "B"}`
- `edit_executive_summary` → returns `{"success": true, "old_summary": "...", "new_summary": "..."}`
- `change_status` → returns `{"success": true, "old_status": "draft", "new_status": "reviewed"}`

**Classify tools:**
```python
WRITE_TOOLS = {"edit_entry", "edit_report_section", "edit_executive_summary", "change_status", "batch_approve"}
READ_TOOLS = {all others}
```

### 3.4 `api/routers/agent.py` — Confirmation Endpoint

Add to `AgentChatRequest`:
```python
conversation_id: Optional[str] = None
confirmed_tool_call_id: Optional[str] = None
confirmed_args: Optional[dict] = None
```

- When `confirmed_tool_call_id` is present, execute the pending tool and return result
- Cache pending tool calls in memory (dict keyed by tool_call_id)

### 3.5 `api/core/db.py` — Audit Log

**New table:**
```sql
CREATE TABLE copilot_audit_log (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sehra_id      UUID REFERENCES sehras(id),
    user_id       TEXT NOT NULL,
    tool_name     TEXT NOT NULL,
    args          JSONB NOT NULL,
    old_value     JSONB,
    new_value     JSONB,
    status        TEXT DEFAULT 'applied',  -- applied | rolled_back
    created_at    TIMESTAMPTZ DEFAULT NOW()
);
```

**New functions:**
- `log_copilot_action(sehra_id, user, tool_name, args, old_value, new_value)` — Record every write
- `get_audit_log(sehra_id)` — Retrieve audit history
- `rollback_action(audit_id)` — Restore old_value, mark as rolled_back

**Modify existing functions** to return old values:
- `update_qualitative_entry()` → return old theme/classification before update
- `update_sehra_status()` → return old status before update
- `update_report_section()` → return old content before update

### 3.6 `api/routers/conversations.py` — Resume Support

Add endpoint:
```
PATCH /conversations/{id}  — Append messages to existing conversation
```

---

## 4. Phase 2: Frontend Changes

### 4.1 `web/src/hooks/use-copilot.ts` — Major Enhancements

**Token-level streaming:**
- Handle new SSE event `message_delta` — append text to current assistant message incrementally
- Users see response forming word by word (~200ms perceived latency vs 3-10s)

**Confirmation flow:**
- Handle `confirmation_required` SSE event → set `pendingConfirmation` state
- New function: `confirmAction(toolCallId: string, approved: boolean)` → sends confirmation back to backend
- On approval, backend executes tool and streams result

**Conversation resume:**
- When `loadConversation(id)` is called, set `conversationId` in state
- On next `sendMessage`, pass `conversation_id` to backend
- Agent receives full prior message history → understands context

**Page refresh trigger:**
- Accept `onDataChanged?: () => void` callback
- Call it after every confirmed write operation completes
- Assessment page passes `mutateSehra()` + `mutateComponents()` as the callback

### 4.2 `web/src/components/copilot/copilot-sidebar.tsx` — UI Additions

**Confirmation Modal:**
```
┌─────────────────────────────────────────────┐
│  Copilot wants to edit executive summary     │
│                                              │
│  ┌─ Current ──────────────────────────────┐ │
│  │ The assessment reveals moderate         │ │
│  │ readiness for school eye health...      │ │
│  └────────────────────────────────────────┘ │
│                                              │
│  ┌─ Proposed ─────────────────────────────┐ │
│  │ The assessment reveals strong           │ │
│  │ readiness for school eye health...      │ │
│  └────────────────────────────────────────┘ │
│                                              │
│  [Approve]    [Edit & Approve]    [Reject]   │
└─────────────────────────────────────────────┘
```

**Streaming text display:**
- Show text as it arrives token by token (not after full response)
- Blinking cursor indicator while streaming

**Result cards (after confirmed writes):**
```
┌─ ✅ Status Changed ──────────────────────────┐
│                                               │
│  Assessment:  India - Delhi                   │
│  Changed:     draft → reviewed                │
│  By:          Copilot (confirmed by you)      │
│  Time:        2 seconds ago                   │
│                                               │
│  [Undo]  [View Assessment]                    │
└───────────────────────────────────────────────┘
```

**Conversation resume indicator:**
- When loading past conversation, show banner: "Continuing from: [title]"
- Agent has full context from the prior conversation

**Context indicator:**
- Clear label: "Locked to: India - Delhi" or "Global mode"

### 4.3 `web/src/components/assessments/report-tab.tsx` — Inline Editing

- **Edit button** on Executive Summary card → opens modal textarea
- **Edit button** on Recommendations card → opens modal textarea
- **"Ask Copilot to improve"** button → sends prompt to copilot sidebar
- **Save** calls `PATCH /sehras/{id}` with updated text
- Auto-refresh after save

### 4.4 `web/src/app/(app)/assessments/[id]/page.tsx` — Integration

- Pass `mutateSehra()` + `mutateComponents()` as refresh callbacks to copilot context
- After copilot write operations complete, page data auto-refreshes

### 4.5 `web/src/components/copilot/copilot-context.tsx` — New State

- `pendingConfirmation` state and setter
- `confirmAction()` function
- `onDataChanged` callback propagation to hook

### 4.6 `web/src/lib/types.ts` — New Types

```typescript
interface ConfirmationRequest {
    toolCallId: string;
    toolName: string;
    description: string;
    affectedRecords?: string[];
    preview?: { oldValue?: string; newValue?: string; count?: number };
}

interface AuditLogEntry {
    id: string;
    sehraId: string;
    toolName: string;
    oldValue: Record<string, unknown>;
    newValue: Record<string, unknown>;
    status: "applied" | "rolled_back";
    createdAt: string;
}
```

---

## 5. Phase 3: Testing

### 5.1 Backend Tests (pytest)

| Test | What It Validates |
|------|-------------------|
| Multi-provider failover | Mock rate limit on Cerebras → verify Gemini called → mock rate limit → verify Groq called |
| Confirmation flow | Send write tool request → verify `confirmation_required` SSE event → send confirmation → verify tool executed |
| Conversation context loading | Create conversation with 5 messages → resume → verify agent sees all 5 in context |
| Web search tool | Mock Tavily API → verify results format with titles, URLs, snippets |
| Audit log | Execute write tool → verify audit log entry created → rollback → verify old value restored |
| Before/after in tool results | Execute `edit_executive_summary` → verify response contains old and new values |
| Token-level streaming | Verify `message_delta` events emitted during streaming response |

### 5.2 Frontend Tests (Playwright)

| Test | What It Validates |
|------|-------------------|
| Confirmation modal | Trigger write operation → modal appears → shows before/after diff |
| Approve flow | Click Approve → tool executes → result card shown → page data refreshes |
| Reject flow | Click Reject → tool not executed → agent acknowledges rejection |
| Token streaming | Send message → text appears incrementally (not all at once) |
| Conversation resume | Load old conversation → send new message → verify agent references prior context |
| Inline edit summary | Click Edit on executive summary → modal opens → edit → save → verify update |
| Page auto-refresh | Copilot changes status → assessment page badge updates without manual refresh |
| Undo button | After write operation → click Undo → verify rollback |

### 5.3 E2E Integration Tests

| Test | Full Flow |
|------|-----------|
| Complete edit cycle | Upload → Analyze → Copilot edits summary → Confirm → Verify change in DB + UI → Export PDF → Verify new summary in export |
| Conversation persistence | Chat → Close → Reopen → Load conversation → Continue chatting → Agent remembers context |
| Multi-provider failover E2E | Exhaust Cerebras quota → verify seamless switch to Gemini mid-conversation |
| Web search in context | Ask "WHO recommendations for school eye screening" → verify Tavily called → results cited in response |

---

## 6. File Change Summary

| File | Action | Est. Lines Changed |
|------|--------|-------------------|
| `api/config.py` | Edit | +10 |
| `api/core/copilot_agent.py` | Major rewrite | ~300 (rewrite 230 → 350) |
| `api/core/agent_tools.py` | Edit | +80 |
| `api/routers/agent.py` | Edit | +40 |
| `api/routers/conversations.py` | Edit | +15 |
| `api/core/db.py` | Edit | +60 |
| `web/src/hooks/use-copilot.ts` | Edit | +100 |
| `web/src/components/copilot/copilot-sidebar.tsx` | Major edit | +200 |
| `web/src/components/copilot/copilot-context.tsx` | Edit | +30 |
| `web/src/components/assessments/report-tab.tsx` | Edit | +80 |
| `web/src/app/(app)/assessments/[id]/page.tsx` | Edit | +15 |
| `web/src/lib/types.ts` | Edit | +20 |
| `tests/test_copilot_backend.py` | New | ~400 |
| `tests/test_copilot_ui.py` | New | ~300 |
| **Total** | | **~1,350 lines** |

---

## 7. Dependency Additions

### Backend (`requirements.txt`)

```
tavily-python        # Web search API (1,000 free credits/month)
cerebras-cloud-sdk   # Cerebras inference (1M tokens/day free)
google-genai         # Gemini API (250 RPD free, OpenAI-compatible)
```

### Frontend (`package.json`)

No new dependencies — using existing shadcn/ui components for modals and dialogs.

---

## Cost Estimate (10-20 Users)

| Service | Monthly Cost |
|---------|-------------|
| Cerebras (primary LLM) | Free (1M tokens/day) |
| Gemini Flash (secondary LLM) | Free (250 RPD) |
| Groq (tertiary LLM) | Free (500K TPD) |
| Tavily (web search) | Free (1,000 credits/month) |
| Railway (2 services) | ~$10-20/month |
| PostgreSQL (same instance) | $0 additional |
| **Total** | **~$10-20/month** |
