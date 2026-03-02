# SEHRA Analyzer — Architecture Document

> School Eye Health Rapid Assessment analysis platform built for PRASHO Foundation by Samanvay Foundation.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **Frontend** | Next.js 16 (App Router), React 19, TypeScript, Tailwind CSS, Shadcn/ui |
| **Data fetching** | SWR (stale-while-revalidate) |
| **Backend** | FastAPI (Python 3.11+), Uvicorn ASGI |
| **Database** | PostgreSQL, SQLAlchemy 2.0 ORM |
| **AI/LLM** | Groq (llama-3.3-70b), Anthropic Claude, OpenAI GPT-4o — multi-provider fallback chain |
| **PDF parsing** | PyMuPDF (fitz), pymupdf4llm |
| **Report gen** | python-docx, openpyxl, Jinja2, WeasyPrint, matplotlib, Plotly |
| **Auth** | JWT (HS256, 24h), bcrypt |
| **Realtime** | Server-Sent Events (SSE) via sse-starlette |
| **Conversations** | Server-side PostgreSQL persistence + feedback + corrections |

---

## Architectural Decisions

> Every technology choice involves trade-offs. This section documents **why** each decision was made in the context of SEHRA — an AI-powered analytics tool used by health analysts in low-resource settings.

### 1. Why Python (Not Java)?

Python was the right choice for this project:

| Factor | Python (chosen) | Java (alternative) |
|--------|----------------|-------------------|
| **AI/LLM integration** | Native SDKs (OpenAI, Anthropic, Groq) are Python-first. 3 lines to call an LLM. | Requires community wrappers, more boilerplate |
| **PDF parsing** | PyMuPDF, pymupdf4llm, Surya OCR — all Python-native | Apache PDFBox exists but weaker for AI-ready extraction |
| **Data science** | Pandas, Plotly, Matplotlib, NumPy — first-class | No equivalent ecosystem |
| **Rapid prototyping** | Streamlit → working app in days. FastAPI → production API in hours | Spring Boot = weeks for equivalent |
| **Team velocity** | ~3x less code for same functionality | More ceremony, annotations, build tooling |
| **Deployment** | Single `pip install`, 11-line Dockerfile | JVM warmup, larger images, more memory |

**Java would make sense if:** You needed enterprise-grade concurrency (10K+ concurrent users), strict type safety across a 50-person team, or had an existing Java microservices ecosystem. For an AI-powered analytics tool used by health analysts? Python is unquestionably the right call.

### 2. Why FastAPI (Not Django or Flask)?

| Factor | FastAPI (chosen) | Django | Flask |
|--------|-----------------|--------|-------|
| **Async support** | Native `async/await`, perfect for SSE streams and LLM calls | Bolt-on via ASGI, Django Channels adds complexity | Requires Quart or gevent hacks |
| **SSE streaming** | `EventSourceResponse` + async generators = trivial | Needs Channels + Redis for real-time | No built-in support |
| **Auto docs** | Swagger UI + ReDoc from type hints, zero config | DRF has it but heavier setup | Flask-RESTx, extra dep |
| **Pydantic validation** | Built-in, validates every request/response | Serializers (DRF) — similar but more verbose | Manual or marshmallow |
| **Performance** | Among fastest Python frameworks (Starlette + Uvicorn) | Heavier ORM, middleware stack | Comparable, but less tooling |
| **Learning curve** | Minimal — reads like annotated Python functions | Large surface area, opinionated | Simple but fewer batteries |

**Django would make sense if:** You needed its admin panel, built-in auth system, or ORM migrations out of the box. For an API-first platform with SSE streaming to an AI copilot, FastAPI's async-native design is a much better fit.

### 3. Why Next.js (Not Create React App or Vite+React)?

| Factor | Next.js (chosen) | CRA / Vite+React |
|--------|-----------------|-------------------|
| **App Router** | File-based routing, layouts, loading states — no react-router config | Manual routing setup, no conventions |
| **SSR/SSG** | Hybrid rendering per-page. Share page is SSR for SEO + OG tags | Client-only, bad for share link previews |
| **Middleware** | Auth redirect in `middleware.ts` — runs at edge, before render | No equivalent; guard logic scattered in components |
| **Image optimization** | Built-in `next/image` with lazy loading, format conversion | Manual optimization or extra packages |
| **Dynamic imports** | `next/dynamic` with SSR toggle — critical for chart libraries | React.lazy works but no SSR control |
| **Production build** | `next build` → optimized chunks, tree-shaking, static export if needed | Vite is fast but less opinionated on deployment |
| **TypeScript** | First-class, zero config | Same with Vite, CRA needs `--template typescript` |

