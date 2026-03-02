"use client";

import Link from "next/link";
import {
  Eye,
  ArrowLeft,
  Database,
  Cpu,
  FileText,
  Shield,
  Zap,
  Bot,
  Layers,
  Server,
  Globe,
  Code2,
  GitBranch,
  Scale,
} from "lucide-react";
import { Mermaid } from "@/components/docs/mermaid";

/* ─── Tiny helpers ─────────────────────────────────────────── */

function Badge({ children, color = "teal" }: { children: React.ReactNode; color?: "teal" | "red" | "gray" | "blue" }) {
  const cls: Record<string, string> = {
    teal: "bg-[#0D7377]/10 text-[#0D7377]",
    red: "bg-red-100 text-red-700",
    gray: "bg-gray-100 text-gray-600",
    blue: "bg-blue-100 text-blue-700",
  };
  return <span className={`inline-block rounded-full px-2.5 py-0.5 text-xs font-medium ${cls[color]}`}>{children}</span>;
}

function Section({ id, icon: Icon, title, children }: { id: string; icon: React.ElementType; title: string; children: React.ReactNode }) {
  return (
    <section id={id} className="scroll-mt-24">
      <div className="flex items-center gap-3 mb-6">
        <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-[#0D7377]/10">
          <Icon className="h-5 w-5 text-[#0D7377]" />
        </div>
        <h2 className="text-2xl font-bold tracking-tight">{title}</h2>
      </div>
      {children}
    </section>
  );
}

function Pre({ children }: { children: string }) {
  return (
    <pre className="overflow-x-auto rounded-xl border bg-gray-950 p-5 text-[13px] leading-relaxed text-gray-300 font-mono">
      {children}
    </pre>
  );
}

function TRow({ cells, header }: { cells: string[]; header?: boolean }) {
  const Tag = header ? "th" : "td";
  return (
    <tr className={header ? "bg-[#0D7377] text-white" : "border-b last:border-0 hover:bg-gray-50 transition-colors"}>
      {cells.map((c, i) => (
        <Tag key={i} className={`px-4 py-2.5 text-left text-sm ${header ? "font-semibold" : ""} ${i === 0 && !header ? "font-medium" : ""}`}>
          {c}
        </Tag>
      ))}
    </tr>
  );
}

function ADR({
  number,
  title,
  headers,
  rows,
  caveat,
}: {
  number: number;
  title: string;
  headers: string[];
  rows: string[][];
  caveat: string;
}) {
  return (
    <div className="space-y-3">
      <h3 className="font-semibold text-base">{number}. {title}</h3>
      <div className="overflow-x-auto rounded-xl border">
        <table className="w-full">
          <thead><TRow cells={headers} header /></thead>
          <tbody>
            {rows.map((r, i) => <TRow key={i} cells={r} />)}
          </tbody>
        </table>
      </div>
      <p className="text-xs text-muted-foreground italic">{caveat}</p>
    </div>
  );
}

/* ─── TOC items ────────────────────────────────────────────── */

const TOC = [
  { id: "tech-stack", label: "Tech Stack", icon: Layers },
  { id: "decisions", label: "Arch Decisions", icon: Scale },
  { id: "architecture", label: "System Architecture", icon: Server },
  { id: "database", label: "Database Schema", icon: Database },
  { id: "data-flow", label: "Data Flow", icon: GitBranch },
  { id: "ai-engine", label: "AI Engine", icon: Cpu },
  { id: "copilot", label: "Copilot", icon: Bot },
  { id: "exports", label: "Export Formats", icon: FileText },
  { id: "frontend", label: "Frontend", icon: Globe },
  { id: "api", label: "API Reference", icon: Code2 },
  { id: "security", label: "Security", icon: Shield },
  { id: "performance", label: "Performance", icon: Zap },
];

/* ─── Page ─────────────────────────────────────────────────── */

export default function DocsPage() {
  return (
    <div className="min-h-screen bg-white">
      {/* ── Header ──────────────────────────────────────────── */}
      <header className="sticky top-0 z-50 border-b bg-white/80 backdrop-blur-lg">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-3">
          <div className="flex items-center gap-3">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-[#0D7377]">
              <Eye className="h-4 w-4 text-white" />
            </div>
            <div>
              <span className="font-bold text-sm">SEHRA</span>
              <span className="ml-1.5 text-xs text-muted-foreground">Architecture</span>
            </div>
          </div>
          <Link
            href="/login"
            className="flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground transition-colors"
          >
            <ArrowLeft className="h-3.5 w-3.5" />
            Back to login
          </Link>
        </div>
      </header>

      <div className="mx-auto max-w-6xl px-6 py-12 lg:grid lg:grid-cols-[220px_1fr] lg:gap-12">
        {/* ── Sidebar TOC ──────────────────────────────────── */}
        <aside className="hidden lg:block">
          <nav className="sticky top-20 space-y-1">
            <p className="mb-3 text-xs font-semibold uppercase tracking-wider text-muted-foreground">On this page</p>
            {TOC.map((item) => (
              <a
                key={item.id}
                href={`#${item.id}`}
                className="flex items-center gap-2 rounded-md px-2.5 py-1.5 text-sm text-muted-foreground hover:text-foreground hover:bg-gray-100 transition-colors"
              >
                <item.icon className="h-3.5 w-3.5" />
                {item.label}
              </a>
            ))}
          </nav>
        </aside>

        {/* ── Main content ──────────────────────────────────── */}
        <main className="space-y-16">
          {/* Hero */}
          <div className="rounded-2xl bg-gradient-to-br from-[#095456] via-[#0D7377] to-[#10857A] p-8 text-white">
            <h1 className="text-3xl font-bold tracking-tight sm:text-4xl">SEHRA Analyzer</h1>
            <p className="mt-2 text-lg text-white/80">Architecture Document</p>
            <p className="mt-4 max-w-2xl text-sm leading-relaxed text-white/70">
              School Eye Health Rapid Assessment analysis platform built for PRASHO Foundation by Samanvay Foundation.
              AI-powered PDF analysis, multi-format exports, agentic copilot, and secure sharing.
            </p>
            <div className="mt-6 flex flex-wrap gap-2">
              <Badge>Next.js 16</Badge>
              <Badge>FastAPI</Badge>
              <Badge>PostgreSQL</Badge>
              <Badge>Multi-LLM AI</Badge>
              <Badge>SSE Streaming</Badge>
            </div>
          </div>

          {/* ── Tech Stack ──────────────────────────────────── */}
          <Section id="tech-stack" icon={Layers} title="Tech Stack">
            <div className="overflow-hidden rounded-xl border">
              <table className="w-full">
                <thead><TRow cells={["Layer", "Technology"]} header /></thead>
                <tbody>
                  <TRow cells={["Frontend", "Next.js 16 (App Router), React 19, TypeScript, Tailwind CSS, Shadcn/ui"]} />
                  <TRow cells={["Data Fetching", "SWR (stale-while-revalidate)"]} />
                  <TRow cells={["Backend", "FastAPI (Python 3.11+), Uvicorn ASGI"]} />
                  <TRow cells={["Database", "PostgreSQL, SQLAlchemy 2.0 ORM"]} />
                  <TRow cells={["AI / LLM", "Groq (llama-3.3-70b), Anthropic Claude, OpenAI GPT-4o \u2014 multi-provider fallback"]} />
                  <TRow cells={["PDF Parsing", "PyMuPDF (fitz), pymupdf4llm"]} />
                  <TRow cells={["Report Gen", "python-docx, openpyxl, Jinja2, WeasyPrint, matplotlib, Plotly"]} />
                  <TRow cells={["Auth", "JWT (HS256, 24h), bcrypt"]} />
                  <TRow cells={["Realtime", "Server-Sent Events (SSE) via sse-starlette"]} />
                </tbody>
              </table>
            </div>
          </Section>

          {/* ── Architectural Decisions ──────────────────────── */}
          <Section id="decisions" icon={Scale} title="Architectural Decisions">
            <p className="text-sm text-muted-foreground mb-6">
              Every technology choice involves trade-offs. This section documents <strong>why</strong> each decision was made in the context of SEHRA &mdash; an AI-powered analytics tool used by health analysts in low-resource settings.
            </p>

            <div className="space-y-10">
              <ADR
                number={1}
                title="Why Python (Not Java)?"
                headers={["Factor", "Python (chosen)", "Java (alternative)"]}
                rows={[
                  ["AI/LLM integration", "Native SDKs (OpenAI, Anthropic, Groq) are Python-first. 3 lines to call an LLM.", "Requires community wrappers, more boilerplate"],
                  ["PDF parsing", "PyMuPDF, pymupdf4llm, Surya OCR \u2014 all Python-native", "Apache PDFBox exists but weaker for AI-ready extraction"],
                  ["Data science", "Pandas, Plotly, Matplotlib, NumPy \u2014 first-class", "No equivalent ecosystem"],
                  ["Rapid prototyping", "Streamlit \u2192 working app in days. FastAPI \u2192 production API in hours", "Spring Boot = weeks for equivalent"],
                  ["Team velocity", "~3x less code for same functionality", "More ceremony, annotations, build tooling"],
                  ["Deployment", "Single pip install, 11-line Dockerfile", "JVM warmup, larger images, more memory"],
                ]}
                caveat="Java would make sense if: You needed enterprise-grade concurrency (10K+ concurrent users), strict type safety across a 50-person team, or had an existing Java microservices ecosystem."
              />

              <ADR
                number={2}
                title="Why FastAPI (Not Django or Flask)?"
                headers={["Factor", "FastAPI (chosen)", "Django", "Flask"]}
                rows={[
                  ["Async support", "Native async/await, perfect for SSE + LLM calls", "Bolt-on via ASGI, Channels adds complexity", "Requires Quart or gevent hacks"],
                  ["SSE streaming", "EventSourceResponse + async generators = trivial", "Needs Channels + Redis for real-time", "No built-in support"],
                  ["Auto docs", "Swagger UI + ReDoc from type hints, zero config", "DRF has it but heavier setup", "Flask-RESTx, extra dependency"],
                  ["Pydantic validation", "Built-in, validates every request/response", "Serializers (DRF) \u2014 similar but more verbose", "Manual or marshmallow"],
                  ["Performance", "Among fastest Python frameworks (Starlette + Uvicorn)", "Heavier ORM, middleware stack", "Comparable but fewer batteries"],
                ]}
                caveat="Django would make sense if: You needed its admin panel, built-in auth system, or ORM migrations out of the box. For an API-first platform with SSE streaming, FastAPI's async-native design is a better fit."
              />

              <ADR
                number={3}
                title="Why Next.js (Not CRA or Vite+React)?"
                headers={["Factor", "Next.js (chosen)", "CRA / Vite+React"]}
                rows={[
                  ["App Router", "File-based routing, layouts, loading states \u2014 no react-router config", "Manual routing setup, no conventions"],
                  ["SSR/SSG", "Hybrid rendering per-page. Share page is SSR for SEO + OG tags", "Client-only, bad for share link previews"],
                  ["Middleware", "Auth redirect in middleware.ts \u2014 runs at edge, before render", "No equivalent; guard logic scattered in components"],
                  ["Dynamic imports", "next/dynamic with SSR toggle \u2014 critical for chart libraries", "React.lazy works but no SSR control"],
                  ["TypeScript", "First-class, zero config", "Same with Vite; CRA needs --template typescript"],
                ]}
                caveat="CRA/Vite would make sense if: You were building a pure SPA with no server-side rendering needs and wanted maximum build speed during development."
              />

              <ADR
                number={4}
                title="Why PostgreSQL (Not MongoDB)?"
                headers={["Factor", "PostgreSQL (chosen)", "MongoDB"]}
                rows={[
                  ["Relational integrity", "SEHRA \u2192 Components \u2192 Entries: strict FK cascades", "Document nesting works, but no referential integrity"],
                  ["JSON support", "items column uses native JSONB \u2014 best of both worlds", "Native document store, but overkill here"],
                  ["ACID compliance", "Full transactions \u2014 critical for multi-table analysis saves", "Eventual consistency by default"],
                  ["Tooling", "SQLAlchemy 2.0, Alembic migrations, mature ecosystem", "Motor/pymongo, less ORM support"],
                  ["Hosting", "Available everywhere: Docker, RDS, Supabase, Neon", "Atlas is good but adds vendor lock-in"],
                ]}
                caveat="MongoDB would make sense if: Your data was truly unstructured, you needed horizontal sharding at scale, or were doing heavy geospatial queries. SEHRA data is inherently relational."
              />

              <ADR
                number={5}
                title="Why SSE (Not WebSockets)?"
                headers={["Factor", "SSE (chosen)", "WebSockets"]}
                rows={[
                  ["Directionality", "Server \u2192 Client only. Perfect for analysis progress + copilot streaming", "Bidirectional \u2014 overkill for our use case"],
                  ["Protocol", "Standard HTTP. Works through proxies, CDNs, load balancers", "Requires upgrade handshake, some proxies block"],
                  ["Reconnection", "Built-in auto-reconnect with EventSource API", "Manual reconnect logic needed"],
                  ["Implementation", "sse-starlette + async yield = 5 lines", "WebSocket handler + connection manager + ping/pong"],
                  ["Debugging", "Standard HTTP \u2014 curl, DevTools, request logging", "Binary frames, needs specialized tools"],
                ]}
                caveat="WebSockets would make sense if: You needed real-time bidirectional communication (collaborative editing, chat between users). For streaming AI responses, SSE is simpler and more reliable."
              />

              <ADR
                number={6}
                title="Why Multi-LLM Fallback (Not Single Provider)?"
                headers={["Factor", "Multi-LLM fallback (chosen)", "Single provider"]}
                rows={[
                  ["Availability", "If Groq is down, Claude handles it. If Claude is down, GPT-4o.", "Single point of failure"],
                  ["Cost optimization", "Groq free tier for dev. Claude/GPT-4o for production quality", "Locked into one pricing model"],
                  ["Rate limits", "Exhaust one provider's limits \u2192 automatic fallback", "Hit rate limit = all AI features stop"],
                  ["Implementation cost", "~30 lines of fallback logic in ai_engine.py", "Slightly simpler, but fragile"],
                ]}
                caveat="Single provider makes sense if: You have an enterprise agreement with guaranteed SLAs. For a health analytics tool where uptime matters, multi-LLM resilience is the safer bet."
              />

              <ADR
                number={7}
                title="Why SWR (Not React Query or Redux)?"
                headers={["Factor", "SWR (chosen)", "React Query", "Redux + RTK Query"]}
                rows={[
                  ["Bundle size", "~4KB gzipped", "~13KB gzipped", "~30KB+ with toolkit"],
                  ["API simplicity", "useSWR(key, fetcher) \u2014 one hook", "useQuery({queryKey, queryFn})", "createApi, slices, store \u2014 significant boilerplate"],
                  ["Stale-while-revalidate", "Core philosophy, built-in", "Supported, similarly good", "Configurable but not default"],
                  ["Learning curve", "Minimal \u2014 works like useState with caching", "Moderate \u2014 more concepts", "Steep \u2014 actions, reducers, middleware"],
                ]}
                caveat="React Query makes sense for complex mutation workflows. Redux makes sense for extensive client-side state. For a data-display-heavy platform where most state is server data, SWR's simplicity is a perfect match."
              />

              <ADR
                number={8}
                title="Why PyMuPDF (Not Tabula or pdfplumber)?"
                headers={["Factor", "PyMuPDF/fitz (chosen)", "Tabula", "pdfplumber"]}
                rows={[
                  ["Widget extraction", "Native form widget API \u2014 reads checkboxes, radio buttons, text fields", "Table extraction only, no widget support", "Can extract form fields but less robust"],
                  ["Performance", "C-based (MuPDF engine), fastest Python PDF lib", "Java bridge, JVM startup overhead", "Pure Python, slower on large docs"],
                  ["Checkbox reading", "widget.field_type_string == \"CheckBox\" \u2014 direct", "Cannot read checkboxes", "Limited checkbox support"],
                  ["Dependencies", "Single C extension, pip install", "Requires Java runtime", "Pure Python, no external deps"],
                ]}
                caveat="Tabula excels at table-heavy PDFs (invoices, financial reports). pdfplumber handles complex text layouts. SEHRA PDFs are form-fillable with checkbox widgets \u2014 PyMuPDF's widget API is the only tool that handles this elegantly."
              />

              <ADR
                number={9}
                title="Why JWT (Not Server-Side Sessions)?"
                headers={["Factor", "JWT (chosen)", "Server-side sessions"]}
                rows={[
                  ["Stateless", "Token contains all auth data. No session store needed", "Requires Redis/DB for session storage"],
                  ["Scaling", "Any backend instance can verify \u2014 no shared state", "Session affinity or shared store needed"],
                  ["API friendliness", "Authorization: Bearer <token> \u2014 standard REST", "Session cookies work but less explicit"],
                  ["Implementation", "40 lines in auth.py (create + decode)", "Session middleware + store + cleanup"],
                  ["Revocation", "Harder \u2014 requires blacklist for immediate revocation", "Easy \u2014 delete session from store"],
                ]}
                caveat="Sessions make sense if you need instant revocation or server-controlled session lifetime. For a small-team platform with 24h token expiry, JWT keeps things simple and stateless."
              />

              <ADR
                number={10}
                title="Why Monolith (Not Microservices)?"
                headers={["Factor", "Monolith (chosen)", "Microservices"]}
                rows={[
                  ["Deployment", "Single Docker container, docker compose up", "Multiple containers, K8s orchestration, service mesh"],
                  ["Development", "One repo, one language, shared types", "Multi-repo, API contracts, versioning"],
                  ["Debugging", "Single process, single log stream, step-through", "Distributed tracing, log aggregation, correlation IDs"],
                  ["Data consistency", "Single DB, ACID transactions across operations", "Saga patterns, eventual consistency"],
                  ["Team size", "1-5 developers \u2014 a monolith is faster", "10+ teams \u2014 independent deployment matters"],
                  ["Latency", "Function calls between modules (nanoseconds)", "Network calls between services (milliseconds)"],
                ]}
                caveat="Microservices make sense with 10+ teams needing independent deploy cycles. For a focused analytics platform with a small team, a well-structured monolith delivers the same code organization without the distributed systems tax."
              />
            </div>
          </Section>

          {/* ── System Architecture ─────────────────────────── */}
          <Section id="architecture" icon={Server} title="System Architecture">
            <Mermaid chart={`graph TB
  subgraph Frontend["Next.js Frontend"]
    Assess["Assessments"]
    Upload["Upload PDF"]
    Collect["Collect Form"]
    Admin["Admin Codebook"]
    Tabs["Overview - Report - Analysis - Export"]
    SWR["SWR Cache Layer"]
    Copilot["Copilot Sidebar"]
    Assess --- Tabs
    Upload -->|SSE| SWR
    Collect -->|SSE| SWR
    Tabs --- SWR
    Admin --- SWR
  end

  subgraph Backend["FastAPI Backend"]
    Auth["auth JWT"]
    SEHRAS["sehras CRUD"]
    AnalysisR["analysis SSE + AI"]
    ExportR["export formats"]
    AgentR["agent copilot"]
  end

  subgraph Core["Core Services"]
    PDF["pdf_parser"]
    AI["ai_engine"]
    Report["report_gen"]
    CopAgent["copilot_agent + tools"]
    PDF --> AI --> Report
    AI --> CopAgent
  end

  DB[("PostgreSQL + SQLAlchemy")]

  SWR -->|REST + SSE| Backend
  Copilot -->|SSE| AgentR
  Backend --> Core
  Core --> DB
`} />
          </Section>

          {/* ── Database Schema ─────────────────────────────── */}
          <Section id="database" icon={Database} title="Database Schema">
            <Mermaid className="mb-6" chart={`erDiagram
  sehras ||--o{ component_analyses : has
  sehras ||--o{ shared_reports : has
  component_analyses ||--o{ qualitative_entries : contains
  component_analyses ||--o{ report_sections : contains
  shared_reports ||--o{ report_views : tracks
  users ||--o{ sehras : creates

  sehras {
    uuid id
    string country
    string province
    string district
    date assessment_date
    string status
    text executive_summary
    text recommendations
  }

  component_analyses {
    uuid id
    uuid sehra_id
    string component
    int enabler_count
    int barrier_count
    json items
  }

  qualitative_entries {
    uuid id
    uuid component_analysis_id
    text remark_text
    string theme
    string classification
    float confidence
  }

  report_sections {
    uuid id
    uuid component_analysis_id
    string section_type
    text content
  }

  shared_reports {
    uuid id
    uuid sehra_id
    string share_token
    string passcode_hash
    datetime expires_at
  }
`} />
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {/* sehras */}
              <div className="rounded-xl border p-4">
                <h3 className="font-semibold text-sm mb-3 flex items-center gap-2">
                  <div className="h-2 w-2 rounded-full bg-[#0D7377]" />
                  sehras
                </h3>
                <ul className="space-y-1 text-xs text-muted-foreground font-mono">
                  <li><span className="text-foreground font-semibold">id</span> PK, UUID</li>
                  <li>country, province, district</li>
                  <li>assessment_date, upload_date</li>
                  <li>status <Badge color="gray">draft | reviewed | published</Badge></li>
                  <li>pdf_filename, raw_extracted_data</li>
                  <li>executive_summary, recommendations</li>
                </ul>
              </div>

              {/* component_analyses */}
              <div className="rounded-xl border p-4">
                <h3 className="font-semibold text-sm mb-3 flex items-center gap-2">
                  <div className="h-2 w-2 rounded-full bg-[#0D7377]" />
                  component_analyses
                </h3>
                <ul className="space-y-1 text-xs text-muted-foreground font-mono">
                  <li><span className="text-foreground font-semibold">id</span> PK &bull; <span className="text-foreground">sehra_id</span> FK</li>
                  <li>component <Badge color="gray">6 types</Badge></li>
                  <li>enabler_count, barrier_count</li>
                  <li>items (JSON[]), numeric_data (JSON)</li>
                </ul>
              </div>

              {/* qualitative_entries */}
              <div className="rounded-xl border p-4">
                <h3 className="font-semibold text-sm mb-3 flex items-center gap-2">
                  <div className="h-2 w-2 rounded-full bg-[#10857A]" />
                  qualitative_entries
                </h3>
                <ul className="space-y-1 text-xs text-muted-foreground font-mono">
                  <li><span className="text-foreground font-semibold">id</span> PK &bull; component_analysis_id FK</li>
                  <li>remark_text, item_id</li>
                  <li>theme, classification, confidence</li>
                  <li>edited_by_human</li>
                </ul>
              </div>

              {/* report_sections */}
              <div className="rounded-xl border p-4">
                <h3 className="font-semibold text-sm mb-3 flex items-center gap-2">
                  <div className="h-2 w-2 rounded-full bg-[#10857A]" />
                  report_sections
                </h3>
                <ul className="space-y-1 text-xs text-muted-foreground font-mono">
                  <li><span className="text-foreground font-semibold">id</span> PK &bull; component_analysis_id FK</li>
                  <li>section_type <Badge color="gray">enabler_summary | barrier_summary | action_points</Badge></li>
                  <li>content (Text), edited_by_human</li>
                </ul>
              </div>

              {/* shared_reports */}
              <div className="rounded-xl border p-4">
                <h3 className="font-semibold text-sm mb-3 flex items-center gap-2">
                  <div className="h-2 w-2 rounded-full bg-[#18A781]" />
                  shared_reports
                </h3>
                <ul className="space-y-1 text-xs text-muted-foreground font-mono">
                  <li><span className="text-foreground font-semibold">id</span> PK &bull; sehra_id FK</li>
                  <li>share_token (unique), passcode_hash</li>
                  <li>created_by, created_at, expires_at</li>
                  <li>is_active, cached_html</li>
                </ul>
              </div>

              {/* users + others */}
              <div className="rounded-xl border p-4">
                <h3 className="font-semibold text-sm mb-3 flex items-center gap-2">
                  <div className="h-2 w-2 rounded-full bg-gray-400" />
                  users &amp; others
                </h3>
                <ul className="space-y-1 text-xs text-muted-foreground font-mono">
                  <li><strong className="text-foreground">users</strong> &mdash; id, username, name, password_hash, role</li>
                  <li><strong className="text-foreground">report_views</strong> &mdash; audit trail (IP, UA, timestamp)</li>
                  <li><strong className="text-foreground">form_drafts</strong> &mdash; in-progress form saves</li>
                  <li><strong className="text-foreground">codebook_override</strong> &mdash; admin question edits</li>
                </ul>
              </div>
            </div>
            <p className="mt-4 text-sm text-muted-foreground">
              <strong>Cascade deletes:</strong> Deleting a SEHRA cascades to components &rarr; entries + sections, and to shared_reports &rarr; views.
            </p>
          </Section>

          {/* ── Data Flow ───────────────────────────────────── */}
          <Section id="data-flow" icon={GitBranch} title="Data Flow: PDF Upload &rarr; Analysis">
            <Mermaid chart={`graph TD
  A["User drops PDF"] --> B["POST /analyze/upload - SSE stream"]
  B --> S1["Step 1: Validate PDF"]
  S1 --> S2["Step 2: Parse Document - PyMuPDF"]
  S2 --> S2a["Extract header fields"]
  S2 --> S2b["Extract checkbox pairs"]
  S2a --> S3["Step 3: Score Items"]
  S2b --> S3
  S3 --> S4["Step 4: AI Analysis per Component"]
  S4 --> S4a["Classify remarks"]
  S4 --> S4b["Generate summaries"]
  S4 --> S4c["Generate action points"]
  S4a --> S5["Steps 5-7: Save to DB"]
  S4b --> S5
  S4c --> S5
  S5 --> S8["Step 8: Executive Summary - AI"]
  S8 --> S9["Step 9: Recommendations - AI"]
  S9 --> S10["Step 10: Complete"]
`} />
            <div className="mt-4 space-y-2 text-sm text-muted-foreground">
              <p>
                <strong>PDF Parser strategy:</strong> Widget-first extraction. SEHRA PDFs are form-fillable &mdash; checkbox widgets give yes/no answers, nearby text blocks give question labels, free-text fields give qualitative remarks. Each checkbox pair is matched to codebook items using fuzzy text matching.
              </p>
              <p>
                <strong>Component page ranges:</strong> Context (pp 10-15), Policy (16-20), Service Delivery (21-26), HR (27-30), Supply Chain (31-35), Barriers (36-41).
              </p>
            </div>
          </Section>

          {/* ── AI Engine ───────────────────────────────────── */}
          <Section id="ai-engine" icon={Cpu} title="AI Engine">
            <Mermaid className="mb-6" chart={`graph LR
  Req["AI Request"] --> G{"Groq available?"}
  G -->|Yes| Groq["Groq llama-3.3-70b"]
  G -->|No| A{"Anthropic available?"}
  Groq -->|Success| V["Pydantic Validation"]
  Groq -->|Fail| A
  A -->|Yes| Claude["Anthropic Claude"]
  A -->|No| O{"OpenAI available?"}
  Claude -->|Success| V
  Claude -->|Fail| O
  O -->|Yes| GPT["OpenAI GPT-4o"]
  O -->|No| Err["Error: No LLM"]
  GPT -->|Success| V
  GPT -->|Fail| Err
  V --> Res["Structured Response"]
`} />

            <div className="overflow-hidden rounded-xl border">
              <table className="w-full">
                <thead><TRow cells={["Operation", "Input", "Output"]} header /></thead>
                <tbody>
                  <TRow cells={["classify_remarks", "Component remarks + codebook", "{theme, classification, confidence} per remark"]} />
                  <TRow cells={["generate_summary", "Classified entries", "Enabler / barrier summary text"]} />
                  <TRow cells={["generate_action_points", "Barrier entries + context", "Actionable recommendations per component"]} />
                  <TRow cells={["generate_executive_summary", "All component data", "High-level assessment overview"]} />
                  <TRow cells={["generate_recommendations", "Full analysis results", "Strategic recommendations"]} />
                </tbody>
              </table>
            </div>

            <div className="mt-4 grid gap-4 sm:grid-cols-2">
              <div className="rounded-xl border p-4">
                <h4 className="font-semibold text-sm mb-2">11 Cross-cutting Themes</h4>
                <div className="flex flex-wrap gap-1.5">
                  {["Infrastructure", "Funding", "Training", "Policy", "Community", "Technology", "Human Resources", "Supply Chain", "Governance", "Access", "Quality", "Other"].map(t => (
                    <Badge key={t} color="gray">{t}</Badge>
                  ))}
                </div>
              </div>
              <div className="rounded-xl border p-4">
                <h4 className="font-semibold text-sm mb-2">Classifications</h4>
                <div className="flex flex-wrap gap-1.5">
                  <Badge>enabler</Badge>
                  <Badge color="red">barrier</Badge>
                  <Badge>strength</Badge>
                  <Badge color="red">weakness</Badge>
                  <Badge color="gray">neutral</Badge>
                </div>
                <p className="mt-2 text-xs text-muted-foreground">All AI responses validated via Pydantic models before storage.</p>
              </div>
            </div>
          </Section>

          {/* ── Copilot ─────────────────────────────────────── */}
          <Section id="copilot" icon={Bot} title="Copilot (AI Assistant)">
            <p className="text-sm text-muted-foreground mb-4">
              Agentic chat with function calling, streamed via SSE. The copilot can both <strong>read</strong> and <strong>write</strong> assessment data &mdash; like an IDE agent (Cursor, Lovable) but for health analytics.
            </p>
            <Mermaid chart={`sequenceDiagram
  participant U as User
  participant FE as Frontend
  participant API as Agent API
  participant LLM as LLM
  participant T as Tools
  participant DB as PostgreSQL

  U->>FE: Send message
  FE->>API: SSE stream request
  API->>DB: Load corrections for context
  API->>LLM: System prompt + context + corrections

  loop Max 8 tool rounds
    LLM-->>API: thinking
    alt Tool call needed
      LLM->>API: tool_call (read or write)
      API->>T: Execute tool
      T->>DB: Query or mutate data
      DB-->>T: Result
      T-->>API: tool_result
      API-->>FE: stream events
      API->>LLM: Feed result back
    else Direct response
      LLM-->>API: message + chart
    end
  end

  API-->>FE: final response
  FE->>API: Save conversation
  API->>DB: Persist messages
  API-->>FE: done event
  FE-->>U: Render response
`} />

            <div className="grid gap-4 sm:grid-cols-2 mt-6">
              <div>
                <h3 className="font-semibold text-sm mb-3 flex items-center gap-2">
                  <Badge>Read</Badge> Query Tools
                </h3>
                <div className="overflow-hidden rounded-xl border">
                  <table className="w-full">
                    <thead><TRow cells={["Tool", "Description"]} header /></thead>
                    <tbody>
                      <TRow cells={["list_assessments", "List all SEHRA assessments"]} />
                      <TRow cells={["get_assessment_details", "Full details for one SEHRA"]} />
                      <TRow cells={["get_component_analysis", "Component-level breakdown"]} />
                      <TRow cells={["get_executive_summary", "Summary + recommendations"]} />
                      <TRow cells={["search_entries", "Filter by theme/classification/confidence"]} />
                      <TRow cells={["compare_assessments", "Side-by-side comparison"]} />
                      <TRow cells={["get_codebook", "Codebook questions by section"]} />
                      <TRow cells={["suggest_actions", "Context-aware next steps"]} />
                    </tbody>
                  </table>
                </div>
              </div>
              <div>
                <h3 className="font-semibold text-sm mb-3 flex items-center gap-2">
                  <Badge color="red">Write</Badge> Edit Tools
                </h3>
                <div className="overflow-hidden rounded-xl border">
                  <table className="w-full">
                    <thead><TRow cells={["Tool", "Description"]} header /></thead>
                    <tbody>
                      <TRow cells={["edit_entry", "Change entry theme/classification"]} />
                      <TRow cells={["edit_report_section", "Rewrite report section content"]} />
                      <TRow cells={["edit_executive_summary", "Update summary/recommendations"]} />
                      <TRow cells={["change_status", "Draft \u2192 Reviewed \u2192 Published"]} />
                      <TRow cells={["batch_approve", "Approve entries above confidence"]} />
                    </tbody>
                  </table>
                </div>
              </div>
            </div>

            <h3 className="font-semibold text-sm mt-6 mb-3">Conversation Persistence &amp; Learning Loop</h3>
            <div className="grid gap-4 sm:grid-cols-3">
              <div className="rounded-xl border p-4">
                <h4 className="font-semibold text-xs mb-2 text-[#0D7377]">Conversations</h4>
                <p className="text-xs text-muted-foreground">
                  Server-side PostgreSQL persistence. Save, retrieve, list, and delete full conversation threads linked to SEHRA assessments.
                </p>
              </div>
              <div className="rounded-xl border p-4">
                <h4 className="font-semibold text-xs mb-2 text-[#0D7377]">Feedback</h4>
                <p className="text-xs text-muted-foreground">
                  Thumbs up/down on individual AI messages with optional comments. Tracked per user and conversation.
                </p>
              </div>
              <div className="rounded-xl border p-4">
                <h4 className="font-semibold text-xs mb-2 text-[#0D7377]">Corrections</h4>
                <p className="text-xs text-muted-foreground">
                  &ldquo;X should be Y&rdquo; corrections auto-injected into the agent&rsquo;s system prompt so it learns from past mistakes.
                </p>
              </div>
            </div>
          </Section>

          {/* ── Exports ─────────────────────────────────────── */}
          <Section id="exports" icon={FileText} title="Export Formats">
            <p className="text-sm text-muted-foreground mb-4">
              All endpoints: <code className="rounded bg-gray-100 px-1.5 py-0.5 text-xs font-mono">GET /export/&#123;sehra_id&#125;/&#123;format&#125;</code> &rarr; StreamingResponse
            </p>
            <div className="overflow-hidden rounded-xl border">
              <table className="w-full">
                <thead><TRow cells={["Format", "Generator", "Content"]} header /></thead>
                <tbody>
                  <TRow cells={["DOCX", "python-docx + matplotlib", "Title page, exec summary, methodology, radar chart, bar chart, heatmap, per-component tables, action points, recommendations, appendix"]} />
                  <TRow cells={["XLSX", "openpyxl", "7+ sheets: Summary, Component Scores, Theme Analysis (pivot), per-component details, All Remarks"]} />
                  <TRow cells={["HTML", "Jinja2 + Plotly", "Self-contained HTML with interactive charts, per-component breakdown, appendix"]} />
                  <TRow cells={["PDF", "WeasyPrint", "A4 print-optimized version of HTML report"]} />
                </tbody>
              </table>
            </div>
            <p className="mt-3 text-xs text-muted-foreground">All exports include metadata: timestamp (IST), exporter username, requester IP. Lazy imports &mdash; heavy libs only loaded on demand.</p>
          </Section>

          {/* ── Frontend ────────────────────────────────────── */}
          <Section id="frontend" icon={Globe} title="Frontend Architecture">
            <div className="grid gap-4 sm:grid-cols-2 mb-6">
              <div className="rounded-xl border p-4">
                <h3 className="font-semibold text-sm mb-3">Routes</h3>
                <ul className="space-y-1 text-xs font-mono text-muted-foreground">
                  <li><span className="text-foreground">/assessments</span> &mdash; Grid of assessment cards</li>
                  <li><span className="text-foreground">/assessments/[id]</span> &mdash; Overview | Report | Analysis | Export</li>
                  <li><span className="text-foreground">/upload</span> &mdash; PDF drag-and-drop + SSE progress</li>
                  <li><span className="text-foreground">/collect</span> &mdash; 6-step form wizard + auto-save</li>
                  <li><span className="text-foreground">/admin</span> &mdash; Codebook question management</li>
                  <li><span className="text-foreground">/share/[token]</span> &mdash; Public passcode-protected viewer</li>
                </ul>
              </div>
              <div className="rounded-xl border p-4">
                <h3 className="font-semibold text-sm mb-3">Key Patterns</h3>
                <ul className="space-y-1.5 text-xs text-muted-foreground">
                  <li><strong className="text-foreground">Dynamic imports</strong> &mdash; Charts, ComponentTabs, CopilotSidebar lazy-loaded</li>
                  <li><strong className="text-foreground">SWR config</strong> &mdash; 5s dedup, no refetch on focus, keep previous data</li>
                  <li><strong className="text-foreground">Copilot context</strong> &mdash; Auto-detects sehraId from URL</li>
                  <li><strong className="text-foreground">Review workflow</strong> &mdash; Draft &rarr; Reviewed &rarr; Published</li>
                </ul>
              </div>
            </div>

            <h3 className="font-semibold text-sm mb-3">Component Hierarchy (Assessment Detail)</h3>
            <Mermaid chart={`graph TD
  Page["AssessmentDetailPage"]
  Page --> OT["OverviewTab"]
  Page --> RT["ReportTab"]
  Page --> AT["AnalysisTab"]
  Page --> ET["ExportTab"]

  OT --> KPI["KPICards"]
  OT --> Radar["EnablerRadarChart"]
  OT --> Bar["EnablerBarrierChart"]

  RT --> Exec["Executive Summary"]
  RT --> Recs["Recommendations"]
  RT --> DL["Download DOCX PDF"]

  AT --> RC["ReviewControls"]
  AT --> CT["ComponentTabs"]
  CT --> ES["Enabler Summary"]
  CT --> BS["Barrier Summary"]
  CT --> AP["Action Points"]
  CT --> QE["Qualitative Entries"]

  ET --> FC["FormatCards"]
  ET --> SF["ShareForm"]
  ET --> SL["ShareLinksTable"]
`} />
          </Section>

          {/* ── API Reference ───────────────────────────────── */}
          <Section id="api" icon={Code2} title="API Reference">
            <p className="text-sm text-muted-foreground mb-4">
              All endpoints (except <code className="rounded bg-gray-100 px-1.5 py-0.5 text-xs font-mono">/public/*</code> and <code className="rounded bg-gray-100 px-1.5 py-0.5 text-xs font-mono">/health</code>) require <code className="rounded bg-gray-100 px-1.5 py-0.5 text-xs font-mono">Authorization: Bearer &lt;JWT&gt;</code>.
            </p>
            <Pre>{`AUTH
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
  POST   /agent/chat                   → EventSource (read + write tool calling)

CONVERSATIONS
  POST   /conversations                → Save conversation
  GET    /conversations                → List user's conversations
  GET    /conversations/{id}           → Retrieve conversation
  DELETE /conversations/{id}           → Delete conversation

FEEDBACK & CORRECTIONS
  POST   /feedback                     → Rate AI message (up/down)
  POST   /corrections                  → Submit correction
  GET    /corrections                  → List corrections

CHAT
  POST   /chat                         → {text, chart_spec}

SHARE
  POST   /shares                       → ShareLink
  GET    /shares/{sehra_id}            → ShareLink[]
  DELETE /shares/{token}
  GET    /public/share/{token}         → {valid, expired}  (no auth)
  POST   /public/share/{token}/verify  → {success, html}   (no auth)

CODEBOOK (admin only)
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
  PATCH  /sections/{id}               → {content}`}</Pre>
          </Section>

          {/* ── Security ────────────────────────────────────── */}
          <Section id="security" icon={Shield} title="Security">
            <div className="overflow-hidden rounded-xl border">
              <table className="w-full">
                <thead><TRow cells={["Area", "Implementation"]} header /></thead>
                <tbody>
                  <TRow cells={["Authentication", "JWT HS256, 24h expiry, cookie sehra_token"]} />
                  <TRow cells={["Password storage", "bcrypt with salt"]} />
                  <TRow cells={["Role-based access", "analyst (default) and admin (codebook management)"]} />
                  <TRow cells={["Route protection", "Next.js middleware checks cookie on all /app routes"]} />
                  <TRow cells={["Share links", "secrets.token_urlsafe(32), bcrypt passcode, optional expiry"]} />
                  <TRow cells={["Rate limiting", "5 failed passcode attempts per 60 min \u2192 HTTP 429"]} />
                  <TRow cells={["Audit trail", "Share views logged: IP, user-agent, timestamp, passcode correctness"]} />
                  <TRow cells={["Compression", "GZip on responses > 500 bytes"]} />
                </tbody>
              </table>
            </div>
          </Section>

          {/* ── Performance ─────────────────────────────────── */}
          <Section id="performance" icon={Zap} title="Performance">
            <div className="overflow-hidden rounded-xl border">
              <table className="w-full">
                <thead><TRow cells={["Technique", "Detail"]} header /></thead>
                <tbody>
                  <TRow cells={["SWR dedup", "5s dedup interval, keeps previous data during revalidation"]} />
                  <TRow cells={["Cache headers", "SEHRA list: max-age=10, stale-while-revalidate=30; Codebook: max-age=60"]} />
                  <TRow cells={["Lazy imports", "Export generators only imported on demand"]} />
                  <TRow cells={["Dynamic imports", "Charts, ComponentTabs, CopilotSidebar loaded via next/dynamic"]} />
                  <TRow cells={["Streaming", "Analysis + copilot use SSE; exports use StreamingResponse"]} />
                  <TRow cells={["GZip middleware", "All responses > 500 bytes compressed"]} />
                  <TRow cells={["DB pooling", "SQLAlchemy pool_pre_ping=True"]} />
                  <TRow cells={["HTML caching", "Share links pre-generate and cache the HTML at creation time"]} />
                </tbody>
              </table>
            </div>
          </Section>

          {/* ── Footer ──────────────────────────────────────── */}
          <footer className="border-t pt-8 text-center text-xs text-muted-foreground">
            <p>SEHRA Analyzer &mdash; Built for PRASHO Foundation by Samanvay Foundation</p>
          </footer>
        </main>
      </div>
    </div>
  );
}
