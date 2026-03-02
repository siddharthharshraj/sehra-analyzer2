"""AI qualitative analysis engine supporting multiple LLM providers.

Supports:
- Groq (fast, free tier available) - set GROQ_API_KEY
- Anthropic Claude - set ANTHROPIC_API_KEY
- OpenAI - set OPENAI_API_KEY

Classifies remarks into themes, generates summaries, action points,
executive summaries, and AI-generated recommendations.
"""

import os
import re
import json
import time
import logging
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field

from core.exceptions import AIAnalysisError

logger = logging.getLogger("sehra.ai_engine")

DATA_DIR = Path(__file__).parent.parent / "data"

COMPONENT_DISPLAY_NAMES = {
    "context": "Context",
    "policy": "Sectoral Legislation, Policy and Strategy",
    "service_delivery": "Institutional and Service Delivery Environment",
    "human_resources": "Human Resources",
    "supply_chain": "Supply Chain",
    "barriers": "Barriers",
}


# --- Pydantic Models for Response Validation ---

class ClassificationResult(BaseModel):
    remark_index: int = 0
    item_id: str = ""
    remark_text: str = ""
    theme: str = ""
    classification: str = ""
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)


class SummaryResult(BaseModel):
    themes: list[str] = []
    summary: str = ""
    action_points: list[str] = []


class ComponentAnalysisResponse(BaseModel):
    classifications: list[ClassificationResult] = []
    enabler_summary: list[SummaryResult] = []
    barrier_summary: list[SummaryResult] = []


# --- Data Loading ---

def _load_themes() -> list[dict]:
    with open(DATA_DIR / "themes.json") as f:
        return json.load(f)["themes"]


def _load_keyword_patterns() -> dict:
    with open(DATA_DIR / "keyword_patterns.json") as f:
        return json.load(f)


def _load_sehra_knowledge() -> dict:
    path = DATA_DIR / "sehra_knowledge.json"
    if path.exists():
        with open(path) as f:
            return json.load(f)
    return {}


def _load_few_shot_examples() -> dict:
    path = DATA_DIR / "few_shot_examples.json"
    if path.exists():
        with open(path) as f:
            return json.load(f)
    return {}


# --- LLM Provider ---

def _get_provider() -> str:
    """Detect which LLM provider to use based on available API keys.

    Priority: OpenAI first, then Groq as fallback, then Anthropic.
    """
    if os.environ.get("OPENAI_API_KEY"):
        return "openai"
    if os.environ.get("GROQ_API_KEY"):
        return "groq"
    if os.environ.get("ANTHROPIC_API_KEY"):
        return "anthropic"
    raise AIAnalysisError(
        "No AI API key found. Set one of: OPENAI_API_KEY, GROQ_API_KEY, or ANTHROPIC_API_KEY"
    )


def _call_llm(system_prompt: str, user_message: str,
              few_shot_messages: list[dict] | None = None,
              max_retries: int = 3) -> str:
    """Call the LLM with retry and exponential backoff.

    Args:
        system_prompt: System prompt for context
        user_message: User message/query
        few_shot_messages: Optional list of {"role": ..., "content": ...} pairs
        max_retries: Number of retry attempts (delays: 2s, 4s, 8s)

    Returns:
        Response text from LLM
    """
    provider = _get_provider()
    delays = [2, 4, 8]

    for attempt in range(max_retries):
        try:
            if provider == "groq":
                return _call_groq(system_prompt, user_message, few_shot_messages)
            elif provider == "anthropic":
                return _call_anthropic(system_prompt, user_message, few_shot_messages)
            elif provider == "openai":
                return _call_openai(system_prompt, user_message, few_shot_messages)
        except AIAnalysisError:
            raise
        except Exception as e:
            if attempt < max_retries - 1:
                delay = delays[min(attempt, len(delays) - 1)]
                logger.warning(
                    "LLM call failed (attempt %d/%d): %s. Retrying in %ds...",
                    attempt + 1, max_retries, str(e)[:200], delay,
                )
                time.sleep(delay)
            else:
                raise AIAnalysisError(
                    f"LLM call failed after {max_retries} attempts: {e}"
                ) from e

    raise AIAnalysisError("LLM call failed: exhausted retries")