**CRA/Vite would make sense if:** You were building a pure SPA with no server-side rendering needs and wanted maximum build speed during development. For a platform with public share pages (needs SSR for previews), auth middleware, and complex routing, Next.js is the right framework.

### 4. Why PostgreSQL (Not MongoDB)?

| Factor | PostgreSQL (chosen) | MongoDB |
|--------|-------------------|---------|
| **Relational integrity** | SEHRA → Components → Entries → Sections: strict FK cascades | Document nesting works, but no referential integrity |
| **JSON support** | `items` column uses native JSONB — best of both worlds | Native document store, but overkill here |
| **Aggregation** | SQL aggregates (COUNT, GROUP BY) for enabler/barrier counts | Aggregation pipeline is powerful but verbose |
| **Full-text search** | `tsvector` available if needed for entry search | Better text search out of the box |
| **Tooling** | SQLAlchemy 2.0, Alembic migrations, mature ecosystem | Motor/pymongo, less ORM support |
| **Hosting** | Available everywhere: Docker, RDS, Supabase, Neon | Atlas is good but adds vendor lock-in |
| **ACID compliance** | Full transactions — critical when saving multi-table analysis results | Eventual consistency by default |

**MongoDB would make sense if:** Your data was truly unstructured (varying schemas per document), you needed horizontal sharding at scale, or you were doing heavy geospatial queries. SEHRA data is inherently relational (assessments have components, components have entries) — PostgreSQL models this perfectly.

### 5. Why SSE (Not WebSockets)?

| Factor | SSE (chosen) | WebSockets |
|--------|-------------|------------|
| **Directionality** | Server → Client only. Perfect for analysis progress + copilot streaming | Bidirectional — overkill for our use case |
| **Protocol** | Standard HTTP. Works through proxies, CDNs, and load balancers | Requires upgrade handshake, some proxies block |
| **Reconnection** | Built-in auto-reconnect with `EventSource` API | Manual reconnect logic needed |
| **Implementation** | `sse-starlette` + `async yield` = 5 lines | WebSocket handler + connection manager + ping/pong |
| **Browser support** | Native `EventSource` API, zero dependencies | Native `WebSocket` API, also zero dependencies |
| **Load balancers** | HTTP/2 multiplexing works out of the box | Sticky sessions or Redis pub/sub needed |
| **Caching/debugging** | Standard HTTP — curl, browser DevTools, request logging | Binary frames, needs specialized tools |

**WebSockets would make sense if:** You needed real-time bidirectional communication (collaborative editing, chat between users, gaming). For streaming AI responses and analysis progress updates (server → client only), SSE is simpler, more reliable, and easier to debug.

### 6. Why Multi-LLM Fallback (Not Single Provider)?

| Factor | Multi-LLM fallback (chosen) | Single provider (e.g. OpenAI only) |
|--------|---------------------------|-----------------------------------|
| **Availability** | If Groq is down, Claude handles it. If Claude is down, GPT-4o. Zero downtime | Single point of failure — one outage blocks all AI features |
| **Cost optimization** | Groq free tier for development. Claude/GPT-4o for production quality | Locked into one pricing model |
| **Rate limits** | Exhaust one provider's limits → automatic fallback to next | Hit rate limit = all AI features stop |
| **Regional compliance** | Choose providers based on data residency requirements | Limited to one provider's regions |
| **Quality hedging** | Different models excel at different tasks | Stuck with one model's strengths and weaknesses |
| **Implementation cost** | ~30 lines of fallback logic in `ai_engine.py` | Slightly simpler, but fragile |

**Single provider makes sense if:** You have an enterprise agreement with guaranteed SLAs, or the model quality difference matters significantly for your use case. For a health analytics tool where uptime matters more than model-specific nuance, multi-LLM resilience is the safer bet.

### 7. Why SWR (Not React Query or Redux)?

| Factor | SWR (chosen) | React Query (TanStack) | Redux + RTK Query |
|--------|-------------|----------------------|-------------------|
| **Bundle size** | ~4KB gzipped | ~13KB gzipped | ~30KB+ with toolkit |
| **API simplicity** | `useSWR(key, fetcher)` — one hook | `useQuery({queryKey, queryFn})` — similar but more options | createApi, slices, store setup — significant boilerplate |
| **Stale-while-revalidate** | Core philosophy, built-in | Supported, similarly good | Configurable but not the default mental model |
| **Mutation support** | `mutate()` for optimistic updates | `useMutation` — more structured | RTK Query mutations — most structured but verbose |
| **Cache invalidation** | `mutate(key)` — simple key-based | `queryClient.invalidateQueries` — similar | Tag-based invalidation — powerful but complex |
| **SSR support** | Next.js integration via `SWRConfig` | Hydration support, slightly more setup | Requires custom hydration |
| **Learning curve** | Minimal — works like `useState` with caching | Moderate — more concepts (query keys, stale time) | Steep — actions, reducers, middleware, selectors |

