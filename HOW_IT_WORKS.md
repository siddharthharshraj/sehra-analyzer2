# How SEHRA Analyzer Works — Complete Technical Walkthrough

> From PDF upload to final report — every step explained.

---

## How It Works in 8 Simple Points

### 1. User uploads a SEHRA PDF
A field team fills out a 44-page form-fillable PDF with checkboxes (Yes/No) and text remarks for each question about school eye health in their country. The user uploads this PDF to the platform.

### 2. The system reads the PDF like a human would — but instantly
It doesn't just read text. It finds every **checkbox widget** on every page, detects which ones are checked (Yes/No), finds the **question text** next to each checkbox using spatial coordinates, and extracts **free-text remarks** from text fields. It also reads the country, district, and date from the first page.

### 3. Each question is matched to a master codebook
The system has a codebook of ~309 standardized SEHRA questions. It fuzzy-matches each extracted question to the codebook to get the official item ID (e.g., "S15" = Policy question 15). This tells the system which component (Policy, HR, Supply Chain, etc.) and which scoring rule applies.

### 4. Quantitative scoring happens automatically — no AI needed
Each Yes/No answer is scored using deterministic rules: Yes = enabler (score 1), No = barrier (score 0). Some questions are **reverse-scored** (e.g., "Are there challenges?" where Yes = barrier). The system counts enablers and barriers per component and calculates a readiness percentage.

### 5. AI classifies the qualitative remarks into 11 themes
This is the step that used to take 2 months manually. Every text remark (e.g., *"The Ministry has adopted WHO guidelines for screening"*) is sent to an LLM (GPT-4o / Llama / Claude) with rich domain context. The AI classifies each remark into one of **11 health system themes** (like Funding, Coordination, Local Capacity) and labels it as an **enabler** or **barrier**, with a confidence score.

### 6. The AI's output is validated and calibrated
The system doesn't blindly trust the AI. It checks that every theme name is valid (fuzzy-matching typos like "Institutional Structure & Stakeholders" → "...and Stakeholders"), caps confidence when the AI is uncertain, reduces confidence for very short remarks, and sanitizes all input to prevent prompt injection.

### 7. AI generates summaries and recommendations
After all 6 components are analyzed, the AI synthesizes everything into an **executive summary** (2-5 paragraphs covering the whole assessment) and **5-8 prioritized recommendations** (actionable next steps based on the barriers found). These are written for program managers and stakeholders.

### 8. Everything is saved and ready for review, editing, and export
All results are stored in PostgreSQL. The user gets an interactive dashboard with charts (radar, bar, heatmap), can **inline-edit** any AI classification they disagree with, **batch-approve** high-confidence entries, chat with an **AI copilot** about the data, and **export** professional reports in DOCX, XLSX, HTML, or PDF — or share via passcode-protected links.

---

## Table of Contents (Detailed)