def _call_groq(system_prompt: str, user_message: str,
               few_shot_messages: list[dict] | None) -> str:
    from openai import OpenAI
    client = OpenAI(
        api_key=os.environ["GROQ_API_KEY"],
        base_url="https://api.groq.com/openai/v1",
    )
    messages = [{"role": "system", "content": system_prompt}]
    if few_shot_messages:
        messages.extend(few_shot_messages)
    messages.append({"role": "user", "content": user_message})

    response = client.chat.completions.create(
        model=os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile"),
        messages=messages,
        max_tokens=4096,
        temperature=0.1,
    )
    return response.choices[0].message.content.strip()


def _call_anthropic(system_prompt: str, user_message: str,
                    few_shot_messages: list[dict] | None) -> str:
    from anthropic import Anthropic
    client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    messages = []
    if few_shot_messages:
        messages.extend(few_shot_messages)
    messages.append({"role": "user", "content": user_message})

    response = client.messages.create(
        model=os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-5-20250514"),
        max_tokens=4096,
        system=system_prompt,
        messages=messages,
    )
    return response.content[0].text.strip()


def _call_openai(system_prompt: str, user_message: str,
                 few_shot_messages: list[dict] | None) -> str:
    from openai import OpenAI
    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    messages = [{"role": "system", "content": system_prompt}]
    if few_shot_messages:
        messages.extend(few_shot_messages)
    messages.append({"role": "user", "content": user_message})

    response = client.chat.completions.create(
        model=os.environ.get("OPENAI_MODEL", "gpt-4o"),
        messages=messages,
        max_tokens=4096,
        temperature=0.1,
    )
    return response.choices[0].message.content.strip()


# --- Prompt Construction ---