**React Query would make sense if:** You had complex mutation workflows (optimistic updates with rollback) or needed built-in devtools. **Redux makes sense if:** You have extensive client-side state beyond server cache. For a data-display-heavy analytics platform where most state is server data, SWR's simplicity is a perfect match.

### 8. Why PyMuPDF (Not Tabula or pdfplumber)?

| Factor | PyMuPDF/fitz (chosen) | Tabula | pdfplumber |
|--------|---------------------|--------|------------|
| **Widget extraction** | Native form widget API — reads checkboxes, radio buttons, text fields directly | Table extraction only — no widget support | Can extract form fields but less robust |
| **Performance** | C-based (MuPDF engine), fastest Python PDF lib | Java bridge (tabula-java), JVM startup overhead | Pure Python, slower on large documents |
| **Checkbox reading** | `widget.field_type_string == "CheckBox"` — direct access | Cannot read checkboxes | Limited checkbox support |
| **Text positioning** | Precise bounding box coordinates for spatial matching | Table-grid detection only | Good text positioning, but slower |
| **Dependencies** | Single C extension, pip install | Requires Java runtime | Pure Python, no external deps |
| **SEHRA PDF structure** | Form-fillable PDFs with widget pairs → perfect match | Designed for tabular PDFs | Better for text-heavy PDFs |

**Tabula makes sense for:** Extracting data from table-heavy PDFs (financial reports, invoices). **pdfplumber makes sense for:** Text extraction from complex layouts. SEHRA PDFs are form-fillable with checkbox widgets — PyMuPDF's native widget API is the only tool that handles this elegantly.

### 9. Why JWT (Not Server-Side Sessions)?

| Factor | JWT (chosen) | Server-side sessions |
|--------|-------------|---------------------|
| **Stateless** | Token contains all auth data. No session store needed | Requires Redis/DB for session storage |
| **Scaling** | Any backend instance can verify — no shared state | Session affinity or shared store needed |
| **Frontend storage** | Cookie + localStorage. Works with SWR fetch wrapper | Cookie-only, similar |
| **API friendliness** | `Authorization: Bearer <token>` — standard for REST APIs | Session cookies work but less explicit |
| **Implementation** | 40 lines in `auth.py` (create + decode) | Session middleware + store + cleanup |
| **Expiry** | Built into token (24h). `exp` claim, self-validating | Server-controlled, more flexible |
| **Revocation** | Harder — requires blacklist for immediate revocation | Easy — delete session from store |

**Sessions would make sense if:** You needed instant revocation (e.g., "log out all devices now") or had sensitive operations requiring server-controlled session lifetime. For a small-team analytics platform with 24h token expiry, JWT keeps the architecture simple and stateless.

### 10. Why Monolith (Not Microservices)?

| Factor | Monolith (chosen) | Microservices |
|--------|-------------------|---------------|
| **Deployment** | Single Docker container, `docker compose up` | Multiple containers, orchestration (K8s), service mesh |
| **Development** | One repo, one language, shared types | Multi-repo or monorepo, API contracts, versioning |
| **Debugging** | Single process, single log stream, step-through debugging | Distributed tracing, log aggregation, correlation IDs |
| **Data consistency** | Single DB, ACID transactions across all operations | Saga patterns, eventual consistency, distributed transactions |
| **Team size** | 1-5 developers — a monolith is faster for everyone | 10+ teams — independent deployment matters |
| **Latency** | Function calls between modules (nanoseconds) | Network calls between services (milliseconds + serialization) |
| **Operational cost** | One server, one DB, one monitoring dashboard | Multiple servers, service discovery, health checks per service |

**Microservices would make sense if:** You had 10+ teams needing independent deploy cycles, or individual components (PDF parsing, AI engine, export) needed to scale independently. For a focused analytics platform with a small team, a well-structured monolith (FastAPI with clear module boundaries) delivers the same code organization without the distributed systems tax.

---