1. [The Big Picture](#1-the-big-picture)
2. [Step 1 — PDF Upload & Validation](#2-step-1--pdf-upload--validation)
3. [Step 2 — PDF Parsing (The Hard Part)](#3-step-2--pdf-parsing-the-hard-part)
4. [Step 3 — Codebook Scoring](#4-step-3--codebook-scoring)
5. [Step 4 — AI Qualitative Analysis](#5-step-4--ai-qualitative-analysis)
6. [Step 5 — Theme Validation & Confidence Calibration](#6-step-5--theme-validation--confidence-calibration)
7. [Steps 6-7 — Save to Database](#7-steps-6-7--save-to-database)
8. [Steps 8-9 — Executive Summary & Recommendations](#8-steps-8-9--executive-summary--recommendations)
9. [Step 10 — Complete](#9-step-10--complete)
10. [The Data Files (Brain of the System)](#10-the-data-files-brain-of-the-system)
11. [Multi-Country: How It Adapts](#11-multi-country-how-it-adapts)
12. [Key Thresholds & Parameters](#12-key-thresholds--parameters)
13. [Visual Pipeline Diagram](#13-visual-pipeline-diagram)

---

## 1. The Big Picture

When a user uploads a SEHRA PDF, the system streams **10 progress events** via Server-Sent Events (SSE) back to the browser. Each step is a discrete operation:

```
Upload PDF
  │
  ├── Step 1:  Validate PDF (size, format, pages)
  ├── Step 2:  Parse PDF (extract checkboxes, text, header)
  ├── Step 3:  Score items (codebook rules → enabler/barrier)
  ├── Step 4:  AI Analysis (classify remarks into 11 themes)
  ├── Step 5:  Save SEHRA record to DB
  ├── Step 6:  Save component analyses to DB
  ├── Step 7:  Fallback summaries (if no remarks exist)
  ├── Step 8:  Generate executive summary (AI)
  ├── Step 9:  Generate recommendations (AI)
  └── Step 10: Complete → return {sehra_id, enabler_count, barrier_count}
```

The browser receives these as real-time progress updates, so the user sees a progress bar moving through each step.

---

## 2. Step 1 — PDF Upload & Validation

**File**: `api/core/validators.py`

Before any analysis, the PDF must pass validation:

| Check | Rule | Why |
|-------|------|-----|
| File type | Must be `application/pdf` | Reject non-PDF files |
| File size | ≤ 10 MB | Prevent memory issues |
| Page count | ≥ 40 pages (configurable per country) | SEHRA PDFs are typically 44+ pages |
| Form widgets | Page 1 must have form fields | Distinguishes form-fillable from scanned PDFs |

If the PDF has no form widgets, the system falls back to **Surya OCR** (optical character recognition for scanned documents).

---

## 3. Step 2 — PDF Parsing (The Hard Part)

**File**: `api/core/pdf_parser.py`

This is the most complex part of the system. A SEHRA PDF is a **form-fillable document** with hundreds of checkboxes, text fields, and free-text areas. The parser must extract structured data from this.

### 3.1 — Extract Header Information

The first page of every SEHRA PDF has text fields for metadata:

```
Text Field 1  →  Country (e.g., "Liberia")
Text Field 2  →  Province (e.g., "Montserrado County")
Text Field 3  →  District (e.g., "Montserrado")
Text Field 45 →  Assessment Date (e.g., "March 15, 2024")
```

The date parser tries **7 different formats** (because field workers enter dates inconsistently):

```
%B %d, %Y      →  "March 15, 2024"
%d/%m/%Y        →  "15/03/2024"
%Y-%m-%d        →  "2024-03-15"
%B %Y           →  "March 2024"
%d %B %Y        →  "15 March 2024"
%b %d, %Y       →  "Mar 15, 2024"
%m/%d/%Y        →  "03/15/2024"
```

### 3.2 — Extract Checkboxes (Widget-First Approach)

This is where PyMuPDF shines. SEHRA PDFs have **checkbox widgets** — actual interactive form elements, not just images of boxes.

```
Page Structure:

   ☐ Yes  ☑ No    "Is there a national eye health policy?"     [Remarks: ___________]
   ☑ Yes  ☐ No    "Are screening guidelines available?"        [Remarks: "WHO guidelines adopted"]
   ☑ Yes  ☐ No    "Is there a referral pathway?"               [Remarks: ___________]
```

**The extraction algorithm**:

1. **For each page in the component's range** (e.g., Policy = pages 16-20):
   - Read all widget objects from the page
   - Separate into checkboxes (field_type=2) and text fields (field_type=7)
   - Record each widget's **bounding box** (x0, y0, x1, y1 in page coordinates)

2. **Read text blocks** from the page:
   - PyMuPDF extracts text with precise bounding box coordinates
   - Each text block = `{text: "Is there a national...", x0, y0, x1, y1}`

### 3.3 — Pair Checkboxes (Yes/No Detection)

Checkboxes come as individual widgets. The system must pair them into Yes/No pairs:

```
                    ┌─────────┐     ┌─────────┐
 Page coordinates:  │ ☑ (x=50)│     │ ☐ (x=80)│    ← Same Y position = same pair
                    │  y=200  │     │  y=202  │
                    └─────────┘     └─────────┘
```

**Algorithm** (`pair_checkboxes()`):

1. **Group by Y-position** (tolerance = 15 pixels):
   - Checkboxes within 15px vertically are considered "same row"
   - This handles slight misalignment in form layouts

2. **Sort each group by X** (left to right):
   - Left checkbox = "Yes"
   - Right checkbox = "No"

3. **Handle different layouts**:

   | Checkboxes in Row | Interpretation |
   |-------------------|----------------|
   | **2** | Standard Yes/No pair |
   | **3** | Yes/No + "Does not exist" extra checkbox |
   | **4+** | Grid row — split into sequential pairs (columns) |
   | **1** | Standalone checkbox (rare) |

4. **Determine answer**:
   ```
   If Yes is checked     → answer = "yes"
   If No is checked      → answer = "no"
   If Extra is checked   → answer = "no" (e.g., "Does not exist")
   If nothing checked    → answer = null
   ```

### 3.4 — Match Questions to Checkboxes (Spatial Matching)

Now we have checkbox pairs at specific coordinates. We need to find the **question text** that belongs to each pair.

**For regular (non-grid) layouts**:

```
    "Is there a national eye health policy?"     ☐ Yes  ☑ No
    ←────────── Question text ──────────────→    ←── Checkboxes ──→
         (x=50, y=200)                               (x=400, y=200)
```

The algorithm finds the text block that is:
- **To the left** of the checkbox (block.x1 < checkbox.x)
- **At the same Y position** (within 15px tolerance)
- **Not noise text** (not "Yes", "No", "Remarks", page numbers, etc.)
- The **longest** matching text (in case multiple candidates exist)

**For grid layouts** (tables with column headers):

```
                          Screening    Referral    Treatment
    Primary schools         ☑  ☐        ☐  ☑        ☑  ☐
    Secondary schools       ☐  ☑        ☑  ☐        ☐  ☑
```

Grid detection triggers when multiple checkbox pairs share the same Y-position. The algorithm:
1. Finds **column headers** — text blocks positioned above the first grid row
2. Finds **row labels** — text blocks to the far left of each row
3. Combines: `"{row label} {column header}"` → "Primary schools Screening"

### 3.5 — Noise Filtering

The parser aggressively filters out non-question text:

| Text | Why Filtered |
|------|-------------|
| "Yes", "No" | Column headers, not questions |
| "Remarks" | Section label |
| "Lines of enquiry" | Section label |
| "Page 12" | Page numbers |
| Pure digits ("42") | Page numbers |
| "Yes No Remarks" | Combined header row |

This filtering is **country-configurable** — different languages can have different noise text sets.

### 3.6 — Extract Remarks (Free Text)

Text fields on the same page are collected as **remarks** — the qualitative data that the AI will analyze:

```
Question: "Is there a referral pathway?"
Answer: Yes
Remark: "The collaboration of the Eye Health Technical Working Group, which involves
         the Ministries of Education and Health, provides a structured referral pathway
         from school screening to district hospitals."
```

Remarks are the most valuable data — they contain the **context and nuance** that enables/barriers classification needs.

### 3.7 — Match to Codebook (Fuzzy Matching)

Each extracted question must be matched to a **codebook item** (the canonical question list). This is necessary because:
- PDF text extraction isn't perfect (slight character differences)
- Question wording may vary between country SEHRA versions
- Whitespace and formatting differs

**Matching strategy** (uses multiple methods, takes best):

| Method | Confidence | Example |
|--------|-----------|---------|
| SequenceMatcher ratio | Actual ratio | "Is there a national policy?" vs "Is there a national eye health policy?" |
| Bidirectional substring | 0.85 | One text fully contains the other |
| First 30 chars match | 0.80 | Both start with "Is there a national..." |
| Key words (short text) | 0.85 | Remove "Are there any" preamble, match core |

**Threshold**: ratio > 0.30 (intentionally low for maximum recall on short labels)

Each matched item gets an **item_id** (e.g., "O10", "S15", "B42") that links it to the codebook scoring rules.

### 3.8 — Output Structure

After parsing, the system produces:

```json
{
  "header": {
    "country": "Liberia",
    "district": "Montserrado",
    "province": "Montserrado County",
    "assessment_date": "2024-03-15"
  },
  "components": {
    "context": {
      "items": [
        {
          "question": "Are there any standalone school eye health programmes?",
          "answer": "yes",
          "remark": "Program started in 2023 with Sightsavers support.",
          "item_id": "O10",
          "component": "context",
          "page_num": 11,
          "match_confidence": 0.92
        }
      ]
    },
    "policy": { "items": [...] },
    "service_delivery": { "items": [...] },
    "human_resources": { "items": [...] },
    "supply_chain": { "items": [...] },
    "barriers": { "items": [...] }
  }
}
```

---

## 4. Step 3 — Codebook Scoring

**File**: `api/core/codebook.py`

Scoring is **deterministic** — no AI involved. Every SEHRA question has a predefined scoring rule in the codebook.

### 4.1 — The Codebook

The codebook (`data/codebook.json`) is the single source of truth. Each item:

```json
{
  "id": "S15",
  "section": "policy",
  "question": "Is school eye health integrated into national health policy?",
  "type": "yes_no",
  "has_scoring": true,
  "is_reverse": false,
  "score_yes": 1,
  "score_no": 0
}
```

**Item ID prefixes map to components**:

| Prefix | Component | Example |
|--------|-----------|---------|
| O | Context | O10, O11, O12... |
| S | Policy (Sectoral Legislation) | S1, S2, S3... |
| I | Service Delivery (Institutional) | I1, I2... |
| H | Human Resources | H1, H2, H3 |
| C | Supply Chain | C1, C2... |
| B | Barriers | B1, B2... |
| M | Summary/Meta | M1, M2 |

### 4.2 — Scoring Logic

For each item with `has_scoring: true`:

```
                        Standard Item              Reverse Item
                     (is_reverse: false)        (is_reverse: true)

  Answer = "Yes"    →  Score = 1 (enabler)    →  Score = 0 (barrier)
  Answer = "No"     →  Score = 0 (barrier)    →  Score = 1 (enabler)
  Answer = null     →  Score = null            →  Score = null
```

**Why reverse scoring?** Some questions are phrased negatively:
- "Are there challenges in procurement?" → Yes = **barrier** (reverse)
- "Is there a policy in place?" → Yes = **enabler** (standard)

### 4.3 — Aggregation

Scores are aggregated per component:

```
Policy Component:
  ├── Item S1:  Yes → enabler (score=1)
  ├── Item S2:  No  → barrier (score=0)
  ├── Item S3:  Yes → enabler (score=1)
  ├── Item S4:  Yes → enabler (score=1)
  └── Item S5:  No  → barrier (score=0)

  Result: enabler_count=3, barrier_count=2
  Readiness: 3/(3+2) = 60%
```

### 4.4 — Output

```json
{
  "by_component": {
    "context":          { "enabler_count": 8,  "barrier_count": 4,  "items": [...] },
    "policy":           { "enabler_count": 17, "barrier_count": 3,  "items": [...] },
    "service_delivery": { "enabler_count": 13, "barrier_count": 2,  "items": [...] },
    "human_resources":  { "enabler_count": 2,  "barrier_count": 3,  "items": [...] },
    "supply_chain":     { "enabler_count": 27, "barrier_count": 5,  "items": [...] },
    "barriers":         { "enabler_count": 10, "barrier_count": 38, "items": [...] }
  },
  "totals": { "enabler_count": 77, "barrier_count": 55 }
}
```

---

## 5. Step 4 — AI Qualitative Analysis

**File**: `api/core/ai_engine.py`

This is where the **real intelligence** lives. The AI classifies free-text remarks into structured themes.

### 5.1 — What Gets Analyzed

Only items with **remarks longer than 5 characters** are sent to the AI. Short/empty remarks are logged and skipped:

```
Item S15: remark = "The Ministry has adopted WHO guidelines for school screening" → ✅ Analyzed
Item S16: remark = "Yes"   → ❌ Filtered (≤5 chars)
Item S17: remark = ""      → ❌ Filtered (empty)
Item S18: remark = "N/A"   → ❌ Filtered (≤5 chars)
```

### 5.2 — The 11 Cross-Cutting Themes

Every remark is classified into one or more of these themes:

| # | Theme | What It Covers |
|---|-------|---------------|
| 1 | **Institutional Structure & Stakeholders** | Government bodies, ministry roles, formal partnerships |
| 2 | **Operationalization Strategies** | Implementation plans, operational procedures, protocols |
| 3 | **Coordination & Integration** | Inter-agency coordination, health-education alignment |
| 4 | **Funding** | Budget availability, fiscal sustainability, cost barriers |
| 5 | **Local Capacity & Service Delivery** | Training, community capacity, service infrastructure |
| 6 | **Accessibility & Inclusivity** | Equitable access, marginalized groups, geographic reach |
| 7 | **Cost, Availability & Affordability** | Service costs, resource availability, user affordability |
| 8 | **Data Considerations** | M&E systems, data collection, evidence-based decisions |
| 9 | **Sociocultural Factors & Compliance** | Cultural beliefs, stigma, awareness, compliance |
| 10 | **Services at Higher Levels** | Referral pathways, specialist care, tertiary services |
| 11 | **Procuring Eyeglasses** | Procurement, distribution, supply chain for glasses |

### 5.3 — Building the LLM Prompt

The system constructs a **rich, domain-specific prompt** with multiple layers of context:

```
┌─────────────────────────────────────────────────────────────────┐
│                        SYSTEM PROMPT                             │
│                                                                  │
│  1. Role: "You are a SEHRA analysis expert..."                  │
│  2. SEHRA context: What SEHRA is, who uses it                   │
│  3. Country context: Liberia-specific background (if available) │
│  4. Component description: What "Policy" covers                 │
│  5. Task: Classify each remark → theme + enabler/barrier        │
│  6. Classification rules: What makes an enabler vs barrier      │
│  7. All 11 themes with descriptions                             │
│  8. Keyword patterns: Domain-specific terms per theme           │
│  9. Output format: JSON schema to return                        │
│  10. Confidence rules: When to assign high vs low confidence    │
├─────────────────────────────────────────────────────────────────┤
│                     FEW-SHOT EXAMPLES                            │
│                                                                  │
│  User: "Here are example remarks for policy..."                 │
│  Assistant: { classifications: [...], summaries: [...] }         │
├─────────────────────────────────────────────────────────────────┤
│                       USER MESSAGE                               │
│                                                                  │
│  "Analyze these remarks from the Policy component:               │
│                                                                  │
│   Remark 1:                                                      │
│     Item ID: S15                                                 │
│     Question: Is school eye health in national policy?           │
│     Answer: yes                                                  │
│     Remark: The Ministry has adopted WHO guidelines..."          │
└─────────────────────────────────────────────────────────────────┘
```

### 5.4 — Multi-LLM Fallback

The system tries providers in order:

```
OPENAI_API_KEY set?    → GPT-4o         (highest quality)
     │ no
GROQ_API_KEY set?      → Llama 3.3 70B  (fast, free tier)
     │ no
ANTHROPIC_API_KEY set? → Claude Sonnet   (good balance)
     │ no
     → ERROR: No API key configured
```

All calls use **temperature=0.1** (nearly deterministic) and **max_tokens=4096**.

**Retry logic**: On failure, waits 2s → 4s → 8s (exponential backoff), max 3 attempts.

### 5.5 — What the AI Returns

The LLM returns JSON:

```json
{
  "classifications": [
    {
      "remark_index": 1,
      "item_id": "S15",
      "remark_text": "The Ministry has adopted WHO guidelines for school screening...",
      "theme": "Operationalization Strategies",
      "classification": "enabler",
      "confidence": 0.92
    },
    {
      "remark_index": 2,
      "item_id": "S18",
      "remark_text": "Limited budget allocation for eye health at district level...",
      "theme": "Funding",
      "classification": "barrier",
      "confidence": 0.88
    }
  ],
  "enabler_summary": [
    {
      "themes": ["Operationalization Strategies", "Institutional Structure"],
      "summary": "WHO screening guidelines have been formally adopted, providing...",
      "action_points": ["Strengthen guideline dissemination to sub-national levels"]
    }
  ],
  "barrier_summary": [
    {
      "themes": ["Funding"],
      "summary": "District-level budget allocation for eye health remains insufficient...",
      "action_points": ["Advocate for dedicated eye health budget line items"]
    }
  ]
}
```

### 5.6 — JSON Parsing (Robustness)

LLMs sometimes return imperfect JSON. The parser handles:

```
1. Clean JSON:         {"classifications": [...]}          → Direct parse
2. Markdown fences:    ```json\n{...}\n```                 → Strip fences, parse
3. Extra text:         "Here is the analysis:\n{...}"      → Regex extract {...}
4. Trailing commas:    {"a": 1,}                           → Regex cleanup
5. Complete failure:   "I cannot analyze this"             → Return empty result
```

---

## 6. Step 5 — Theme Validation & Confidence Calibration

**File**: `api/core/ai_engine.py`

After the AI returns classifications, two post-processing steps ensure quality.

### 6.1 — Theme Validation

The LLM might return a theme name that doesn't exactly match our 11 defined themes:

```
LLM returns: "Institutional Structure & Stakeholders"
Actual theme: "Institutional Structure and Stakeholders"
                                        ^^^
                                   (& vs and)
```

**Validation algorithm**:

```
For each classification:
  │
  ├── Exact match (case-insensitive)?
  │     YES → Accept. theme_validated = true
  │
  ├── Fuzzy match (SequenceMatcher ≥ 0.7)?
  │     YES → Auto-correct to closest theme.
  │           Log warning. theme_fuzzy_matched = true
  │
  └── No match (< 0.7)?
        → Assign closest theme anyway
        → Set theme_validated = false
        → Cap confidence at 0.4
        → Flag for human review
```

### 6.2 — Confidence Calibration

Raw LLM confidence scores are unreliable (LLMs tend to be overconfident). Post-processing applies heuristics:

| Condition | Action | Rationale |
|-----------|--------|-----------|
| Theme not validated | Cap at 0.4 | Wrong theme = unreliable |
| Remark < 20 chars | Reduce by 0.2 | Less context = less reliable |
| Remark > 200 chars | Boost by 0.05 | More detail = more reliable |
| Any score | Clamp to [0.0, 1.0] | Prevent impossible values |
| Final score | Round to 3 decimals | Clean output |

### 6.3 — Input Sanitization

Before any remark enters an LLM prompt, it's sanitized:

```
1. Strip leading/trailing whitespace
2. Remove control characters (keep \n, \t)
3. Truncate at 2,000 characters (prevent prompt stuffing)
```

This prevents **prompt injection** — a malicious form field value cannot break the JSON output format.

---

## 7. Steps 6-7 — Save to Database

**File**: `api/core/db.py`

All results are persisted in PostgreSQL with cascading relationships:

```
SEHRA (root record)
  │
  ├── country, district, province, assessment_date
  ├── pdf_filename, raw_extracted_data (full parsed JSON)
  ├── executive_summary (text)
  ├── recommendations (text)
  ├── status: draft → reviewed → published
  │
  └── ComponentAnalysis (×6: one per component)
        │
        ├── component: "policy"
        ├── enabler_count: 17
        ├── barrier_count: 3
        ├── items: JSON[] (all scored items)
        │
        ├── QualitativeEntry (×N: one per classified remark)
        │     ├── remark_text: "The Ministry has adopted..."
        │     ├── item_id: "S15"
        │     ├── theme: "Operationalization Strategies"
        │     ├── classification: "enabler"
        │     ├── confidence: 0.92
        │     └── edited_by_human: false
        │
        └── ReportSection (×3: enabler_summary, barrier_summary, action_points)
              ├── section_type: "enabler_summary"
              ├── content: "WHO screening guidelines have been..."
              └── edited_by_human: false
```

**Cascade deletes**: Deleting a SEHRA automatically deletes all component analyses → entries + sections.

---

## 8. Steps 8-9 — Executive Summary & Recommendations

### 8.1 — Executive Summary

The AI synthesizes **across all 6 components** to produce a 2-5 paragraph overview:

**Input to LLM**:
```
Component Overview:
  - Context: 8 enablers, 4 barriers (67% readiness)
  - Policy: 17 enablers, 3 barriers (85% readiness)
  - Service Delivery: 13 enablers, 2 barriers (87% readiness)
  - Human Resources: 2 enablers, 3 barriers (40% readiness)
  - Supply Chain: 27 enablers, 5 barriers (84% readiness)
  - Barriers: 10 enablers, 38 barriers (21% readiness)

Key Enabler Themes:
  - Operationalization Strategies (12 items)
  - Institutional Structure (8 items)

Key Barrier Themes:
  - Funding (15 items)
  - Sociocultural Factors (11 items)

Location: Liberia (Montserrado district)
```

**Output**: Professional executive summary paragraph(s).

### 8.2 — Recommendations

The AI generates **5-8 prioritized, actionable recommendations** based on the barrier analysis:

```
1. Address funding gaps at district level by advocating for dedicated
   eye health budget line items within national health budgets.

2. Strengthen the referral pathway from school screening to district
   hospitals by establishing formal MOUs between education and health sectors.

3. Expand community health worker training to include basic vision
   screening techniques, reducing dependency on specialist eye care staff.

...
```

---

## 9. Step 10 — Complete

The pipeline emits a final SSE event:

```json
{
  "event": "complete",
  "sehra_id": "a1b2c3d4-...",
  "enabler_count": 77,
  "barrier_count": 55
}
```

The browser receives this and redirects to the assessment detail page.

---

## 10. The Data Files (Brain of the System)

The AI's domain expertise comes from 5 data files:

### `codebook.json` — The Question Bank

~309 items defining every possible SEHRA question with scoring rules.

```json
{
  "id": "S15",
  "section": "policy",
  "question": "Is school eye health integrated into national health policy?",
  "type": "yes_no",
  "has_scoring": true,
  "is_reverse": false,
  "score_yes": 1,
  "score_no": 0
}
```

### `themes.json` — The 11 Classification Categories

Defines the valid theme names and descriptions. Used for LLM prompt construction and output validation.

### `keyword_patterns.json` — Domain Keywords

Organized by component and theme. Guides the LLM on what terms indicate each theme:

```json
{
  "patterns": {
    "policy": {
      "Institutional Structure and Stakeholders": {
        "keywords": "Ministry, Government, Department, agency, body, unit, committee",
        "remarks": ["The Ministry of Health has established...", ...]
      },
      "Funding": {
        "keywords": "budget, funding, allocation, fiscal, financial, cost",
        "remarks": ["Limited budget allocation for...", ...]
      }
    }
  }
}
```

### `few_shot_examples.json` — In-Context Learning

3-5 worked examples per component showing the expected input→output format. These are injected as conversation history before the actual analysis request.

### `sehra_knowledge.json` — Domain Knowledge

Background information about SEHRA, component descriptions, classification rules (what makes an enabler vs barrier), and country-specific context.

---

## 11. Multi-Country: How It Adapts

The system uses a **3-tier data loading hierarchy**:

```
1. Database override (admin edits via web UI)
       ↓ not found
2. Country-specific file (data/countries/{country}/codebook.json)
       ↓ not found
3. Default file (data/codebook.json)
```

### What's Country-Specific

| Data | Why It Varies | Example |
|------|--------------|---------|
| **Page ranges** | PDF layout differs by SEHRA version | Liberia: Context pp 10-15; India might differ |
| **Codebook** | Question wording may vary | Different countries may have different items |
| **Keyword patterns** | Different NGOs, organizations, programs | Liberia mentions Sightsavers; India mentions others |
| **Knowledge base** | Country-specific health system context | Liberia's MoH structure ≠ India's |
| **Few-shot examples** | Country-specific analysis examples | Real classified remarks from that country |
| **Noise texts** | Language differences | English: "yes/no"; French: "oui/non" |

### Adding a New Country

1. Add entry to `country_configs.json` (page ranges, language)
2. Create `data/countries/{country}/` directory
3. Add country-specific data files (or use defaults)
4. **No code changes required**

---

## 12. Key Thresholds & Parameters

| Component | Parameter | Value | Purpose |
|-----------|-----------|-------|---------|
| **PDF Parsing** | | | |
| | Y-tolerance | 15 px | Group checkboxes at same row |
| | Grid column tolerance | 40 px | Match column headers to checkboxes |
| | Min text length | 3 chars | Filter out tiny text fragments |
| **Codebook Matching** | | | |
| | Fuzzy threshold | 0.30 | Minimum match ratio to accept |
| | Substring match | 0.85 | Confidence when one text contains other |
| | First-30-chars match | 0.80 | Confidence when beginnings match |
| **Remark Filtering** | | | |
| | Min remark length | 5 chars | Skip "Yes", "N/A", empty remarks |
| | Max remark length | 2,000 chars | Truncate to prevent prompt stuffing |
| **AI Engine** | | | |
| | Temperature | 0.1 | Nearly deterministic output |
| | Max tokens | 4,096 | Maximum response length |
| | Retry attempts | 3 | With exponential backoff (2s, 4s, 8s) |
| **Theme Validation** | | | |
| | Fuzzy match threshold | 0.70 | Accept auto-corrected theme name |
| | Unvalidated confidence cap | 0.40 | Reduce trust for unmatched themes |
| **Confidence Calibration** | | | |
| | Short remark (< 20 chars) | -0.20 | Less context = less reliable |
| | Long remark (> 200 chars) | +0.05 | More detail = more reliable |
| | Score range | [0.0, 1.0] | Always clamped |

---

## 13. Visual Pipeline Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         USER UPLOADS PDF                                 │
└─────────────────────────────┬───────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  STEP 1: VALIDATE                                                        │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────────────┐          │
│  │ PDF type │→ │ ≤ 10 MB  │→ │ ≥ 40 pgs │→ │ Has widgets?   │          │
│  └──────────┘  └──────────┘  └──────────┘  └───────┬────────┘          │
│                                                      │                   │
│                                          Yes ←───────┼───────→ No        │
│                                          │           │         │         │
│                                    Form PDF     Scanned PDF    │         │
│                                    (PyMuPDF)    (Surya OCR)    │         │
└─────────────────────────────────────────┬───────────────────────────────┘
                                          │
                                          ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  STEP 2: PARSE                                                           │
│                                                                          │
│  ┌─ Header ──────────────────────────────────────────────────────────┐  │
│  │  Text Field 1 → Country    Text Field 3 → District               │  │
│  │  Text Field 2 → Province   Text Field 45 → Date (7 formats)      │  │
│  └───────────────────────────────────────────────────────────────────┘  │
│                                                                          │
│  ┌─ Per Component (×6) ─────────────────────────────────────────────┐  │
│  │                                                                    │  │
│  │  Pages 10-15 (Context)  →  Extract checkbox widgets               │  │
│  │  Pages 16-20 (Policy)       │                                     │  │
│  │  Pages 21-26 (Service)      ├→ Pair Yes/No (Y-tolerance: 15px)    │  │
│  │  Pages 27-30 (HR)           │                                     │  │
│  │  Pages 31-35 (Supply)       ├→ Find question text (spatial match) │  │
│  │  Pages 36-41 (Barriers)     │                                     │  │
│  │                              ├→ Filter noise ("Yes","No","Page")   │  │
│  │                              │                                     │  │
│  │                              ├→ Extract remarks (text fields)      │  │
│  │                              │                                     │  │
│  │                              └→ Match to codebook (fuzzy ≥ 0.30)  │  │
│  └───────────────────────────────────────────────────────────────────┘  │
│                                                                          │
│  Output: {header, components: {context: {items}, policy: {items}, ...}} │
└─────────────────────────────────────┬───────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  STEP 3: SCORE (Deterministic — No AI)                                   │
│                                                                          │
│  For each item with has_scoring=true:                                    │
│                                                                          │
│    Standard:  Yes → score=1 (enabler)    No → score=0 (barrier)         │
│    Reverse:   Yes → score=0 (barrier)    No → score=1 (enabler)         │
│                                                                          │
│  Aggregate per component: {enabler_count, barrier_count}                │
│  Calculate readiness: enablers / (enablers + barriers) × 100%           │
└─────────────────────────────────────┬───────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  STEP 4: AI ANALYSIS (Per Component)                                     │
│                                                                          │
│  ┌─ Filter ──────────────────┐                                          │
│  │ Keep remarks > 5 chars    │                                          │
│  │ Sanitize (strip control   │                                          │
│  │   chars, truncate 2000)   │                                          │
│  └───────────┬───────────────┘                                          │
│              │                                                           │
│              ▼                                                           │
│  ┌─ Build Prompt ────────────────────────────────────────────────────┐  │
│  │ System: Domain expert role + SEHRA context + component desc       │  │
│  │         + 11 themes + keyword patterns + classification rules     │  │
│  │ Few-shot: 3-5 worked examples for this component                  │  │
│  │ User: Formatted remarks with item IDs and questions               │  │
│  └───────────┬───────────────────────────────────────────────────────┘  │
│              │                                                           │
│              ▼                                                           │
│  ┌─ Call LLM ────────────────────────────────────────────────────────┐  │
│  │ OpenAI GPT-4o → Groq Llama 3.3 → Anthropic Claude (fallback)     │  │
│  │ temperature=0.1, max_tokens=4096, retry×3 with backoff            │  │
│  └───────────┬───────────────────────────────────────────────────────┘  │
│              │                                                           │
│              ▼                                                           │
│  ┌─ Parse Response ──────────────────────────────────────────────────┐  │
│  │ Handle: clean JSON, markdown fences, extra text, malformed JSON   │  │
│  │ Validate: Pydantic schema (ClassificationResult, SummaryResult)   │  │
│  └───────────┬───────────────────────────────────────────────────────┘  │
│              │                                                           │
│              ▼                                                           │
│  ┌─ Post-Process ────────────────────────────────────────────────────┐  │
│  │ 1. Validate themes (fuzzy match ≥ 0.7, flag unmatched)           │  │
│  │ 2. Calibrate confidence (short remark: -0.2, unvalidated: ≤0.4)  │  │
│  │ 3. Enrich with full remark text and item IDs                      │  │
│  └───────────────────────────────────────────────────────────────────┘  │
│                                                                          │
│  Output per component:                                                   │
│    classifications: [{theme, classification, confidence, remark_text}]  │
│    enabler_summary: [{themes, summary, action_points}]                  │
│    barrier_summary: [{themes, summary, action_points}]                  │
└─────────────────────────────────────┬───────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  STEPS 5-7: SAVE TO DATABASE                                             │
│                                                                          │
│  SEHRA record → ComponentAnalysis (×6) → QualitativeEntry (×N)          │
│                                        → ReportSection (×3)              │
└─────────────────────────────────────┬───────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  STEPS 8-9: EXECUTIVE SUMMARY & RECOMMENDATIONS                         │
│                                                                          │
│  Input: All component results + enabler/barrier counts + key themes     │
│  LLM generates:                                                         │
│    - Executive summary (2-5 paragraphs, cross-component synthesis)      │
│    - Recommendations (5-8 prioritized, actionable items)                │
└─────────────────────────────────────┬───────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  STEP 10: COMPLETE                                                       │
│                                                                          │
│  → Browser receives: {sehra_id, enabler_count: 77, barrier_count: 55}  │
│  → Redirects to assessment detail page with dashboard                    │
│  → User can: review, edit, approve, export (DOCX/XLSX/HTML/PDF)        │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## What Happens After Analysis

Once the pipeline completes, the user has a full interactive dashboard:

- **KPI Cards**: Total enablers, barriers, readiness percentage
- **Radar Chart**: Component readiness profile (hexagonal visualization)
- **Bar Charts**: Enabler vs barrier breakdown per component
- **Theme Heatmap**: Distribution of themes across all components
- **Inline Editing**: Click any classification to change theme or enabler/barrier
- **Batch Approval**: Approve all entries above a confidence threshold
- **AI Copilot**: Chat with the assessment data, ask questions, request edits
- **Export**: Download professional reports in DOCX, XLSX, HTML, or PDF format
- **Share**: Generate passcode-protected links for stakeholders

---

*Built by Samanvay Foundation for PRASHO Foundation.*