def build_system_prompt(component: str, keyword_patterns: dict, themes: list[dict]) -> str:
    """Build the system prompt with rich SEHRA domain context."""
    knowledge = _load_sehra_knowledge()

    theme_list = "\n".join(
        f"  {t['id']}. {t['name']}: {t['description']}"
        for t in themes
    )

    # Add extended theme descriptions from knowledge base
    theme_details = ""
    themes_kb = knowledge.get("themes", {})
    if themes_kb:
        for key, info in themes_kb.items():
            theme_details += f"\n  {info['name']}:\n    {info['description']}\n"
            if info.get("patterns"):
                theme_details += f"    Key terms: {', '.join(info['patterns'][:8])}\n"

    comp_patterns = keyword_patterns.get("patterns", {}).get(component, {})
    pattern_text = ""
    if comp_patterns:
        for theme_name, patterns in comp_patterns.items():
            pattern_text += f"\n  Theme: {theme_name}\n"
            if isinstance(patterns, dict):
                for key, val in patterns.items():
                    if val:
                        pattern_text += f"    {key}: {val[:500]}\n"
            elif isinstance(patterns, str):
                pattern_text += f"    keywords: {patterns}\n"

    comp_display = COMPONENT_DISPLAY_NAMES.get(component, component)

    # Component description from knowledge base
    comp_desc = ""
    comp_info = knowledge.get("components", {}).get(component, {})
    if comp_info:
        comp_desc = f"\nCOMPONENT DESCRIPTION:\n{comp_info.get('description', '')}\nTypical items: {comp_info.get('typical_items', '')}\n"

    # Classification rules from knowledge base
    rules_text = ""
    rules = knowledge.get("classification_rules", {})
    if rules:
        for cls_type, rule_info in rules.items():
            rules_text += f"\n  {cls_type.upper()}: {rule_info.get('definition', '')}\n"
            indicators = rule_info.get("indicators", [])
            if indicators:
                rules_text += "    Indicators:\n"
                for ind in indicators[:5]:
                    rules_text += f"      - {ind}\n"
            edge = rule_info.get("edge_cases", [])
            if edge:
                rules_text += "    Edge cases:\n"
                for ec in edge:
                    rules_text += f"      - {ec}\n"

    return f"""You are a School Eye Health Rapid Assessment (SEHRA) analysis expert working for PRASHO Foundation.

CONTEXT:
{knowledge.get('overview', 'SEHRA is a structured assessment tool by Peek Vision used globally to evaluate readiness for school eye health programmes.')}

You are analyzing the "{comp_display}" component.
{comp_desc}

YOUR TASK:
Given remarks extracted from SEHRA survey responses for this component, you must:
1. Classify each remark into one or more of 11 predefined themes
2. Classify each remark as: enabler, barrier, strength, or weakness
3. Generate a narrative summary grouping findings by theme for enablers and barriers
4. Generate specific, actionable action points for each barrier theme

CLASSIFICATION RULES:
{rules_text if rules_text else '''- Enabler: Conditions, policies, or practices that support/facilitate school eye health
- Barrier: Conditions, policies, or practices that hinder/prevent school eye health
- Strength: Existing capabilities or assets (subset of enablers with emphasis on what's working well)
- Weakness: Gaps or deficiencies (subset of barriers with emphasis on what needs improvement)'''}

THE 11 THEMES:
{theme_list}

EXTENDED THEME DESCRIPTIONS:
{theme_details}

KEYWORD PATTERNS TO GUIDE CLASSIFICATION (from PRASHO's codebook):
{pattern_text if pattern_text else "  No specific keyword patterns defined for this component."}

KEYWORD PATTERN SYNTAX:
- Commas (,) = OR: "Ministry, Government, plan" means any of these words
- Plus (+) = AND: "Ministry + delivered" means both must appear
- Use these as guidance, not strict rules. Apply semantic understanding.

REPORT AUDIENCE:
{knowledge.get('report_audience', 'Programme planners, Ministry officials, and NGO partners.')}

OUTPUT RULES:
- Each remark can belong to multiple themes if applicable
- Assign the MOST relevant theme as primary
- Confidence should be 0.0-1.0 (1.0 = very confident)
- Summaries should be professional, concise, and evidence-based
- Action points should be specific and implementable
- Reference the original remarks in summaries where relevant"""


def _build_few_shot_messages(component: str) -> list[dict]:
    """Build few-shot example messages for the given component."""
    examples_data = _load_few_shot_examples()
    cls_examples = examples_data.get("classification_examples", {}).get(component, [])

    if not cls_examples:
        return []

    # Build a user message with example remarks
    user_msg = "Here are example remarks to classify:\n\n"
    for i, ex in enumerate(cls_examples[:3], 1):
        user_msg += f'Remark {i}:\n  Remark text: {ex["remark"]}\n\n'

    # Build assistant response with correct classifications
    response = {"classifications": []}
    for i, ex in enumerate(cls_examples[:3], 1):
        response["classifications"].append({
            "remark_index": i,
            "remark_text": ex["remark"][:100],
            "theme": ex["theme"],
            "classification": ex["classification"],
            "confidence": ex["confidence"],
        })

    # Add summary example if available
    summary_examples = examples_data.get("summary_examples", {})
    if summary_examples.get("enabler_summary", {}).get("component") == component:
        es = summary_examples["enabler_summary"]
        response["enabler_summary"] = [{
            "themes": es["themes"],
            "summary": es["summary"][:300],
            "action_points": es["action_points"][:2],
        }]
    else:
        response["enabler_summary"] = []

    if summary_examples.get("barrier_summary", {}).get("component") == component:
        bs = summary_examples["barrier_summary"]
        response["barrier_summary"] = [{
            "themes": bs["themes"],
            "summary": bs["summary"][:300],
            "action_points": bs["action_points"][:2],
        }]
    else:
        response["barrier_summary"] = []

    return [
        {"role": "user", "content": user_msg},
        {"role": "assistant", "content": json.dumps(response, indent=2)},
    ]


# --- JSON Parsing ---