```
┌──────────────────────────────────────────────────────────────┐
│                      Next.js Frontend                        │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌─────────────┐ │
│  │Assessments│  │ Upload   │  │ Collect  │  │   Admin     │ │
│  │  [id]     │  │ (PDF)    │  │ (Form)   │  │ (Codebook)  │ │
│  ├──────────┤  └────┬─────┘  └────┬─────┘  └─────────────┘ │
│  │Overview  │       │             │                          │
│  │Report    │       │ SSE         │ SSE                      │
│  │Analysis  │       │             │                          │
│  │Export    │       ▼             ▼                          │
│  └──────────┘  ┌─────────────────────┐   ┌───────────────┐ │
│                │   SWR Cache Layer    │   │Copilot Sidebar│ │
│                └──────────┬──────────┘   └───────┬───────┘ │
└───────────────────────────┼──────────────────────┼─────────┘
                            │ REST + SSE           │ SSE
                            ▼                      ▼
┌──────────────────────────────────────────────────────────────┐
│                    FastAPI Backend (/api/v1)                  │
│                                                              │
│  ┌────────┐ ┌────────┐ ┌──────────┐ ┌────────┐ ┌─────────┐│
│  │  auth  │ │ sehras │ │ analysis │ │ export │ │  agent  ││
│  │ (JWT)  │ │ (CRUD) │ │ (SSE AI) │ │ (docs) │ │(copilot)││
│  └────────┘ └────────┘ └────┬─────┘ └───┬────┘ └────┬────┘│
│                             │            │           │      │
│  ┌──────────────────────────┴────────────┴───────────┴───┐ │
│  │                     Core Services                      │ │
│  │  pdf_parser ─→ ai_engine ─→ report_gen                │ │
│  │                copilot_agent + agent_tools             │ │
│  │                chat_agent + charts                     │ │
│  └───────────────────────────┬───────────────────────────┘ │
│                              │                              │
│  ┌───────────────────────────┴───────────────────────────┐ │
│  │              PostgreSQL (SQLAlchemy ORM)               │ │
│  └───────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────┘
```

---

## Database Schema

```
┌──────────────────────┐
│       sehras         │
├──────────────────────┤
│ id          (PK, UUID)│
│ country     (String)  │
│ province    (String)  │
│ district    (String)  │
│ assessment_date (Date)│
│ upload_date (DateTime)│
│ status      (String)  │  ← draft | reviewed | published
│ pdf_filename(String)  │
│ raw_extracted_data(JSON)│
│ executive_summary(Text)│
│ recommendations  (Text)│
└──────┬───────────────┘
       │ 1:N
       ▼
┌──────────────────────────┐
│   component_analyses     │
├──────────────────────────┤
│ id            (PK, UUID) │
│ sehra_id      (FK)       │
│ component     (String)   │  ← context|policy|service_delivery|human_resources|supply_chain|barriers
│ enabler_count (Int)      │
│ barrier_count (Int)      │
│ items         (JSON[])   │  ← [{question, item_id, yes_no, remark, score, is_reverse}]
│ numeric_data  (JSON)     │
└──────┬───────┬───────────┘
       │       │
       │ 1:N   │ 1:N
       ▼       ▼
┌──────────────────┐  ┌──────────────────┐
│qualitative_entries│  │ report_sections  │
├──────────────────┤  ├──────────────────┤
│ id         (UUID)│  │ id         (UUID)│
│ comp_analysis_id │  │ comp_analysis_id │
│ remark_text(Text)│  │ section_type     │  ← enabler_summary|barrier_summary|action_points
│ item_id  (String)│  │ content    (Text)│
│ theme    (String)│  │ edited_by_human  │
│ classification   │  └──────────────────┘
│ confidence(Float)│
│ edited_by_human  │
└──────────────────┘

┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐
│      users       │  │  shared_reports  │  │   report_views   │
├──────────────────┤  ├──────────────────┤  ├──────────────────┤
│ id         (UUID)│  │ id         (UUID)│  │ id         (UUID)│
│ username (unique)│  │ sehra_id   (FK)  │  │ shared_report_id │
│ name     (String)│  │ share_token      │  │ viewed_at        │
│ password_hash    │  │ passcode_hash    │  │ viewer_ip        │
│ role             │  │ created_by       │  │ viewer_user_agent│
│  analyst | admin │  │ created_at       │  │ passcode_correct │
└──────────────────┘  │ expires_at       │  └──────────────────┘
                      │ is_active        │
┌──────────────────┐  │ cached_html(Text)│
│   form_drafts    │  └──────────────────┘
├──────────────────┤
│ id, user         │  ┌──────────────────┐
│ section_progress │  │ codebook_override│
│ responses (JSON) │  ├──────────────────┤
│ created/updated  │  │ id = "current"   │
└──────────────────┘  │ data (JSON)      │
                      └──────────────────┘

┌──────────────────────┐  ┌──────────────────┐  ┌──────────────────┐
│    conversations     │  │   ai_feedback    │  │  ai_corrections  │
├──────────────────────┤  ├──────────────────┤  ├──────────────────┤
│ id         (PK)      │  │ id       (UUID)  │  │ id       (UUID)  │
│ user       (String)  │  │ message_id       │  │ user     (String)│
│ title      (String)  │  │ conversation_id  │  │ original_text    │
│ messages   (JSON[])  │  │ rating (up/down) │  │ corrected_text   │
│ sehra_id   (FK, opt) │  │ comment  (Text)  │  │ context  (String)│
│ created_at           │  │ user     (String)│  │ sehra_id (FK,opt)│
│ updated_at           │  │ created_at       │  │ message_id       │
└──────────────────────┘  └──────────────────┘  │ created_at       │
                                                 └──────────────────┘
```

