# SEHRA Analyzer: "Claude Code for SEHRA" Research Report

**Date**: March 2, 2026
**Prepared by**: Engineering Team
**Purpose**: Research & analysis for transforming SEHRA Copilot into an intelligent, learning AI assistant

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Product Manager Personality Profile](#2-product-manager-personality-profile)
3. [Current State Analysis & Gaps](#3-current-state-analysis--gaps)
4. [Open Source AI Agent Frameworks](#4-open-source-ai-agent-frameworks)
5. [Architecture: Claude Code for SEHRA](#5-architecture-claude-code-for-sehra)
6. [UI/UX Patterns for AI Copilots](#6-uiux-patterns-for-ai-copilots)
7. [Performance & Speed Optimizations](#7-performance--speed-optimizations)
8. [Export Functionality](#8-export-functionality)
9. [Implementation Roadmap](#9-implementation-roadmap)

---

## 1. Executive Summary

SEHRA Analyzer already has a solid foundation: 13 copilot tools (8 read + 5 write), SSE streaming, conversation persistence, and a feedback/corrections loop. However, **the copilot currently operates as a chatbot, not as an intelligent assistant**. The gap between "chatbot" and "Claude Code for SEHRA" requires:

| Capability | Current | Target |
|---|---|---|
| **Edit confirmation** | No confirmation, silent execution | Human-in-the-loop approval with diff preview |
| **Learning** | Last 10 corrections injected into prompt | Semantic memory with pgvector, per-user preferences |
| **UI feedback** | Tool results hidden in collapsed section | Prominent result cards, before/after display |
| **Page refresh** | Stale data after copilot edits | Auto-refresh with optimistic updates |
| **Inline editing** | Only theme/classification dropdowns | Executive summary, recommendations, report sections |
| **Streaming** | Full response, then display | Token-level streaming (3-5x perceived speed improvement) |
| **Web search** | Not available | External research with citations |
| **Guardrails** | None | Tiered authorization, audit trail, rollback |

**Recommended approach**: Enhance existing FastAPI agent + integrate CopilotKit on frontend. This preserves your working backend while adding professional copilot UI patterns.

---

## 2. Product Manager Personality Profile

### Who: Mahalakshmi ([@mahalakshme](https://github.com/mahalakshme))

Product Manager at Samanvay Research and Development Foundation. Core team member of the Avni project (open-source field service delivery platform). Authored **1,345+ issues** and **857+ issue comments** across the Avni ecosystem. Likely has a ThoughtWorks background based on repo forks and agile practices.

### Communication Style

- **Structured**: Uses consistent "Need / AC (Acceptance Criteria)" format
- **Direct and concise**: No padding, action-oriented language
- **Accountability-focused**: Follows up on progress, pushes back on weak justifications
- **Variable detail**: Rich detail for complex features (screenshots, edge cases, implementation hints), deliberate brevity for tracking stubs
- **Scope-conscious**: Proactively includes "Out of Scope" sections

### What She Values

| Priority | Evidence |
|---|---|
| **User-centricity** | Created epic "Making app intuitive" — product tours, welcome messages, guided tooltips |
| **Documentation** | Persistent push for READMEs, Swagger docs, release blogs with GIFs |
| **Data quality** | Caught encoding issues (curly vs straight apostrophes), demanded idempotency |
| **Proactive maintenance** | "Instead of looking into it after it is reported, we need to look into it ahead" |
| **Accessibility** | Website redesign explicitly listed screen readers, contrast ratios |
| **Cost consciousness** | Estimation requests, awareness of client funding constraints |

### What Would Impress Her

- Clear acceptance criteria and well-structured documentation
- Proactive error handling and failure monitoring (not just happy-path)
- Features that reduce onboarding friction for non-technical users
- AI capabilities that solve practical field problems (not tech demos)
- Visual demos (GIFs, screenshots) showing real-world usage
- Idempotent, safe-to-retry operations
- Evidence of edge case thinking

### What Would Concern Her

- Scope creep without explicit boundaries
- Reactive-only approaches to quality
- Missing or outdated documentation
- Features that work first time but break on edge cases
- Over-engineered solutions when simpler ones exist
- Cost overruns without upfront estimates
- Poor justifications for deprioritization

### Design Implications for SEHRA

1. **Every copilot action must be confirmable and reversible** — she values safety over speed
2. **Show what changed, not just "success"** — she cares about data accuracy details
3. **Document the copilot's capabilities** — in-app help, tooltips, guided first-use
4. **Build for non-technical users** — field workers and analysts, not developers
5. **Track and surface failures** — copilot accuracy metrics dashboard
6. **Keep it simple** — don't over-engineer for 10-20 users

---

## 3. Current State Analysis & Gaps

### What Works

| Component | Status | Details |
|---|---|---|
| Agent loop | Working | 8 rounds, multi-LLM fallback (Groq -> Claude -> GPT-4o) |
| 13 tools | Working | 8 read + 5 write tools, all tested |
| SSE streaming | Working | 7 event types (thinking, tool_call, tool_result, message, chart, actions, done) |
| Conversation persistence | Working | Full history saved to PostgreSQL |
| Corrections loop | Working | Last 10 corrections injected into system prompt |
| Feedback | Working | Thumbs up/down + text corrections |
| Sidebar UI | Working | Desktop panel (380px) + mobile drawer |
| Inline edit (entries) | Working | Theme/classification dropdowns in Analysis tab |
| Exports | Working | DOCX, XLSX, HTML, PDF |

### 14 Critical Gaps Identified

#### UX-Critical (Must Fix)

| # | Gap | Impact |
|---|---|---|
| 1 | **No edit confirmation for write operations** | Users can't see what copilot will change before it executes |
| 2 | **Tool results hidden in collapsed section** | Users don't know what actually changed |
| 3 | **No page refresh after copilot edits** | Stale data displayed after copilot modifies entries |
| 4 | **Executive summary not editable in UI** | Must use copilot chat to edit; no inline edit button |
| 5 | **No undo/rollback for copilot changes** | Accidental bulk approvals can't be reversed |
| 6 | **No impact preview before action execution** | "Approve 10 entries" — which 10? |
| 7 | **Tool results don't show before/after** | Just `{"success": true}` — no diff |

#### Learning & Feedback Gaps

| # | Gap | Impact |
|---|---|---|
| 8 | **No feedback loop for write operations** | System doesn't learn when actions are wrong |
| 9 | **Corrections not tied to specific fields** | Agent can't learn "executive_summary should say X" |
| 10 | **No copilot accuracy metrics** | Can't measure improvement over time |
| 11 | **No user preferences for copilot behavior** | Same behavior for all users |

#### Discoverability Gaps

| # | Gap | Impact |
|---|---|---|
| 12 | **No suggested actions on main assessment page** | Users must open copilot to discover actions |
| 13 | **Copilot context unclear to users** | Don't know when locked to assessment vs global |
| 14 | **Charts not persisted in conversation** | Can't revisit conversation and see visualizations |

---

## 4. Open Source AI Agent Frameworks

### Recommended Stack

Based on scanning [tom-doerr's repo posts](https://tom-doerr.github.io/repo_posts/) and web research across 50+ projects:

| Layer | Project | Stars | Why |
|---|---|---|---|
| **Frontend Copilot** | [CopilotKit](https://github.com/CopilotKit/CopilotKit) | 28K+ | Purpose-built for in-app copilots, React components, human-in-the-loop, generative UI |
| **Core Orchestration** | Existing FastAPI agent | — | Already working; enhance rather than replace |
| **Per-User Memory** | [Hindsight](https://github.com/vectorize-io/hindsight) | ~2K | Retain/Recall/Reflect memory system, learns from corrections, per-user personalization |
| **Web Search** | [Local Deep Research](https://github.com/LearningCircuit/local-deep-research) | ~4.1K | Multi-source search with citations, ~95% accuracy, per-user encrypted DB |
| **Database Tools** | [MCP Toolbox](https://github.com/googleapis/genai-toolbox) | ~13.2K | Google's MCP server for secure database tool calling |
| **Document Processing** | [Docling MCP](https://github.com/docling-project/docling-mcp) | ~477 | PDF parsing, format conversion via MCP |
| **Execution Infrastructure** | [Trigger.dev](https://github.com/triggerdotdev/trigger.dev) | ~13.9K | Long-running tasks, retries, human-in-the-loop approval |
| **Testing & QA** | [Better Agents](https://github.com/langwatch/better-agents) | ~1.5K | Scenario-based testing, prompt versioning, evaluation |

### Framework Comparison for SEHRA

| Framework | Fit | Reasoning |
|---|---|---|
| **CopilotKit** | HIGHEST | Purpose-built for in-app copilots; replaces 350 lines of custom code |
| **Vercel AI SDK 6** | HIGH | Great React integration, tool approval UI; alternative to CopilotKit |
| **Anthropic Claude Agent SDK** | HIGH | Native Claude integration, add as primary provider in fallback chain |
| **LangChain/LangGraph** | MEDIUM | Heavy abstraction for simple agent loop; overkill for current needs |
| **CrewAI / AutoGen** | LOW | Multi-agent; overkill for single-copilot |

### Recommendation

**Don't replace your working backend.** Instead:
1. Add **CopilotKit** on the frontend for professional copilot UI
2. Add **Hindsight** as a memory layer for per-user learning
3. Keep FastAPI agent loop, add token-level streaming
4. Add **Anthropic Claude Agent SDK** as primary LLM provider

---

## 5. Architecture: Claude Code for SEHRA

### Current vs Target Architecture

```
CURRENT:
┌──────────────┐    SSE     ┌─────────────────┐    SQL    ┌──────────┐
│  Next.js UI  │ ────────── │  FastAPI Agent   │ ──────── │ Postgres │
│  (custom)    │            │  (8 rounds)      │          │          │
└──────────────┘            │  Groq/Claude/GPT │          └──────────┘
                            └─────────────────┘

TARGET:
┌──────────────┐   AG-UI    ┌─────────────────┐    SQL    ┌──────────┐
│  CopilotKit  │ ────────── │  FastAPI Agent   │ ──────── │ Postgres │
│  + Custom UI │  protocol  │  + Streaming     │          │ + pgvec  │
│              │            │  + Confirmation  │          └──────────┘
│  - Confirm   │            │  + Audit trail   │
│    dialogs   │            │  + Parallel exec │   REST    ┌──────────┐
│  - Diff view │            │  + Memory layer  │ ──────── │ Hindsight│
│  - Inline    │            │                  │          │ (memory) │
│    edit      │            │  + Web search    │          └──────────┘
│  - Actions   │            │  (Brave/Tavily)  │
│    on page   │            └─────────────────┘
└──────────────┘
```

### Key Design Decisions

#### 1. Human-in-the-Loop (Tiered Authorization)

```
Tier 1 — Auto-execute (no confirmation):
  ├── list_assessments
  ├── get_assessment_details
  ├── get_component_analysis
  ├── get_executive_summary
  ├── search_entries
  ├── compare_assessments
  ├── get_codebook
  └── suggest_actions

Tier 2 — Require confirmation (show diff):
  ├── edit_entry           → Show: "Change theme from X to Y"
  ├── edit_report_section  → Show: before/after text diff
  ├── edit_executive_summary → Show: before/after text diff
  ├── change_status        → Show: "draft → reviewed"
  └── batch_approve        → Show: "Approve N entries above X% confidence"
```

**Implementation**: New SSE event type `confirmation_required`:
```json
{
  "event": "confirmation_required",
  "data": {
    "tool_call_id": "call_abc123",
    "tool_name": "batch_approve",
    "description": "Approve 8 entries above 85% confidence",
    "affected_records": ["entry_1", "entry_2", ...],
    "preview": { "count": 8, "threshold": 0.85 }
  }
}
```

Frontend shows modal → User clicks Approve/Reject → Sends confirmation back → Agent resumes.

#### 2. Memory Architecture

```
┌─────────────────────────────────────────────┐
│              Memory System                   │
├─────────────┬──────────────┬────────────────┤
│  Short-term │  Medium-term │   Long-term    │
│  (current)  │  (enhance)   │   (new)        │
├─────────────┼──────────────┼────────────────┤
│ Conversation│ User correc- │ Semantic memory│
│ history     │ tions with   │ via pgvector   │
│ (per chat)  │ field context │ (per user)     │
│             │              │                │
│ Max 20 msgs │ Per-user     │ Retrieve by    │
│ then        │ preferences  │ similarity to  │
│ summarize   │ ("always     │ current query  │
│             │  confirm     │                │
│             │  bulk ops")  │ "When user     │
│             │              │  asked about   │
│             │              │  infrastructure│
│             │              │  in India,     │
│             │              │  they meant..."│
└─────────────┴──────────────┴────────────────┘
```

#### 3. Audit Trail & Rollback

Every write operation logs:
```sql
CREATE TABLE copilot_audit_log (
  id            UUID PRIMARY KEY,
  sehra_id      UUID REFERENCES sehras(id),
  user_id       UUID REFERENCES users(id),
  tool_name     TEXT NOT NULL,
  args          JSONB NOT NULL,
  old_value     JSONB,        -- snapshot before change
  new_value     JSONB,        -- snapshot after change
  status        TEXT DEFAULT 'applied',  -- applied | rolled_back
  created_at    TIMESTAMPTZ DEFAULT NOW()
);
```

Enables:
- "Show me what copilot changed" → query audit log
- "Undo last batch approval" → rollback from old_value
- "Copilot changed this 5 min ago" → badge on UI

#### 4. Web Search Integration

Add a new tool `search_web` that uses Tavily (purpose-built for LLM agents):
```python
def search_web(query: str, num_results: int = 5) -> dict:
    """Search the web for relevant eye health, SEHRA, or policy information."""
    # Tavily — 1,000 free credits/month, returns LLM-optimized results with citations
    from tavily import TavilyClient
    client = TavilyClient(api_key=settings.tavily_api_key)
    results = client.search(query, max_results=num_results)
    return {"results": [{"title": r["title"], "url": r["url"], "snippet": r["content"]} for r in results["results"]]}
```

**Why Tavily over Brave**: Brave dropped its free tier (now $5/month). Tavily offers 1,000 free credits/month with LLM-optimized output (ranked snippets, relevance scores, citations). Alternative: Serper (2,500 free/month) for raw volume.

This enables:
- "What's the WHO recommendation for school eye screening?" → web search + citation
- "Compare our barriers with global benchmarks" → search + analysis
- "Find recent studies on eye health in Kenya" → contextualized results

---

## 6. UI/UX Patterns for AI Copilots

### Pattern 1: Confirmation Modal (Write Operations)

```
┌─────────────────────────────────────────┐
│  Copilot wants to edit executive summary │
│                                          │
│  ┌─ Current ──────────────────────────┐ │
│  │ The assessment reveals moderate     │ │
│  │ readiness for school eye health...  │ │
│  └────────────────────────────────────┘ │
│                                          │
│  ┌─ Proposed ─────────────────────────┐ │
│  │ The assessment reveals [strong]     │ │
│  │ readiness for school eye health...  │ │
│  └────────────────────────────────────┘ │
│                                          │
│  [Approve]  [Edit & Approve]  [Reject]   │
└─────────────────────────────────────────┘
```

### Pattern 2: Inline Edit with AI Assist

```
┌── Executive Summary ──────────── [Edit] ─┐
│                                           │
│  The assessment reveals moderate          │
│  readiness for school eye health          │
│  programmes in India - Delhi...           │
│                                           │
│  [Ask Copilot to improve] [Save] [Cancel] │
└───────────────────────────────────────────┘
```

### Pattern 3: Result Cards (After Write Operations)

Instead of hiding results in collapsed tool calls:

```
┌─ ✅ Status Changed ──────────────────────┐
│                                           │
│  Assessment: India - Delhi                │
│  Changed:    draft → reviewed             │
│  By:         Copilot (confirmed by you)   │
│  Time:       2 seconds ago                │
│                                           │
│  [Undo]  [View Assessment]                │
└───────────────────────────────────────────┘
```

### Pattern 4: Suggested Actions on Assessment Page

```
┌─ 💡 Copilot Suggestions ────────────────┐
│                                          │
│  • 8 entries ready to approve (>85%)     │
│    [Review & Approve]                    │
│                                          │
│  • Executive summary can be improved     │
│    [Ask Copilot]                         │
│                                          │
│  • Assessment ready for review           │
│    [Change Status]                       │
└──────────────────────────────────────────┘
```

### Pattern 5: Learning Indicator

```
┌─ 🧠 Copilot Memory ────────────────────┐
│                                          │
│  Learned 3 corrections for this          │
│  assessment:                             │
│                                          │
│  • Infrastructure in rural = barrier     │
│  • Training programs = enabler           │
│  • Prefer formal tone in summaries       │
│                                          │
│  [View All]  [Clear Memory]              │
└──────────────────────────────────────────┘
```

---

## 7. Performance & Speed Optimizations

### Critical: Token-Level Streaming

**Current**: Full LLM response generated, then sent as single SSE event (3-10s wait).
**Target**: Stream tokens as they arrive (perceived latency drops to ~200ms).

```python
# copilot_agent.py — change from:
response = client.chat.completions.create(model=model, messages=messages, tools=tools)

# to:
stream = client.chat.completions.create(model=model, messages=messages, tools=tools, stream=True)
for chunk in stream:
    if chunk.choices[0].delta.content:
        yield _sse_event("message_delta", {"text": chunk.choices[0].delta.content})
```

**Impact**: Single highest-impact improvement. Users see response forming in real-time.

### Parallel Read Tool Execution

When LLM requests multiple tools in one turn, execute read tools in parallel:

```python
import asyncio

read_calls = [tc for tc in tool_calls if tc.function.name in READ_TOOLS]
write_calls = [tc for tc in tool_calls if tc.function.name in WRITE_TOOLS]

# Parallel reads (safe, no side effects)
read_results = await asyncio.gather(*[execute_tool(tc) for tc in read_calls])

# Sequential writes (order matters, need confirmation)
for tc in write_calls:
    yield confirmation_event(tc)
    # Wait for user approval...
    result = await execute_tool(tc)
```

### Caching Strategy

| Layer | What | TTL | How |
|---|---|---|---|
| LLM response cache | Identical prompts for same sehra_id | 5 min | Redis or dict keyed on hash(messages + sehra_id) |
| Tool result cache | Assessment details, component analyses | 30s | `@lru_cache` with TTL on read tools |
| Frontend SWR | Assessment data | 30s for published, 5s for draft | Increase SWR dedup window |
| Conversation list | User's conversations | 60s | SWR with revalidateOnFocus |

### Optimistic UI Updates

After copilot confirms an edit:
```typescript
// 1. Update SWR cache immediately
mutate(`/sehras/${sehraId}`, applyEdit(currentData, editDetails), false);
// 2. Revalidate in background
mutate(`/sehras/${sehraId}`);
```

---

## 8. Export Functionality

### Current State (Working)

| Format | Generator | Notes |
|---|---|---|
| DOCX | python-docx + matplotlib | Title page, charts, component sections, appendix |
| XLSX | openpyxl | 7+ sheets, styled, conditional formatting |
| HTML | Jinja2 + Plotly | Interactive charts |
| PDF | WeasyPrint | HTML-to-PDF conversion |
| Share Link | Cached HTML | Passcode-protected, expiring |

### Recommended Enhancements

1. **AI-Audience-Specific Exports**
   ```
   GET /export/{sehra_id}/pdf?audience=policymakers
   GET /export/{sehra_id}/pdf?audience=practitioners
   GET /export/{sehra_id}/pdf?audience=donors
   ```
   Each generates a tailored executive summary and emphasis areas.

2. **Copilot-Triggered Downloads**
   - "Download this assessment as PDF" in copilot → triggers download directly
   - Currently just navigates to export tab

3. **OG Meta Tags for Share Links**
   - Rich previews when shared on WhatsApp/email
   - Critical for health workers in low-resource settings

4. **Offline HTML Export**
   - Self-contained HTML with embedded data and charts
   - No external dependencies, works without internet
   - Important for field settings

---

## 9. Implementation Roadmap

### Phase 1: Foundation Fixes (1-2 weeks)

| Task | Impact | Effort | Files |
|---|---|---|---|
| Token-level streaming | HIGH | LOW | `copilot_agent.py` |
| Confirmation modal for write tools | HIGH | MEDIUM | New SSE event + frontend modal |
| Prominent result cards (before/after) | HIGH | MEDIUM | `copilot-sidebar.tsx` |
| Auto-refresh page after copilot edits | HIGH | LOW | `use-copilot.ts` + SWR mutate |
| Inline edit for executive summary | HIGH | LOW | `report-tab.tsx` |
| Audit log table | MEDIUM | LOW | DB migration + `agent_tools.py` |

### Phase 2: Intelligence Layer (2-4 weeks)

| Task | Impact | Effort | Files |
|---|---|---|---|
| Add pgvector for semantic corrections | MEDIUM | MEDIUM | DB migration + `copilot_agent.py` |
| Web search tool (Tavily API) | HIGH | LOW | New tool in `agent_tools.py` |
| Parallel read tool execution | MEDIUM | LOW | `copilot_agent.py` |
| User preference memory | MEDIUM | MEDIUM | New DB table + settings UI |
| Suggested actions on assessment page | HIGH | MEDIUM | New component on detail page |
| Undo/rollback for copilot changes | HIGH | MEDIUM | Audit log + rollback endpoint |

### Phase 3: Polish & Advanced (4-8 weeks)

| Task | Impact | Effort | Files |
|---|---|---|---|
| CopilotKit or Vercel AI SDK integration | HIGH | HIGH | Replace custom copilot UI |
| Conversation summarization (long threads) | MEDIUM | MEDIUM | `copilot_agent.py` |
| Copilot accuracy metrics dashboard | MEDIUM | HIGH | New admin page |
| AI-audience-specific exports | MEDIUM | MEDIUM | Export endpoints |
| Generative UI (agent renders components) | HIGH | HIGH | CopilotKit integration |
| Offline HTML export | LOW | MEDIUM | `report_html.py` |

### Cost Estimate (for 10-20 users)

| Service | Monthly Cost |
|---|---|
| Groq (primary LLM) | Free tier (100K tokens/day) |
| Claude API (fallback) | ~$5-15/month |
| Tavily Search API | Free (1000 credits/month) |
| Railway (2 services) | ~$10-20/month |
| pgvector (same Postgres) | $0 additional |
| **Total** | **~$15-35/month** |

---

## Sources

### Vercel/AI Frameworks
- [Vercel AI SDK 6](https://vercel.com/blog/ai-sdk-6)
- [CopilotKit](https://github.com/CopilotKit/CopilotKit)
- [Claude Agent SDK](https://github.com/anthropics/claude-agent-sdk-python)

### Architecture & Patterns
- [Pendoah: AI Copilot Architecture Guide](https://pendoah.ai/insights/blog/ai-copilot-architecture-guide/)
- [Microsoft: Agent Architecture Components](https://learn.microsoft.com/en-us/microsoft-copilot-studio/guidance/architecture/components-of-agent-architecture)
- [Auth0: Secure HITL Interactions](https://auth0.com/blog/secure-human-in-the-loop-interactions-for-ai-agents/)

### Open Source Projects
- [Hindsight Memory](https://github.com/vectorize-io/hindsight) — Per-user learning memory
- [Local Deep Research](https://github.com/LearningCircuit/local-deep-research) — Multi-source web search
- [MCP Toolbox](https://github.com/googleapis/genai-toolbox) — Database tool calling
- [Trigger.dev](https://github.com/triggerdotdev/trigger.dev) — Long-running task execution
- [Better Agents](https://github.com/langwatch/better-agents) — Agent testing & evaluation
- [Hermes Agent](https://github.com/NousResearch/hermes-agent) — Skill learning pattern
- [tom-doerr's repo posts](https://tom-doerr.github.io/repo_posts/) — AI project catalog

### UI/UX
- [Microsoft: UX Guidance for Generative AI](https://learn.microsoft.com/en-us/microsoft-cloud/dev/copilot/isv/ux-guidance)
- [Groto: AI Copilot UX Best Practices](https://www.letsgroto.com/blog/mastering-ai-copilot-design)
- [Figr: Copilot as the UI](https://figr.design/blog/copilot-as-the-ui)

### Performance
- [Speeding Up AI Agents](https://mbrenndoerfer.com/writing/speeding-up-ai-agents-performance-optimization)
- [Hierarchical Caching for Agentic Workflows](https://www.mdpi.com/2504-4990/8/2/30)

### PM Profile
- [GitHub: mahalakshme](https://github.com/mahalakshme)
- [Avni Project Issues](https://github.com/avniproject/) — 1,345+ authored issues