def _parse_llm_json(response_text: str) -> dict:
    """Parse JSON from LLM response, handling markdown fences."""
    text = response_text.strip()

    # Remove markdown fences
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else text[3:]
    if text.endswith("```"):
        text = text[:-3]
    if text.startswith("json"):
        text = text[4:]
    text = text.strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        json_match = re.search(r'\{[\s\S]*\}', text)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                pass
        logger.warning("Failed to parse LLM JSON response: %s", text[:300])
        return {
            "classifications": [],
            "enabler_summary": [],
            "barrier_summary": [],
            "error": "Failed to parse LLM response",
            "raw_response": text[:500],
        }


def _validate_response(raw: dict) -> ComponentAnalysisResponse:
    """Validate and normalize the LLM response using Pydantic."""
    try:
        return ComponentAnalysisResponse(**raw)
    except Exception as e:
        logger.warning("Pydantic validation partial failure: %s", e)
        return ComponentAnalysisResponse(
            classifications=[
                ClassificationResult(**c) for c in raw.get("classifications", [])
                if isinstance(c, dict)
            ],
            enabler_summary=[
                SummaryResult(**s) for s in raw.get("enabler_summary", [])
                if isinstance(s, dict)
            ],
            barrier_summary=[
                SummaryResult(**s) for s in raw.get("barrier_summary", [])
                if isinstance(s, dict)
            ],
        )


# --- Component Analysis ---

def analyze_component(component: str, items: list[dict],
                      component_text: str = "") -> dict:
    """Analyze all remarks for a single component using LLM.

    Args:
        component: Component key (context, policy, etc.)
        items: List of parsed items with {question, answer, remark, item_id}
        component_text: Full text of the component section (for context)

    Returns:
        {
            "classifications": [{remark_text, item_id, theme, classification, confidence}],
            "enabler_summary": [{"themes": [...], "summary": "...", "action_points": [...]}],
            "barrier_summary": [{"themes": [...], "summary": "...", "action_points": [...]}]
        }
    """
    logger.info("Analyzing component: %s", component)
    themes = _load_themes()
    keyword_patterns = _load_keyword_patterns()

    # Collect non-empty remarks
    remarks_for_analysis = []
    for item in items:
        remark = item.get("remark", "").strip()
        if remark and len(remark) > 5:
            remarks_for_analysis.append({
                "item_id": item.get("item_id", ""),
                "question": item.get("question", ""),
                "answer": item.get("answer", ""),
                "remark": remark,
            })

    if not remarks_for_analysis:
        logger.info("No remarks to analyze for %s", component)
        return {
            "classifications": [],
            "enabler_summary": [],
            "barrier_summary": [],
        }

    logger.info("Analyzing %d remarks for %s", len(remarks_for_analysis), component)

    system_prompt = build_system_prompt(component, keyword_patterns, themes)
    few_shot_messages = _build_few_shot_messages(component)

    # Build user message
    remarks_text = ""
    for i, r in enumerate(remarks_for_analysis, 1):
        answer_str = r["answer"] if r["answer"] else "N/A"
        remarks_text += f"""
Remark {i}:
  Item ID: {r['item_id']}
  Question: {r['question']}
  Answer: {answer_str}
  Remark text: {r['remark']}
"""

    theme_names = [t["name"] for t in themes]

    user_message = f"""Analyze the following {len(remarks_for_analysis)} remarks from the "{COMPONENT_DISPLAY_NAMES.get(component, component)}" component of a SEHRA assessment.

{remarks_text}

Respond with a JSON object with this exact structure:
{{
  "classifications": [
    {{
      "remark_index": 1,
      "item_id": "...",
      "remark_text": "...",
      "theme": "<one of the 11 themes>",
      "classification": "<enabler|barrier|strength|weakness>",
      "confidence": 0.95
    }}
  ],
  "enabler_summary": [
    {{
      "themes": ["<theme name>", ...],
      "summary": "<narrative summary of enablers for these themes>",
      "action_points": ["<specific action point>", ...]
    }}
  ],
  "barrier_summary": [
    {{
      "themes": ["<theme name>", ...],
      "summary": "<narrative summary of barriers for these themes>",
      "action_points": ["<specific action point>", ...]
    }}
  ]
}}

Available themes: {json.dumps(theme_names)}
Valid classifications: enabler, barrier, strength, weakness

IMPORTANT: Return ONLY valid JSON, no markdown fences or extra text."""

    response_text = _call_llm(system_prompt, user_message, few_shot_messages)
    raw_result = _parse_llm_json(response_text)

    # Validate with Pydantic
    validated = _validate_response(raw_result)
    result = validated.model_dump()

    # Enrich classifications with full remark text
    for cls in result.get("classifications", []):
        idx = cls.get("remark_index", 0) - 1
        if 0 <= idx < len(remarks_for_analysis):
            cls["remark_text"] = remarks_for_analysis[idx]["remark"]
            cls["item_id"] = remarks_for_analysis[idx]["item_id"]

    logger.info(
        "Component %s: %d classifications, %d enabler summaries, %d barrier summaries",
        component, len(result.get("classifications", [])),
        len(result.get("enabler_summary", [])),
        len(result.get("barrier_summary", [])),
    )

    return result