**Cascade deletes**: Deleting a SEHRA cascades to components → entries + sections, and to shared_reports → views.

---

## Data Flow: PDF Upload → Analysis

```
User drops PDF
      │
      ▼
POST /analyze/upload (SSE stream, 10 steps)
      │
      ├─ Step 1: Validate PDF (size, format, ≥40 pages)
      ├─ Step 2: Parse document (PyMuPDF widget extraction)
      │          ├─ extract_header_from_form_fields() → country, district, date
      │          └─ extract_checkbox_pairs() → yes/no per codebook item
      ├─ Step 3: Score items (match to codebook, apply reverse scoring)
      ├─ Step 4: AI analysis per component
      │          ├─ Classify remarks → theme + classification + confidence
      │          ├─ Generate enabler_summary, barrier_summary
      │          └─ Generate action_points
      ├─ Steps 5-7: Save to DB (SEHRA + components + entries + sections)
      ├─ Step 8: Generate executive_summary (AI)
      ├─ Step 9: Generate recommendations (AI)
      └─ Step 10: Complete event → {sehra_id, enabler_count, barrier_count}
```

**PDF Parser strategy**: Widget-first extraction. SEHRA PDFs are form-fillable — checkbox widgets give yes/no answers, nearby text blocks give question labels, free-text fields give qualitative remarks. Each checkbox pair is matched to codebook items using fuzzy text matching.

**Component page ranges**: Context (pp 10-15), Policy (16-20), Service Delivery (21-26), HR (27-30), Supply Chain (31-35), Barriers (36-41).

---

## AI Engine

Multi-LLM with automatic fallback:

```
GROQ_API_KEY set?  ──yes──→  Groq (llama-3.3-70b-versatile)  [fastest, free tier]
       │ no
ANTHROPIC_API_KEY? ──yes──→  Claude (Anthropic)
       │ no
OPENAI_API_KEY?    ──yes──→  GPT-4o (OpenAI)
```

### AI operations

| Operation | Input | Output | Used in |
|-----------|-------|--------|---------|
| **classify_remarks** | Component remarks + codebook context | `{theme, classification, confidence}` per remark | Analysis pipeline step 4 |
| **generate_summary** | Classified enabler/barrier entries | Enabler summary, barrier summary text | Analysis pipeline step 4 |
| **generate_action_points** | Barrier entries + context | Actionable recommendations per component | Analysis pipeline step 4 |
| **generate_executive_summary** | All component data | High-level assessment overview | Analysis pipeline step 8 |
| **generate_recommendations** | Full analysis results | Strategic recommendations | Analysis pipeline step 9 |

All AI responses are validated against Pydantic models (`ClassificationResult`, `SummaryResult`, `ComponentAnalysisResponse`) before storage.

### 11 cross-cutting themes

Infrastructure, Funding, Training, Policy, Community, Technology, Human Resources, Supply Chain, Governance, Access, Quality, Other.

### Classifications

`enabler` | `barrier` | `strength` | `weakness` | `neutral`

---

## Copilot (AI Assistant)

Agentic chat with function calling, streamed via SSE. The copilot can both **read** and **write** assessment data — like an IDE agent (Cursor, Lovable) but for health analytics.

```
User message
      │
      ▼
POST /agent/chat (SSE stream)
      │
      ├─ System prompt (SEHRA domain context + available tools + user corrections)
      ├─ LLM decides: respond or call tool
      │     │
      │     ├─ Tool call → execute → feed result back → LLM continues
      │     │   (max 8 tool rounds per conversation)
      │     │
      │     └─ Direct response → stream message + optional chart + actions
      │
      ▼
SSE events: thinking → tool_call → tool_result → message/chart/actions → done
```

### Read tools

| Tool | Description |
|------|-------------|
| `list_assessments` | List all SEHRA assessments |
| `get_assessment_details` | Full details for one SEHRA |
| `get_component_analysis` | Component-level breakdown |
| `get_executive_summary` | Summary + recommendations |
| `search_entries` | Filter by theme/classification/confidence/text |
| `compare_assessments` | Side-by-side comparison of two SEHRAs |
| `get_codebook` | Codebook questions by section |
| `suggest_actions` | Context-aware next steps |

### Write tools (agent can directly edit data)

| Tool | Description |
|------|-------------|
| `edit_entry` | Change a qualitative entry's theme and/or classification |
| `edit_report_section` | Rewrite a report section's content |
| `edit_executive_summary` | Update executive summary and/or recommendations |
| `change_status` | Transition assessment status (draft → reviewed → published) |
| `batch_approve` | Approve all entries above a confidence threshold |

### Conversation persistence

Conversations are persisted **server-side** in PostgreSQL (not just localStorage):

```
POST   /conversations          → Save conversation (messages + sehra_id)
GET    /conversations          → List user's conversations
GET    /conversations/{id}     → Retrieve full conversation with messages
DELETE /conversations/{id}     → Delete conversation
```

### Feedback & corrections learning loop

Users can provide feedback on individual AI messages and submit corrections when the copilot makes mistakes. Corrections are **injected into the system prompt** so the agent learns from past edits:

```
POST   /feedback               → Thumbs up/down on a message
POST   /corrections            → "X should be Y" correction
GET    /corrections            → Retrieve corrections (filterable by sehra_id)

System prompt injection:
  Previous user corrections (learn from these and apply similar fixes):
  - "Infrastructure is an enabler" → "Infrastructure is a barrier in rural areas"
  - "Training rate is 45%" → "Training rate is 59%"
```

| Endpoint | Purpose |
|----------|---------|
| `POST /feedback` | Rate individual AI messages (up/down) with optional comment |
| `POST /corrections` | Submit "original → corrected" pairs with context |
| System prompt | Last 10 corrections auto-injected into agent context per session |

---

## Export Formats

All export endpoints: `GET /export/{sehra_id}/{format}` → `StreamingResponse`

| Format | Generator | Content |
|--------|-----------|---------|
| **DOCX** | python-docx + matplotlib | Title page, executive summary, methodology, radar chart, overall bar chart, theme heatmap, per-component sections (enabler/barrier tables grouped by theme, bar charts, action points), recommendations, appendix of all remarks |
| **XLSX** | openpyxl | 7+ sheets: Summary (KPIs + exec summary), Component Scores (readiness %), Theme Analysis (pivot), per-component detail sheets, All Remarks. Styled headers, conditional formatting, frozen panes |
| **HTML** | Jinja2 + Plotly | Self-contained HTML with interactive Plotly charts, per-component breakdown, appendix |
| **PDF** | WeasyPrint (HTML→PDF) | A4 print-optimized version of HTML report |

All exports include metadata: generation timestamp (IST), exporter username, requester IP.

Lazy imports — matplotlib, docx, openpyxl, weasyprint only loaded when the specific format is requested.

---

## Frontend Architecture

### Route Structure

```
/                          → redirect to /assessments
/login                     → JWT login
/assessments               → Grid of assessment cards with enabler rate bars
/assessments/[id]          → Tabbed detail view (Overview | Report | Analysis | Export)
/upload                    → PDF drag-and-drop + SSE progress
/collect                   → 6-step wizard form + auto-save drafts
/admin                     → Codebook question management
/share/[token]             → Public passcode-protected report viewer
/settings                  → User settings
```

### Key Patterns

- **Assessment detail tabs**: Overview (KPI cards + radar/bar charts), Report (executive summary + recommendations from `sehra` prop), Analysis (review controls + component tabs with structured summary cards), Export (format cards with loading states + share links)
- **Dynamic imports**: Charts, ComponentTabs, CopilotSidebar loaded lazily to reduce initial bundle
- **SWR config**: 5s dedup, no refetch on focus, 2 retries, keep previous data
- **Copilot context**: Auto-detects `sehraId` from URL, syncs with copilot hook

### Component Hierarchy (Assessment Detail)