def analyze_full_sehra(parsed_data: dict) -> dict:
    """Analyze all components of a parsed SEHRA.

    Args:
        parsed_data: Output from pdf_parser.parse_and_enrich()

    Returns:
        Dict mapping component -> analysis results
    """
    results = {}
    components_to_analyze = ["context", "policy", "service_delivery",
                             "human_resources", "supply_chain", "barriers"]

    for component in components_to_analyze:
        comp_data = parsed_data.get("components", {}).get(component, {})
        items = comp_data.get("items", [])
        comp_text = comp_data.get("text", "")

        if items:
            try:
                results[component] = analyze_component(component, items, comp_text)
            except AIAnalysisError as e:
                logger.error("AI analysis failed for %s: %s", component, e)
                results[component] = {
                    "classifications": [],
                    "enabler_summary": [],
                    "barrier_summary": [],
                    "error": str(e),
                }
        else:
            results[component] = {
                "classifications": [],
                "enabler_summary": [],
                "barrier_summary": [],
            }

    return results


def generate_component_summary(component: str, scored_items: list[dict]) -> dict:
    """Generate enabler/barrier summaries from scored codebook items (no text remarks needed).

    Args:
        component: Component key
        scored_items: List of {item_id, question, answer, classification, score}

    Returns:
        {enabler_summary: str, barrier_summary: str, action_points: str}
    """
    enablers = [i for i in scored_items if i.get("classification") == "enabler"]
    barriers = [i for i in scored_items if i.get("classification") == "barrier"]
    comp_name = COMPONENT_DISPLAY_NAMES.get(component, component)

    if not enablers and not barriers:
        return {"enabler_summary": "", "barrier_summary": "", "action_points": ""}

    enabler_list = "\n".join(
        f"  - [{i.get('item_id', '')}] {i.get('question', '')[:150]} → Answer: {i.get('answer', 'N/A')}"
        for i in enablers
    )
    barrier_list = "\n".join(
        f"  - [{i.get('item_id', '')}] {i.get('question', '')[:150]} → Answer: {i.get('answer', 'N/A')}"
        for i in barriers
    )

    system_prompt = f"""You are a SEHRA analysis expert. Given scored codebook items for the "{comp_name}" component, generate a professional summary suitable for a report to Ministry officials.

For each group (enablers and barriers), write a concise cross-cutting summary paragraph highlighting what the findings indicate about the school eye health programme readiness.
Also generate 2-4 specific, actionable recommendations addressing the barriers."""

    user_message = f"""Component: {comp_name}

ENABLER ITEMS ({len(enablers)}):
{enabler_list if enabler_list else "  None"}

BARRIER ITEMS ({len(barriers)}):
{barrier_list if barrier_list else "  None"}

Respond with a JSON object:
{{
  "enabler_summary": "<2-3 sentence narrative of enablers>",
  "barrier_summary": "<2-3 sentence narrative of barriers>",
  "action_points": "<bulleted action items, each on a new line starting with - >"
}}

Return ONLY valid JSON, no markdown or extra text."""

    try:
        response_text = _call_llm(system_prompt, user_message)

        # Parse JSON robustly — _parse_llm_json may return lists for summary fields
        # when parsing fails, so we handle both truncated JSON and type mismatches.
        text = response_text.strip()
        # Remove markdown fences
        if text.startswith("```"):
            text = text.split("\n", 1)[1] if "\n" in text else text[3:]
        if text.endswith("```"):
            text = text[:-3]
        if text.startswith("json"):
            text = text[4:]
        text = text.strip()

        parsed = None
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError:
            # Try regex extraction for each field (handles truncated JSON)
            json_match = re.search(r'\{[\s\S]*\}', text)
            if json_match:
                try:
                    parsed = json.loads(json_match.group())
                except json.JSONDecodeError:
                    pass

        # If JSON parsing failed entirely, extract fields via regex
        if not parsed:
            logger.info("JSON parse failed for component summary, extracting via regex")
            parsed = {}
            for field in ["enabler_summary", "barrier_summary", "action_points"]:
                match = re.search(rf'"{field}"\s*:\s*"((?:[^"\\]|\\.)*)', text)
                if match:
                    parsed[field] = match.group(1)

        # Ensure all values are strings (not lists)
        return {
            "enabler_summary": str(parsed.get("enabler_summary", "")) if not isinstance(parsed.get("enabler_summary"), list) else "",
            "barrier_summary": str(parsed.get("barrier_summary", "")) if not isinstance(parsed.get("barrier_summary"), list) else "",
            "action_points": str(parsed.get("action_points", "")) if not isinstance(parsed.get("action_points"), list) else "",
        }
    except Exception as e:
        logger.warning("Failed to generate component summary for %s: %s", component, e)
        return {"enabler_summary": "", "barrier_summary": "", "action_points": ""}


# --- Executive Summary & Recommendations ---

def generate_executive_summary(all_results: dict, header: dict,
                               scored_components: dict | None = None) -> str:
    """Generate an executive summary synthesizing across all components.

    Args:
        all_results: Dict mapping component -> analysis results
        header: {country, district, province, assessment_date}
        scored_components: Optional dict mapping component -> {enabler_count, barrier_count, items}

    Returns:
        Executive summary text
    """
    country = header.get("country", "the country")
    district = header.get("district", "")
    location = f"{country}" + (f" ({district})" if district else "")

    # Collect summary data — prefer scored data (actual counts) over AI classification counts
    comp_summaries = []
    scored_items_text = ""
    for comp in ["context", "policy", "service_delivery", "human_resources", "supply_chain", "barriers"]:
        if scored_components and comp in scored_components:
            sc = scored_components[comp]
            e_count = sc.get("enabler_count", 0)
            b_count = sc.get("barrier_count", 0)
            comp_summaries.append(
                f"- {COMPONENT_DISPLAY_NAMES.get(comp, comp)}: "
                f"{e_count} enablers, {b_count} barriers"
            )
            # Include sample scored items for context
            items = sc.get("items", [])
            enabler_items = [i for i in items if i.get("classification") == "enabler"]
            barrier_items = [i for i in items if i.get("classification") == "barrier"]
            if enabler_items[:3] or barrier_items[:3]:
                scored_items_text += f"\n{COMPONENT_DISPLAY_NAMES.get(comp, comp)}:\n"
                for i in enabler_items[:3]:
                    scored_items_text += f"  [Enabler] {i.get('question', '')[:100]}\n"
                for i in barrier_items[:3]:
                    scored_items_text += f"  [Barrier] {i.get('question', '')[:100]}\n"
        elif comp in all_results:
            results = all_results[comp]
            enablers = [c for c in results.get("classifications", [])
                         if c.get("classification") in ("enabler", "strength")]
            barriers = [c for c in results.get("classifications", [])
                         if c.get("classification") in ("barrier", "weakness")]
            comp_summaries.append(
                f"- {COMPONENT_DISPLAY_NAMES.get(comp, comp)}: "
                f"{len(enablers)} enablers, {len(barriers)} barriers"
            )

    system_prompt = """You are a SEHRA analysis expert writing a professional executive summary for a school eye health readiness assessment report. Write in a formal, evidence-based style suitable for Ministry officials and programme planners. The summary should synthesize findings across all components, highlighting the most significant enablers and barriers."""

    user_message = f"""Based on the following SEHRA analysis results for {location}, write a concise executive summary (3-5 paragraphs).

Component Overview:
{chr(10).join(comp_summaries)}

{f"Sample scored items:{scored_items_text}" if scored_items_text else ""}

Key enabler themes found:
{_extract_key_themes(all_results, "enabler")}

Key barrier themes found:
{_extract_key_themes(all_results, "barrier")}

Write only the executive summary text, no JSON. Be specific to the findings, professional in tone, and about 200-300 words."""

    logger.info("Generating executive summary for %s", location)
    return _call_llm(system_prompt, user_message)