```
AssessmentDetailPage
  ├─ OverviewTab
  │    ├─ KPICards (enablers, barriers, rate, components)
  │    ├─ EnablerRadarChart (dynamic, ssr:false)
  │    └─ EnablerBarrierChart (dynamic, ssr:false)
  ├─ ReportTab
  │    ├─ Executive Summary card
  │    ├─ Recommendations card
  │    └─ Download buttons (DOCX, PDF)
  ├─ AnalysisTab
  │    ├─ ReviewControls (batch approve, status workflow)
  │    └─ ComponentTabs (dynamic)
  │         └─ Per component:
  │              ├─ Enabler/Barrier count pills
  │              ├─ Enabler Summary card (teal accent)
  │              ├─ Barrier Summary card (red accent)
  │              ├─ Action Points card (bulleted list)
  │              └─ Qualitative Entries table (editable theme/classification)
  └─ ExportTab
       ├─ FormatCards (DOCX/XLSX/PDF/HTML with loading states)
       ├─ ShareForm (passcode + expiry)
       └─ ShareLinksTable (copy/revoke)
```

---

## API Reference

```
AUTH
  POST   /auth/login                   → TokenResponse
  POST   /auth/refresh                 → TokenResponse
  POST   /auth/change-password

SEHRAS
  GET    /sehras                       → SEHRASummary[]
  GET    /sehras/{id}                  → SEHRADetail
  DELETE /sehras/{id}
  PATCH  /sehras/{id}/status           → SEHRADetail
  GET    /sehras/{id}/components       → ComponentAnalysis[]
  GET    /sehras/{id}/summary          → {executive_summary, recommendations}
  POST   /sehras/{id}/batch-approve    → {approved_count}

ANALYSIS (SSE)
  POST   /analyze/upload               → EventSource (10 steps)
  POST   /analyze/form                 → EventSource (8 steps)

EXPORT
  GET    /export/{id}/docx             → StreamingResponse
  GET    /export/{id}/xlsx             → StreamingResponse
  GET    /export/{id}/html             → StreamingResponse
  GET    /export/{id}/pdf              → StreamingResponse

COPILOT (SSE)
  POST   /agent/chat                   → EventSource (tool calling, read + write tools)

CONVERSATIONS
  POST   /conversations                → Save conversation
  GET    /conversations                → List user's conversations
  GET    /conversations/{id}           → Retrieve conversation
  DELETE /conversations/{id}           → Delete conversation

FEEDBACK & CORRECTIONS
  POST   /feedback                     → Rate AI message (up/down)
  POST   /corrections                  → Submit correction
  GET    /corrections                  → List corrections (filter by sehra_id)

CHAT
  POST   /chat                         → {text, chart_spec}

SHARE
  POST   /shares                       → ShareLink
  GET    /shares/{sehra_id}            → ShareLink[]
  DELETE /shares/{token}
  GET    /public/share/{token}         → {valid, expired}  (no auth)
  POST   /public/share/{token}/verify  → {success, html}   (no auth)

CODEBOOK (admin)
  GET    /codebook/sections            → string[]
  GET    /codebook/items?section=      → CodebookItem[]
  POST   /codebook/items
  PATCH  /codebook/items/{id}
  DELETE /codebook/items/{id}

DRAFTS
  GET    /drafts                       → FormDraft | null
  PUT    /drafts                       → FormDraft
  DELETE /drafts

ENTRIES
  PATCH  /entries/{id}                 → {theme?, classification?}
  PATCH  /sections/{id}               → {content}
```

All endpoints (except `/public/*` and `/health`) require `Authorization: Bearer <JWT>`.

---

## Security

| Area | Implementation |
|------|---------------|
| **Authentication** | JWT HS256, 24h expiry, cookie `sehra_token` |
| **Password storage** | bcrypt with salt |
| **Role-based access** | `analyst` (default) and `admin` (codebook management) |
| **Route protection** | Next.js middleware checks cookie on all `/app` routes |
| **Share links** | `secrets.token_urlsafe(32)`, bcrypt passcode, optional expiry |
| **Rate limiting** | 5 failed passcode attempts per 60 min → HTTP 429 |
| **Audit trail** | Share views logged: IP, user-agent, timestamp, passcode correctness |
| **CORS** | Configurable origins via `CORS_ORIGINS` env var |
| **Compression** | GZip on responses > 500 bytes |

---

## Performance

| Technique | Detail |
|-----------|--------|
| **SWR dedup** | 5s dedup interval, keeps previous data during revalidation |
| **Cache headers** | SEHRA list: `max-age=10, stale-while-revalidate=30`; Codebook: `max-age=60` |
| **Lazy imports** | Export generators only imported on demand (matplotlib, docx, openpyxl, weasyprint) |
| **Dynamic imports** | Charts, ComponentTabs, CopilotSidebar loaded via `next/dynamic` |
| **Streaming** | Analysis + copilot use SSE (non-blocking); exports use `StreamingResponse` |
| **GZip middleware** | All responses > 500 bytes compressed |
| **DB pooling** | SQLAlchemy `pool_pre_ping=True` |
| **Settings cache** | `@lru_cache` on `get_settings()` |
| **HTML caching** | Share links pre-generate and cache the HTML report at creation time |