def generate_recommendations(all_results: dict, header: dict,
                             scored_components: dict | None = None) -> str:
    """Generate AI-powered recommendations based on analysis results.

    Args:
        all_results: Dict mapping component -> analysis results
        header: {country, district, province, assessment_date}
        scored_components: Optional dict mapping component -> {enabler_count, barrier_count, items}

    Returns:
        Recommendations text (numbered list)
    """
    country = header.get("country", "the country")

    # Collect barrier themes for targeted recommendations
    barrier_themes = _extract_key_themes(all_results, "barrier")
    enabler_themes = _extract_key_themes(all_results, "enabler")

    # Include scored barrier items for richer context
    barrier_items_text = ""
    if scored_components:
        for comp, sc in scored_components.items():
            items = sc.get("items", [])
            barriers = [i for i in items if i.get("classification") == "barrier"]
            if barriers:
                barrier_items_text += f"\n{COMPONENT_DISPLAY_NAMES.get(comp, comp)} barriers:\n"
                for i in barriers[:5]:
                    barrier_items_text += f"  - {i.get('question', '')[:120]}\n"

    system_prompt = """You are a SEHRA analysis expert generating actionable recommendations for a school eye health programme. Recommendations should be specific, evidence-based, prioritized, and implementable. They should directly address the barriers identified while building on existing enablers."""

    user_message = f"""Based on the SEHRA analysis for {country}, generate 5-8 prioritized recommendations.

Key barriers identified:
{barrier_themes}

{f"Specific barrier items from assessment:{barrier_items_text}" if barrier_items_text else ""}

Existing enablers to build on:
{enabler_themes}

Format each recommendation as a numbered item (1., 2., etc.) with a clear, actionable statement followed by a brief justification.
Write only the numbered recommendations, no JSON or additional formatting."""

    logger.info("Generating recommendations for %s", country)
    return _call_llm(system_prompt, user_message)


def _extract_key_themes(all_results: dict, classification_type: str) -> str:
    """Extract key themes from analysis results for summary generation."""
    theme_counts: dict[str, int] = {}
    sample_remarks: dict[str, str] = {}

    for comp, results in all_results.items():
        for c in results.get("classifications", []):
            cls = c.get("classification", "")
            if classification_type == "enabler" and cls in ("enabler", "strength"):
                theme = c.get("theme", "")
                theme_counts[theme] = theme_counts.get(theme, 0) + 1
                if theme not in sample_remarks:
                    sample_remarks[theme] = c.get("remark_text", "")[:150]
            elif classification_type == "barrier" and cls in ("barrier", "weakness"):
                theme = c.get("theme", "")
                theme_counts[theme] = theme_counts.get(theme, 0) + 1
                if theme not in sample_remarks:
                    sample_remarks[theme] = c.get("remark_text", "")[:150]

    lines = []
    for theme, count in sorted(theme_counts.items(), key=lambda x: -x[1]):
        sample = sample_remarks.get(theme, "")
        lines.append(f"- {theme} ({count} items): e.g., \"{sample}\"")

    return "\n".join(lines) if lines else "None identified"