---

## Environment Variables

```env
DATABASE_URL=postgresql://user:pass@host:5432/sehra_db
JWT_SECRET=<random-secret>
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=1440
CORS_ORIGINS=http://localhost:3000
GROQ_API_KEY=<optional>
ANTHROPIC_API_KEY=<optional>
OPENAI_API_KEY=<optional>
LOG_LEVEL=INFO
APP_URL=http://localhost:3000
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
```

---

## Review Workflow

```
  ┌───────┐       ┌──────────┐       ┌───────────┐
  │ Draft │──────→│ Reviewed │──────→│ Published │
  └───────┘       └──────────┘       └───────────┘
      ▲               │                    │
      └───────────────┴────────────────────┘
                  (revert to draft)
```

1. PDF uploaded or form submitted → status = `draft`
2. Analyst reviews AI classifications (edit theme/classification inline)
3. Batch approve entries above confidence threshold
4. Mark as `reviewed` → `published`
5. Can revert to `draft` at any time

---

## File Structure

```
sehra-analyzer/
├── api/
│   ├── main.py                    FastAPI app, middleware, router mount
│   ├── config.py                  Settings from .env
│   ├── auth.py                    JWT create/decode
│   ├── deps.py                    Auth dependency injection
│   ├── schemas.py                 Pydantic request/response models
│   ├── routers/
│   │   ├── auth.py                Login, refresh, change password
│   │   ├── sehras.py              SEHRA CRUD, batch approve, entries/sections
│   │   ├── analysis.py            SSE upload + form analysis pipelines
│   │   ├── export.py              DOCX/XLSX/HTML/PDF export
│   │   ├── agent.py               Copilot SSE chat (read + write tools)
│   │   ├── conversations.py       Conversation persistence, feedback, corrections
│   │   ├── chat.py                Simple chat with charts
│   │   ├── share.py               Share link management
│   │   ├── codebook.py            Codebook admin
│   │   └── drafts.py              Form draft save/load
│   └── core/
│       ├── db.py                  ORM models + database operations
│       ├── ai_engine.py           Multi-LLM analysis engine
│       ├── pdf_parser.py          PyMuPDF widget extraction
│       ├── copilot_agent.py       Agentic loop with tool calling
│       ├── agent_tools.py         Tool schemas + implementations
│       ├── chat_agent.py          Chat with chart generation
│       ├── charts.py              Plotly + matplotlib chart builders
│       ├── report_gen.py          DOCX report generator
│       ├── report_xlsx.py         XLSX report generator
│       ├── report_html.py         HTML report generator (Jinja2)
│       └── report_pdf.py          PDF report generator (WeasyPrint)
├── web/
│   └── src/
│       ├── app/
│       │   ├── layout.tsx         Root layout (SWR provider, Toaster)
│       │   ├── (app)/layout.tsx   App layout (Sidebar, Header, CopilotProvider)
│       │   ├── (app)/assessments/ Assessment list + [id] detail page
│       │   ├── (app)/upload/      PDF upload page
│       │   ├── (app)/collect/     Form wizard page
│       │   ├── (app)/admin/       Codebook management
│       │   ├── (auth)/login/      Login page
│       │   └── share/[token]/     Public share viewer
│       ├── components/
│       │   ├── assessments/       Tab components (overview, report, analysis, export)
│       │   ├── dashboard/         KPI cards, charts, component tabs, review controls
│       │   ├── copilot/           AI sidebar, context provider, chart renderer
│       │   ├── export/            Format cards, share form/table
│       │   ├── upload/            PDF dropzone, analysis progress
│       │   ├── collect/           Wizard stepper, header/section forms
│       │   ├── layout/            Sidebar, header
│       │   └── ui/                Shadcn/ui primitives
│       ├── hooks/
│       │   ├── use-sehras.ts      SWR data hooks
│       │   ├── use-copilot.ts     Copilot SSE + conversation management
│       │   ├── use-sse.ts         Analysis progress streaming
│       │   ├── use-chat.ts        Simple chat hook
│       │   └── use-auth.ts        Auth state management
│       └── lib/
│           ├── api-client.ts      HTTP client (GET/POST/PATCH/DELETE/upload/download/SSE)
│           ├── types.ts           TypeScript interfaces
│           ├── constants.ts       Components, themes, colors
│           ├── auth.ts            Cookie/localStorage token management
│           ├── copilot-store.ts   Conversation localStorage persistence
│           └── utils.ts           Tailwind cn() helper
└── auth_config.yaml               Seed users for first startup
```
